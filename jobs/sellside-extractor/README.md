# Sell-Side Daily Research Extractor

Daily cloud routine that turns the broker PDFs in OneDrive `Daily Research` into Supabase evidence rows and a Notion
digest. Replaces the OpenClaw / Clawd Office sell-side extractor (Mac OneDrive sync → Poppler → GPT-5.5 → REST
insert), which is retired.

## How it works

| Step | Where |
|---|---|
| List `Daily Research` recursively (date folders ≥ 2026-10-22) | Microsoft 365 connector |
| Diff every PDF against the ledger; queue new, changed and retryable files | Supabase `sellside_file_ledger` |
| Read PDFs and propose rows (JSON + exact quotes) | `sellside-pdf-extractor` subagents, Sonnet 5.5, read-only |
| Validate, re-map, stored-evidence check, admission and load gate | main session + installed **datapoint-filter** skill + `validate_rows.py` |
| Publish digest, then insert, then read back and annotate `SB #id` | Notion (Openclaw Output) → Supabase `research_evidence` |
| Close out file and run records | Supabase `sellside_file_ledger`, `sellside_runs` |

The runbook is `.claude/skills/sellside-folder-digest/SKILL.md`; the subagent is
`.claude/agents/sellside-pdf-extractor.md`. Admission, wording, the nine-field contract and the load gate come from
the installed datapoint-filter skill and its Notion master; they are not copied here.

No external model API and no secrets: connectors carry all traffic.

## Running it

- **Scheduled:** routine "Sell-Side Daily Research Extractor", weekdays 12:07 and 16:27 PT, prompt in
  [`PROMPT.md`](PROMPT.md).
- **On demand:** "Run now" on the routine, or in a Claude Code session on this repo: "run the sell-side extractor"
  (add "dry run", "limit to folder 10.23.26" or "budget 120" as needed).
- **Backfill:** run with a folder limit. Files already in the ledger as done are skipped; changed files re-run.
  Re-running a folder is safe: the exact-repeat check on `(research_id, event_date, evidence_text)` and the
  stored-evidence check stop duplicate inserts.
- **Re-process one file:** set its ledger row to `pending` with `attempts = 0`.

## State

All state is in Supabase project `hftouzahniiwigcchvje`, schema `public`:

- `sellside_file_ledger` — one row per OneDrive PDF (`drive_item_id`): status, attempts, counts, loaded evidence IDs,
  hold reasons, re-filed-copy link (`duplicate_of`).
- `sellside_runs` — one row per live run: status (`running`, `completed`, `partial`, `blocked_source`, `failed`),
  counts, Notion URL, notes.

Useful queries:

```sql
select status, count(*) from sellside_file_ledger group by 1;
select * from sellside_runs order by id desc limit 10;
select folder_path, file_name, attempts, last_error from sellside_file_ledger where status = 'failed';
```

Schema: [`migrations/20261027200000_sellside_ledger.sql`](migrations/20261027200000_sellside_ledger.sql) (applied
2026-10-27). Both tables have RLS on with no policies; only the connector's privileged role reads or writes them.

## Guarantees

- "No new PDFs" is reported only after a successful connector listing in that run; a failed listing is reported as
  `blocked_source`.
- Every file is compared against the ledger, not just new date folders.
- Files that were not read in full (`complete_read: false`) are retried up to 3 times and never loaded.
- Subagents never write. The main session never UPDATEs or DELETEs stored evidence.

## Limits

- The connector reads PDFs as text; numbers that exist only inside chart images are not captured.
- Default budget is 60 PDFs per run; the rest stay `pending` for the next run and are listed in the digest.

## Reference

[`hermes-reference.md`](hermes-reference.md) documents the retired pipeline (schedules, prompts, dedup layers,
historical rules). Reference only; datapoint-filter v1.2 governs where they differ.
