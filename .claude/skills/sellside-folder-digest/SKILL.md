---
name: sellside-folder-digest
description: Sell-side Daily Research extractor for Bobby Ashkenazi (SRS). Inventories the OneDrive "Daily Research" folder through the Microsoft 365 connector, diffs every PDF against the Supabase ledger, fans the new or changed PDFs out to sellside-pdf-extractor subagents, applies the datapoint-filter skill, publishes a Notion digest under Openclaw Output and auto-loads qualifying rows to Supabase. Use when asked to "run the sell-side extractor", "sweep Daily Research", "run sellside-folder-digest", for the scheduled routine, or for a dry run or backfill of one date folder.
---

# Sell-Side Folder Digest

The main session owns inventory, mapping, dedup, validation, every write and publishing. Subagents
(`sellside-pdf-extractor`, Sonnet 5.5) only read PDFs and return candidate rows. No external LLM API, no API keys,
no local files carried between runs: state lives in Supabase.

Job files: `jobs/sellside-extractor/` (README, PROMPT, `validate_rows.py`, `hermes-reference.md`, migrations).

## Fixed identifiers

| Item | Value |
|---|---|
| OneDrive drive ID | `b!FJwk4wuDWkK0YqsCOFcwCBUYQuPS0M1MnrmOON_3fvtgrpGgDA9cTJd7WVPx15G9` |
| `Daily Research` folder | `file:///{driveId}/01Q4NHPUUUMGKP4YG7B5GK2V7KCPMGVONJ` |
| Supabase project | `hftouzahniiwigcchvje` (never `wjpjpzdzpsauwjccxaec`) |
| Ledger tables | `public.sellside_runs`, `public.sellside_file_ledger` |
| Rules page (Notion) | OpenClaw Agent Feedback `33aa883333de817c853ef25feefea41d` |
| Output parent (Notion) | Openclaw Output `2fba883333de80e4b112d56bfe32e124` |

## Parameters

Read them from the request; defaults in brackets.

- `mode`: `live` [default] or `dry_run`. "dry run", "stage only" and "don't upload" all mean `dry_run`.
- `folders`: limit to named date folders, e.g. `10.26.26` [all folders ≥ floor].
- `floor`: earliest date folder in scope [**2026-10-22**]. Older folders are out of scope; never read or import the
  retired pipeline's ledgers or manifests.
- `budget`: max PDFs extracted this run [**60**].
- `concurrency`: subagents in flight at once [**4**].
- `trigger`: `scheduled` when started by the routine, else `manual`.

**dry_run** = full inventory and extraction, **no Supabase writes of any kind** (no `research_evidence`, no
`sellside_runs`, no `sellside_file_ledger`), Notion page title prefixed `DRY RUN — `, ledger diff computed by
read-only SELECT.

Work in a scratch directory (`$WORK`, e.g. a fresh temp dir). Save every subagent reply and SQL result you need
later as a file there; read files back instead of holding large outputs in context.

## 1. Start the run

1. **Tools.** Load the Microsoft 365 `read_resource`, Supabase `execute_sql` and Notion fetch/create/update tools
   (ToolSearch if deferred). If M365 is missing, go to **Blocked source** below. If Supabase is missing, continue
   as `dry_run` and say why. If Notion is missing, continue but do not insert (§9 needs a staging page).
2. **Concurrency guard (live).** `select id, started_at from sellside_runs where status = 'running'`. A row
   younger than 3 hours means another run is active: stop and report it. Older rows: set `status = 'failed'`,
   `notes = notes || '{"reason":"stale running row closed by run N"}'`, and reset that run's `extracting` ledger
   rows to `pending`.
3. **Open the run (live).** `insert into sellside_runs (mode, trigger, rules_version) values (...) returning id`.
4. **Rules.** Invoke the installed **datapoint-filter** skill and follow its Step 0 once (Notion master, calibration
   toggles, compression rules, Supabase Database Reference §3/7/8). From the same saved copy of the feedback page,
   also take the **"🟢 Extractor (sell-side)"** toggle (under OpenClaw and Hermes Agent Feedback) and the
   **GLOBAL EXTRACTION & SCORING STANDARD**. Where they ask for broad capture, extra tags (class, derivation,
   publicity, customer) or scores, datapoint-filter governs: stricter admission, nine fields, no tags, no scores.
   Keep their compatible parts: publication-date rule, ticker = whose P&L moves, split heterogeneous bundles,
   relays ≠ corroboration, numbers-first wording, Daily Callout Block layout.
   Write `$WORK/rules-pack.md`: master text, calibration, compression rules, entry contract, the compatible
   extractor rules, and a first line stating the datapoint-filter version or Notion master date. Do not edit the
   installed skill or the Notion page.
5. **Schema check** (the filter's Auto-load destination check): one query confirming `research_evidence` columns,
   the six `active_research_fields` keys and the `source_type_enum` values. A mismatch makes the run `dry_run`;
   report the difference.

## 2. Inventory

List `Daily Research` with `read_resource` on the folder URI. Each entry is `name (folder|file, N bytes) uri`.
A listing page holds 200 entries; when a final `Note:` line says more remain, call again with the `startPage` it
names until none remain.

- Date folders are named **`M.D.YY`, not zero-padded** (`10.1.26`, `9.21.26`; occasionally `MM.DD.YY`). Parse with
  `^(\d{1,2})\.(\d{1,2})\.(\d{2})$` → `20YY-MM-DD`. Keep folders ≥ `floor` (and in `folders` if given); ignore
  names that do not parse.
- **Recurse fully** into each kept date folder, including nested folders such as `AI Files`, paging each listing.
- For each `.pdf` (case-insensitive) record `drive_item_id` (the last URI segment), `uri`, `folder_path`
  (e.g. `Daily Research/10.26.26/AI Files`), `folder_date`, `file_name`, `size_bytes`. Skip non-PDF files (MP3s
  and the like) and count them separately.
- The listing returns no last-modified time, so "changed" means a size change. Leave `last_modified` null.

**If any listing call fails** (error, empty response for a folder that the parent listing showed as non-empty, or
an unparsable reply) after one retry: go to **Blocked source**. Never report "no new PDFs" unless every listing
call in this run succeeded.

Save the inventory to `$WORK/inventory.json`.

## 3. Diff against the ledger

One SELECT of the ledger rows for all inventoried item IDs, plus all rows with `status in ('pending','failed',
'extracting')`. Classify:

- **New:** item ID not in the ledger.
- **Changed:** in the ledger with a different `size_bytes`. Reset to `pending`, `attempts = 0`.
- **Retry:** ledger `pending`, `failed` with `attempts < 3`, or `extracting` whose `last_run_id` is not running.
- **Re-filed copy:** a new item whose `file_name` matches an existing ledger row or another inventoried file, with
  size within 1%. Record it as `skipped` with `duplicate_of` = the original's item ID; do not extract it. Keep the
  oldest item as the original.
- **Done:** everything else (`loaded`, `held_only`, `no_datapoints`, `skipped`, `failed` with `attempts ≥ 3`).

Live mode: insert new items as `pending` (one `insert ... on conflict (drive_item_id) do nothing`), apply the
changed/copy updates, and set `files_listed` and `files_new` on the run row. Dry run: compute the same sets only.

## 4. Plan batches

Queue = new + changed + retry. Take the `budget` oldest by `folder_date` (then file name); the rest stay `pending`
and are reported. Within the selection, **big files go first**: size > 5 MB, or > 20 pages when already known from
the ledger. One big file per subagent; small files **4–6 per subagent**, grouped by folder.

## 5. Resolve mapping once

Collect ticker hints from filenames (`YYYYMMDD_Broker_TICKER_Title.pdf`; the ticker token is the one right after the
broker, e.g. `MKSI`, `2454-TT`, `ASML-NA`, `SAP-GR`; brokers can contain underscores, so match against the directory
rather than splitting blindly). One query on `research_directory`, comparing normalized tickers (upper case, strip
non-alphanumerics) and also the base symbol without an exchange suffix (`2454-TT` → `2454`; `4062-JP` ↔ `4062 JT`):

```sql
select id, ticker, company_name from research_directory
where upper(regexp_replace(ticker, '[^A-Za-z0-9]', '', 'g')) = any(array[<normalized hints>])
   or upper(split_part(ticker, ' ', 1)) = any(array[<base symbols>]);
```

Save the slice. Subagents get it as a proposal aid; you re-resolve every row yourself in §7.

## 6. Fan out

Live: set the batch's ledger rows to `extracting`, `attempts = attempts + 1`, `last_run_id = <run>`.

Spawn `sellside-pdf-extractor` subagents with the Agent tool, `concurrency` at a time, refilling as each finishes.
Each prompt gives: the absolute path of `$WORK/rules-pack.md`, the absolute repo path of
`jobs/sellside-extractor/hermes-reference.md`, the catalog slice, and the batch's files (`drive_item_id`, `uri`,
`file_name`, `folder_path`). Ask for the JSON contract in the agent file and nothing else. Save each reply verbatim
to `$WORK/out/<batch>.json` (strip a surrounding code fence if present). When the Agent result points to a
transcript file, extract the final reply from it with a short script instead of re-typing the JSON.

If the subagent type is not available, stop and report it; do not extract in the main session.

## 7. Validate

1. Run `python3 -I jobs/sellside-extractor/validate_rows.py $WORK/validation.json $WORK/out/*.json`.
2. **Parse error or missing file entry:** retry that batch once with a fresh subagent. A second failure marks those
   files `failed` with `last_error`.
3. **`complete_read: false`:** mark the file `failed` (it retries next run, up to 3 attempts); do not load its rows.
4. **Row errors:** fix nothing that would change meaning. A row with contract errors is held with the error as the
   reason. An empty quote list makes the row a cut. "Numbers not found in quotes" is a flag for you to check
   against the quotes: a unit conversion or rounding the quotes support (¥757,715mn → ¥757.7bn) is fine; a figure
   the quotes do not support makes the row a cut ("unsupported number").
5. **Re-resolve `research_id`** for every row from `ticker`/`company` against the directory (one batched query for
   anything not in the slice). Subagent IDs are proposals: if yours differs, use yours and note it; if none
   resolves, the row is held "mapping unresolved: <ticker> <company>". Never invent an ID or create a `research`
   record.
   **Alias groups.** The directory holds several IDs for some companies (e.g. SAP 65/768/772, APPF 688/310,
   4062 JT 87 / 4062 JP 717, MU 15/773, NVDA 4/774). Use the canonical IDs in the agent file where listed;
   otherwise pick the ID with the most `research_evidence` rows over the last 180 days (one batched count query),
   tie → lowest ID. List the alias groups you resolved in the page's Inputs section.
6. `publication_date_basis = filename_fallback` makes every row from that file held ("event_date is a filename
   fallback"), per the filter's load gate.
7. Read each kept row against its quotes. You are the final admission judge under datapoint-filter: cut what fails
   admission, and tighten wording under the compression rules only where the quotes support every word.

## 8. Stored-evidence check and admission

Follow datapoint-filter Auto-load **§A** exactly: one 60-day / 60-rows-per-ID query for all resolved IDs (save to
file), then one batched 180-day distinctive-term lookup for candidates that may restate older events. A candidate
that restates a stored row's event is removed as a duplicate, naming the stored ID. Also collapse duplicates
**within this run** (the same event from two brokers' notes: keep the fuller one; a second broker counts as
confirmation only with independent evidence). Then apply the **§B load gate**; every failing row is held with its
reason.

## 9. Publish, insert, read back

1. **Publish the Notion page first** (layout below) under Openclaw Output, with every kept row shown as staged.
   Dry run: publish and stop here (skip 2–3).
2. **Insert** per datapoint-filter **§C**: re-check exact repeats on `(research_id, event_date, evidence_text)`;
   one multi-row `INSERT` per ≤ 100 rows into the nine columns, dollar-quoted text, explicit enum casts,
   `RETURNING id, research_id, field_key, event_date, created_at`. On error or timeout, check what committed before
   any retry. Strip `ticker`, `company`, `source_quotes`, `page_hint`, `disposition`, `hold_reason` first.
3. **Read back** per **§D**, then update the page: `SB #<id>` on each loaded row, `Held: <reason>` on each held row,
   and the "📤 Supabase load" block.

Never UPDATE or DELETE `research_evidence`, create `research` records, change schema or enums, or touch scores.

## 10. Close out (live)

One `UPDATE sellside_file_ledger ... FROM (VALUES ...)` setting per file: `status` (`loaded` if ≥ 1 row loaded;
`held_only` if rows were kept but none loaded; `no_datapoints` if zero kept; `failed` as above), `page_count`,
`kept`, `held`, `cut`, `evidence_ids`, `hold_reasons`, `last_error`, `updated_at = now()`. Then close the run row:
`finished_at`, `status` (`completed`, or `partial` when files remain pending or failed), counts, `notion_url`,
`notes` (unresolved tickers, drift notes, stored-evidence check scope).

The last line of the session is exactly:

`Supabase: N loaded (IDs a–b) · H held · D duplicates skipped · F failed · P files pending`

## Blocked source

When the M365 connector is missing or a listing fails: (live) set the run row `status = 'blocked_source'` with
the error in `notes`; publish a short Notion page `Sell-Side Folder Sweep — YYYY-MM-DD — BLOCKED: Daily Research
listing failed` stating the error and that **no inventory was taken, so this is not a "no new PDFs" result**; end
with `Supabase: 0 loaded · 0 held · 0 duplicates skipped · 0 failed · source BLOCKED (no inventory)`. Do not touch
ledger file rows.

## Notion page

Title: `Sell-Side Folder Sweep — YYYY-MM-DD — N PDFs · R rows` (N = PDFs processed, R = rows loaded, or kept in a
dry run). Use datapoint-filter display conventions: impact dots (🟢🟢 🟢 🔵 🔴 🔴🔴), bold model-moving figures,
dates as YYYY-MM-DD. Sections, omitting any that would be empty except contradictions:

1. **Callouts** (Daily Callout Block order): biggest datapoint; up to 5 most positive; up to 5 most negative; up to 5
   inflections; up to 5 themes; contradictions (or "no thesis stress today"); supply/demand state changes;
   revisions (≤ 5); new names or gaps (≤ 3). Numbers first.
2. **Ticker summary:** ticker | loaded | held | top datapoint.
3. **Ticker toggles** (alphabetical): per row, header `dot **TICKER** | field_key | confidence`, the evidence text,
   event date, primary/secondary source, source PDF file name and folder, then `SB #id` or `Held: reason`.
4. **Held, cut and duplicates:** each with its reason; duplicates name the stored ID.
5. **Coverage:** files listed / new / changed / processed / pending / failed / re-filed copies skipped / non-PDF
   skipped, per date folder; any incomplete reads with pages.
6. **Inputs and run summary:** datapoint-filter version or Notion master date and any drift note; stored-evidence
   check scope (window, rows read, unresolved tickers); 📤 Supabase load block; run ID, mode, trigger, start/end
   time PT; subagent count.
