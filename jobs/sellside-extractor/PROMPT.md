# Routine prompt

Paste the block below as the prompt of the **Sell-Side Daily Research Extractor** routine. It is self-contained.

```text
Run the sellside-folder-digest skill in this repository end to end for today, in live mode, with trigger = scheduled. The skill is at .claude/skills/sellside-folder-digest/SKILL.md (job files under jobs/sellside-extractor/); if it is not listed as a skill, Read that file and follow it. Use the sellside-pdf-extractor subagent defined in .claude/agents/ for all PDF reading.

This prompt is my standing authorization to load qualifying rows to Supabase project hftouzahniiwigcchvje (public.research_evidence) under the datapoint-filter Auto-load policy for this pipeline, and to write the sellside_runs and sellside_file_ledger tables. It does not authorize updating or deleting stored evidence, creating research records, changing schema or enums, or touching scores.

Do not ask questions. If blocked, publish a blocker note to Notion under Openclaw Output and stop. Never report "no new PDFs" unless the Microsoft 365 listing of Daily Research succeeded in this run.

Finish with the one-line summary: Supabase: N loaded (IDs a–b) · H held · D duplicates skipped · F failed · P files pending
```

## Variants for "Run now"

- **Backfill one folder:** add `Limit to folder 10.23.26.` (or several, comma-separated).
- **Dry run:** replace "in live mode" with "in dry_run mode" — no Supabase writes, Notion page marked DRY RUN.
- **Larger catch-up:** add `Budget 120 PDFs.`
