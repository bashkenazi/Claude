---
name: datapoint-filter
description: "Bobby Ashkenazi's (SRS Investment Management) Datapoint Filter: the single shared standard for deciding which investment datapoints are kept, how they are worded, and how they are staged and auto-loaded to Supabase. It is the admission test, stored-evidence check, auto-load policy, compression standard and nine-field entry contract used by every extraction skill (tech-email-digest-new, semianalysis-digest, research-folder-digest, analyst-folder-extractor, alphasense-digest, sellside-folder-digest, datapoint-organizer, and any future one). Always read this skill before extracting, filtering, shortening, auditing, deduplicating or uploading datapoints, whether another skill sends you here or Bobby asks directly: \"filter these datapoints\", \"would you keep this\", \"audit my datapoints\", \"clean up these entries\", \"shorten these\", \"what passes the filter\", \"stage these for Supabase\", \"upload these to Supabase\", or pastes research and asks what matters."
---

# Datapoint Filter

## Run cost tally (applies to every run)

Keep a running token tally from the moment this skill loads until the final output is delivered. It is an **estimate** (the chat environment exposes no token meter), so always label it "est." and never present it as exact.

- **Tool calls (N):** count every tool call: MCP tools, Outlook/Notion/Slack, search/fetch, bash, file and skill reads.
- **In:** for every tool result and every file or skill read, add its approximate size in tokens: characters ÷ 4 for prose, characters ÷ 3 for tables, JSON or number-dense output. Use any size the tool reports (bytes, characters); otherwise estimate from length.
- **Out:** add the approximate size of everything written: tool inputs (page bodies, SQL, JSON, file contents) plus chat replies.
- Round to the nearest 1k (use 0.1k under 10k).
- **Report it** in the timestamp footer and as the last line of the chat reply: `Generated YYYY-MM-DD HH:MM ET · ~XXXk tokens est. (XXXk in / XXk out · N tool calls)`. If this skill otherwise has no footer, add this line at the end of its output.
- **Multi-turn runs** (a confirm or "continue" step): carry the tally forward and report the cumulative total.
- **Sub-step runs:** if this skill is being run inside another skill, do not print a separate line; the parent skill's tally includes this work.

**Version:** v1.3.1 (2026-10-28; entry contract folded into the installed SKILL.md, sellside-folder-digest added to scope). Calling skills record this line, or the Notion master's date, in their Inputs section.

Prioritize signal over completeness. Keep a datapoint only if it materially changes Bobby's view, or meaningfully changes confidence in that view, of a company's growth, margins, competitive positioning, or shareholder returns. Explain exactly what changes and why.

This skill is the shared standard. A calling skill owns retrieval, its `source_type` value, its page layout and any source-specific overrides it names explicitly. Everything else about selecting, wording and staging a datapoint is here, so it is not repeated in each digest.

---

## Step 0 — Load the live standard (once per task, not once per entry)

Fetch the **OpenClaw Agent Feedback** Notion page (`33aa883333de817c853ef25feefea41d`) with `mcp__Notion__notion-fetch` (load it via `tool_search` first). If a calling skill already fetched it in this task, reuse that copy. The page is large: save it and grep for the toggles below rather than reading it whole.

1. **Master text: the toggle titled "🧩 SKILL: datapoint-filter — master text"** (top of Active Agents). Bobby edits the filter there; this file is the fallback copy. It is the skill's own text, not a calibration reference.
   - If the toggle has text, it governs. Compare it with this file. If they differ, follow the Notion text and report the drift in one line ("Notion master differs from skill v1.1: [what changed]") so Bobby can repackage the skill.
   - If the toggle is empty or missing, follow this file and say so.
2. **Calibration reference: the "Datapoint Filter" toggle under Global Feedback** (the one reference file; the skill toggle above is separate). Read its sub-toggles: "General Rules for important data points", "General Rules", "Examples of Datapoints that I would have removed", "Examples of Datapoints that I would keep", "Preferred shorter wording". Also read Cross-Agent Standards → "Evidence_text compression rules".
3. **"Supabase Database Reference File"**, sections 3, 7 and 8 only (entry object, JSON example, producer schema), when staging or uploading.

Read calibration examples as judgment examples, not verified current company facts or fixed ticker rules.

**If Notion cannot be fetched,** continue with this file and state that in the output. Never stop the calling workflow for it.

**Precedence:** Bobby's instruction in the current conversation > the calling skill's explicitly named overrides > the Notion master text > this file. Bobby's current calibration toggles override conflicting older examples. Note any conflict rather than silently picking one.

---

## Admission test

Require all four:

1. **Relevance:** Identify the company and affected investment assumption. Admit industry evidence when it changes an identifiable supply/demand or cost assumption for relevant companies.
2. **Consequence:** Explain a meaningful business or shareholder consequence relative to company size and the importance of the driver.
3. **Evidence:** Ensure the source supports the claim and attribution. Distinguish actuals, management targets, channel checks, forecasts, and inference.
4. **Increment:** Identify a new fact, meaningful revision, material baseline, correction, or independent confirmation that changes conviction.

Return Keep or Remove only. Exclude unclear cases from the main thesis feed. Create no watchlist or speculative backlog; reconsider if stronger evidence later arrives. Set no quota, minimum per source, or target rejection rate. Zero qualifying datapoints is valid.

## Investment dimensions

Use exactly six categories: Growth, Margins, Competition, Shareholder return, TAM, Risks. Categorize pricing, demand outlook and product architecture within these; never propose them as additional categories. Choose the most directly affected assumption: weak demand is Growth, rising costs is Margins; not every negative is Risks.

| Dimension | Relevant assumptions |
| --- | --- |
| Growth | Revenue trajectory, demand durability, pricing, penetration, retention, bookings, backlog, deliverable capacity |
| Margins | Pricing power, costs, mix, utilization, operating leverage, capital intensity, sustainable unit economics |
| Competitive positioning | Share, differentiation, switching costs, substitution, distribution, technology relevance, bargaining power |
| Shareholder returns | Cash generation, returns on capital, allocation, dilution, leverage, financing, acquisitions/disposals, dividends, buybacks |

Connect risk to one of these outcomes; reject generic risk labels. Require no precise EPS/revenue estimate when the supported business mechanism is compelling. Admit meaningful customer qualification, adoption delays, actual monetization, cost actions, contract changes and corrections before their ultimate financial impact is measurable. Admit attributed forecasts that materially challenge a central assumption. Preserve uncertainty and opposing evidence.

## Default exclusions

Exclude unless the admission test clearly passes:

- Routine features, specifications, SDK/access updates, research demos, and narrow benchmarks without commercial consequences.
- Funding/valuation announcements without operating evidence or material financing/ownership effects.
- Uncommitted financing talks, speculative campuses, exploratory partnerships and personnel news without sufficiently concrete business consequences.
- Broad TAM/policy aspirations, static forecasts without meaningful revisions or new evidence, and mechanical scenario arithmetic.
- Vague improvement claims, resolved temporary bugs, isolated testimonials and historical recaps masquerading as new events.
- Generic supplier/customer/competitor read-throughs requiring several speculative steps.
- **Consensus restatements.** If Bobby could get the number from Visible Alpha or FactSet consensus, it is not new evidence. This includes routine earnings recaps (beats/misses vs consensus) already on his earnings pages.
- **Ratings and price targets.** Initiations, rating changes and PTs are not datapoints. Keep only the evidence inside them.
- **Analyst estimates (Bobby, 2026-10-27).** An analyst's own forecasts, model outputs, estimate revisions and estimate-vs-consensus gaps are not datapoints; Bobby sees them in Visible Alpha. Keep the evidence behind them (channel checks, supplier or customer comments, management statements, disclosed orders) when it passes on its own. Exception: scarce industry supply/demand series Visible Alpha does not carry (CoWoS capacity, wafer starts, HBM bits, WFE), labeled as the analyst's estimate.
- Daily stock-price moves, positioning and flows, and pure opinion with no number or mechanism.

**Cost of capital is fundamental evidence, not market noise.** Bond prices/yields, CDS, loan spreads/OID, tranche-level funding costs and financing outcomes for capital-intensive borrowers (e.g. AI-infrastructure names) can pass; map them to Margins, Shareholder return or Risks.

Do not infer company margin from customer API prices or experimental speedups. Do not treat ARR as recognized revenue, contract value as annual revenue, planned MW as operating capacity, or intended migration as realized churn. Never invent a baseline, consensus gap, contribution, date, confidence level, or holding.

## Consolidation and provenance

Treat one underlying event as one event. Link affected companies instead of multiplying generic signals. Preserve distinct supported company effects. Consolidate earnings details while preserving separate growth/margin implications. Attach useful detail, denials and corrections; never erase counterevidence.

**Relays are not corroboration.** Multiple relays of one original source are one event. Notes from the same firm built on the same checks (e.g. a Cleveland "Juice" email plus its company notes, or an initiation plus its Juice) are one source: attribute each fact to the item that states it most fully and never count them as confirming each other. Count a later item as confirmation only if its evidence is independent.

**Row boundaries.** One coherent development per row. Split heterogeneous bundles (different drivers, signs or tickers); keep a homogeneous metric set from one observation together. The ticker is the company whose revenue, margins or position moves. A second-order read-through gets its own row on the affected company, with the causal mechanism stated in the evidence text.

For duplicate audit rows, return Remove as a standalone entry and identify the retaining entry/event. Preserve unique information in proposed consolidation. If the retaining record was not inspected, label consolidation as proposed; do not claim its content is preserved. Label a historical material baseline as a baseline. Disclose when archive-wide novelty was not checked.

## Concise entries without information loss

Apply this standard to every new extracted/database entry and whenever asked to shorten existing entries. Read the compression toggles before rewrites and before the first database-writing batch.

- Lead with the material fact/change and its key numbers. Follow with the supported business consequence or essential caveat. Prefer one or two short sentences, usually 25–50 words; use more whenever needed to preserve important information. Set no hard word limit or required reduction percentage.
- Preserve every material number, unit, period, comparison/baseline, timing, scope, causal mechanism, attribution, uncertainty, condition, correction and opposing fact. Preserve distinctions such as actual versus target, ARR versus revenue, customer versus company savings, and example versus company-wide practice.
- Remove repetition, filler, lengthy introductions, redundant labels, generic implications and nonmaterial product/process detail. Do not erase material content merely because it was not the headline. Use familiar abbreviations; avoid ambiguous shorthand.
- Keep source URLs, full provenance and other structured metadata in their dedicated fields. Avoid repeating them in evidence text, but retain attribution needed to distinguish a claim/forecast from an actual result. If no suitable metadata field exists, retain important provenance inline; never discard it to meet the length preference.
- Before accepting a rewrite, compare it against the complete original/source. Check all material facts, numbers and qualifications, and verify that the shortened version adds no unsupported certainty, inference or financial impact. If a shorter version loses meaning, retain the longer wording.

---

## Entry contract (Supabase staging)

Every staged row has exactly these nine fields and no others. Read the **Bundled reference: entry contract** section at the end of this file for the field rules, enum values and a worked example before staging the first row of a task.

`research_id`, `field_key`, `evidence_text`, `event_date`, `field_impact`, `primary_source`, `secondary_source`, `source_type`, `confidence`

The essentials, so nothing is missed even before the reference is read:

- **field_key** (schema keys, all skills): Growth → `growth_driver`, Margins → `margin_driver`, Competition → `competition`, Shareholder return → `shareholder_return`, TAM → `tam`, Risks → `risk`. No numbered keys, no plain-English categories, no `earnings` key.
- **field_impact:** `positive` / `negative` / `mixed` only (live producer schema). Direction of effect on the business, not on a long/short view. Intensity is display-only: 🟢🟢 and 🔴🔴 mark broad or structural changes on the page, but the row still stages `positive` or `negative`; 🔵 is `mixed`.
- **primary_source** is the underlying origin; **secondary_source** is the intermediary that delivered it. The person who forwarded or emailed it is never the primary source.
- **source_type** is set by the calling skill and describes the kind of origin, never the delivery channel: broker research received by email is `sell_side`, not `email`. Live values are listed in the reference below.
- **research_id:** a resolved integer `research.id`, or null. When null, add `ticker` and `company` beside the row (the only permitted extra fields) so the uploader can resolve it; null rows are blocked at upload. Never invent IDs.
- **secondary_source:** the intermediary, or null if none. Never an empty string.
- No staging tags (`datapoint_class`, `quant/qual`, `derivation`, `sector`, etc.). Context goes in `evidence_text`.

---

## Output modes

**Extraction** (the default inside a digest): return only qualifying entries, each with:

- **What changed:** fact, revision, correction, material baseline, or meaningful confirmation.
- **Why it matters:** affected assumption and consequence.
- Company/ticker, dimension, source/link, event date distinct from insertion date, relevant numbers/units/period/baseline, attribution, uncertainty, opposing evidence, shared-event link when applicable, and the staged row.

State missing information. Report counts kept vs removed per input; detail rejected items only when asked for an audit. Apply admission before scoring. Keep credibility (`confidence`), direction (`field_impact`) and investment importance distinct. Never let repeated weak facts outweigh material events through entry count.

**Audit** (Bobby asks which existing entries should stay): retain every requested row.

Entry ID | Company | Original entry | Keep/Remove | Affected dimension | Reason

Preserve original text separately from analysis. Give an individual reason and duplicate destination. For large reviews, provide a filterable table/file with reconciled totals.

**Shortening only:** preserve each entry's substantive content and identity. Do not silently filter it out, merge events, delete rows, reclassify it or change dates/scores/source fields. Offer removal/consolidation separately only if requested. For a preview, show Entry ID | Original entry | Shortened entry, keeping the original intact. Applying rewrites to stored rows requires an explicit request and follows the scoped update procedure in the Supabase reference.

---

## Notion inputs and Supabase uploads

Read the Supabase Database Reference File when reading a Notion output, checking stored evidence, or uploading. Use the verified default database recorded there; accept a user-specified replacement. Revalidate the live destination and schema before writes. Ask for the project link/reference only if the saved destination cannot be resolved or the intended destination is ambiguous.

When filtering a Notion output Bobby identifies, fetch it including relevant nested content and requested database/view results. Preserve page URLs and original source attribution. Inclusion in a Notion output does not establish quality or novelty; apply the same admission test.

Extraction runs of the skills named in the Auto-load policy below load qualifying rows automatically under that policy. Everything else defaults to review only: when Bobby explicitly asks to upload/save/add qualifying datapoints to Supabase, filter and deduplicate, then insert the qualifying new evidence without a second approval. A request to edit this skill is configuration authorization only, not permission to ingest research. Do not upload rejected entries. Do not modify Notion content, existing evidence, thesis definitions, scores, schema or jobs because an upload was requested. If the live column rejects a value (e.g. a new `source_type`), report the blocked rows; never substitute another value. Report inserted IDs and counts, duplicate skips, rejected counts and blocked/failed records, and verify persisted rows before claiming success.

## Auto-load policy (Bobby, 2026-10-27)

Bobby's standing instruction: datapoints that pass this filter in the extraction digests load to Supabase automatically, with no approval step. This is the explicit upload authorization for those runs.

**Scope.** Extraction runs of `research-folder-digest`, `tech-email-digest-new`, `semianalysis-digest`, `alphasense-digest`, `analyst-folder-extractor` and `sellside-folder-digest`. Not `datapoint-organizer` (it skips the admission test), not audit or shortening modes, and not ad hoc filtering in chat; those stay review-only unless Bobby asks to upload. Bobby turns it off for a run with "stage only", "dry run" or "don't upload".

**Destination.** Supabase project `hftouzahniiwigcchvje` ("bashkenazi's Project"), table `public.research_evidence`, via `mcp__Supabase__execute_sql` (load with `tool_search` "supabase execute sql"). Verified 2026-10-27: nine producer columns plus database-generated `id` and `created_at`; `research_id` NOT NULL, FK to `research`; `field_impact` CHECK; enums `source_type_enum` and `confidence_enum` (`high`/`medium`/`low`). The other project ("Clawd Shared Memory", `wjpjpzdzpsauwjccxaec`) has no evidence tables; never write there. At the start of each load, confirm the table, the six `active_research_fields` keys and the `source_type_enum` values in one query; if they differ from this section, stage only and report the difference. If the Supabase tools are unavailable, stage only and say so.

**A. Stored-evidence check (before the increment test)**

Run once per task, after candidates are extracted and before admission is decided:

1. Resolve every ticker in the run to `research_id` with one query on `research_directory` (match ticker and confirm the company name; resolve aliases). Never infer or invent an ID.
2. Pull stored evidence for those IDs in one query, saved to a file and read per ticker. Heavily covered names carry ~100+ rows a month (NVDA, MU, AMD: ~1,570 rows in 120 days), so keep it compact:

```sql
select id, research_id, field_key, event_date, left(primary_source, 60) src, left(evidence_text, 160) ev
from (select e.*, row_number() over (partition by research_id order by event_date desc, id desc) rn
      from research_evidence e
      where research_id = any(array[<ids>]) and event_date >= current_date - 60) x
where rn <= 60 order by research_id, event_date desc;
```

For a candidate that may restate an older event, run one batched lookup over 180 days on its distinctive figures or terms (`evidence_text ilike any(array['%300k%', '%MI455%', ...])`, scoped to its `research_id`).
3. Apply it in the increment test. A candidate that restates a stored row's underlying event (reworded, or arriving through another relay) is Remove as a duplicate; note the stored ID. A meaningful revision, correction, distinct company effect or independent confirmation still passes; name the stored ID it updates in **What changed**.
4. State the check's scope (window, rows read, tickers unresolved) in the calling skill's Inputs section.

**B. Load gate**

Load a kept row only if all of these hold; otherwise **hold** it (staged on the page, not loaded) with the reason:

- It passed the stored-evidence check.
- It validates against the nine-field contract: exact keys, enum values, a real calendar date, non-empty `evidence_text` and `primary_source`, `secondary_source` null or non-empty.
- `research_id` is resolved (non-null) and the company matches.
- `source_type` is non-null and in the live enum.
- `confidence` is `high` or `medium`.
- It is not labeled as inference, and its direction is known.
- `event_date` is a publication or delivery date, not a scan-date fallback.

Never change a row to get it through the gate: no substituted `source_type`, invented ID or upgraded confidence.

**C. Insert**

After the digest page is published, so a staging record exists:

- Re-check for exact repeats (same `research_id`, `event_date` and `evidence_text`) and skip them; this makes reruns of the same window safe.
- One multi-row `INSERT` into the nine columns (split at 100 rows), `RETURNING id, research_id, field_key, event_date, created_at`. Never send `id` or `created_at`. Quote text with dollar-quoting on a tag absent from the text (e.g. `$ev$...$ev$`); cast enums explicitly (`'sell_side'::source_type_enum`, `'high'::confidence_enum`).
- On a timeout or error, check for committed rows before any retry.
- Never UPDATE or DELETE stored rows, create `research` or company records, change schema or enums, or touch scores. Conflicts with stored rows are held and reported for Bobby.

**D. Verify and report**

- Read back the returned IDs and confirm `research_id`, `field_key`, `event_date`, `source_type` and `confidence`. Staging alone is not loading; never report a row as loaded without the read-back.
- Update the digest page: each loaded datapoint shows `SB #<id>`; each held one shows `Held: <reason>`. Add a "📤 Supabase load" block to the Inputs section: loaded count and ID range, held rows with reasons, duplicates skipped with the stored ID, failures.
- End the chat reply with: `Supabase: N loaded (IDs a–b) · H held · D duplicates skipped · F failed`.
- If the load fails entirely, the published page remains the staging record; say so plainly.

## Scope and execution

Use this as a judgment filter. Outside the Auto-load policy it is not automatic write authorization. Apply it in chat or within another requested extraction workflow, alongside the relevant source, PDF, database and artifact skills. Do not browse merely to embellish an audit; verify sources when requested or necessary for a factual conclusion. Distinguish stored claims from independently verified facts.

Keep verified, nonsecret destination identifiers in the Supabase reference; store no credentials or purported current portfolio. Default to evaluation without mutations. Write, consolidate, delete, change scores/schema, or modify scheduled jobs only within explicit user instructions. Do not request repeat permission for already authorized work. Never claim an existing job uses this filter unless its integration was actually updated and verified.

**Final check:** What should Bobby think differently about this company because of this datapoint? If unclear, exclude it.

---

## Bundled reference: entry contract

The live definition is the "Supabase Database Reference File" toggle on this page. This file is the working copy for staging. If the live schema differs, the live schema wins; report the difference.

**Example (format illustration only, not a stored fact)**

```json
{
  "research_id": null,
  "field_key": "growth_driver",
  "evidence_text": "MI455 unit expectations revised to 300k+ on channel checks; [baseline], [timing] and [condition] go here when the source gives them.",
  "field_impact": "positive",
  "event_date": "2026-05-06",
  "primary_source": "Cleveland Research channel checks",
  "secondary_source": "Chandler Converse (Cleveland Research) email, 2026-05-06, [subject]",
  "source_type": "independent_research",
  "confidence": "medium"
}
```

With `research_id` null, stage `"ticker": "AMD", "company": "Advanced Micro Devices"` beside the row.

When a destination renders code blocks badly (Notion shows them as one unreadable line), show the row as wrapped plain text; the fields and values do not change.

**Field rules**

| Field | Rule |
| --- | --- |
| `research_id` | Existing `research.id` for the company, resolved from the database. Null if not resolvable this session; then add `ticker` and `company` beside the row and list it as an unresolved mapping. The live schema requires an integer ≥ 1, so null rows are staging-only and are blocked at upload until resolved. Never invent IDs. |
| `field_key` | `growth_driver` / `margin_driver` / `competition` / `shareholder_return` / `tam` / `risk`. Most directly affected assumption. One key per row; split the row if two assumptions move for different reasons. |
| `evidence_text` | Number-first statement of what was said, per the compression standard. States whether it is an actual, management target, channel observation, analyst forecast, or inference. No interpretation the source did not make. |
| `field_impact` | `positive` / `negative` / `mixed`. Effect on the company's business or shareholder economics. The SQL column also accepts `very_positive`/`very_negative`, but the producer contract uses three values because some uploaders support only those. Double dots on the page are display intensity only. Hold an unknown direction for review; never force `mixed`. |
| `event_date` | YYYY-MM-DD the information was first published by the attributable source, never the period described or the forecast horizon, and never the insertion date. If only the delivery date is known, use it and label it as a fallback. |
| `primary_source` | The resolved origin: a company disclosure, a named supplier contact, IDC/TrendForce, the analyst's own channel checks or model. If no origin is cited, the analyst's own work (e.g. "Cleveland Research channel checks", "SemiAnalysis — article title"). One origin per row. |
| `secondary_source` | The intermediary that delivered it, specific enough to find again: "Analyst Name (Firm) email, YYYY-MM-DD, subject", or the article when the primary is a third party. null if the primary arrived directly; never an empty string (the schema rejects it). |
| `source_type` | Set by the calling skill: the kind of origin, never the delivery channel. Live schema values: `company`, `sell_side`, `independent_research`, `news`, `substack`, `twitter`, `reddit`, `evernote`, `fintool`, `rogo`, `email`, or null. Independent research publishers, including SemiAnalysis, are `independent_research`. If the column rejects a value, report the blocked rows; never substitute. |
| `confidence` | Evidence credibility only (directness, expertise, specificity, independence): `high` / `medium` / `low` / null. Separate from direction and importance. |

**Display conventions for digest pages**

- Header line: impact dot + **TICKER** | Category | confidence
- Dots (display only): 🟢🟢 broad/structural positive, 🟢 positive, 🔵 mixed, 🔴 negative, 🔴🔴 broad/structural negative
- Dates YYYY-MM-DD everywhere; bold every model-moving figure
