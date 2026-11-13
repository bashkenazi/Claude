# AlphaSense expert-call backfill: handoff

Bobby asked for a full 90-day backfill of the `alphasense-expert-calls` skill: Tier 1-3, window 2026-08-13 to
2026-11-10 ET, live mode. On 2026-11-11 he chose the full run (option 4) after seeing the cost estimate. On
2026-11-13 he approved raising the MCP tool timeout. This folder holds the run state, so a new session can resume
the run.

## Why a new session

AlphaSense GenSearch `ask` can take about 2.5 minutes. The old session had `MCP_TOOL_TIMEOUT=60000`, so about 30%
of asks timed out before returning a `conversation_id`. Those asks were probably charged, and their answers can't be
recovered. Commit "Raise MCP tool timeout to 5 minutes" adds `env.MCP_TOOL_TIMEOUT=300000` to
`.claude/settings.json`.

**First step in the new session:** run `echo $MCP_TOOL_TIMEOUT`. If it is not 300000, the cloud environment's own
variable is overriding the settings file. Bobby must change it in the environment settings (environment menu → Edit
→ environment variables). Do not launch paid workers until it reads 300000.

## Files

- `calls_all.json`: all **4,323** matched calls, the full sweep result (`relevant` and `near_miss`). The sweep was free
  and is complete, so do not re-run it.
- `universe.json`: Companies DB Tier 1-3 (224 names) as of 2026-11-11.
- `plan_week.py <week_idx> [cap] [calls_all.json]` writes `chunks/wNN/batches/worker-*.json` (calls grouped by ticker,
  ≤12 per worker). Week index 12 is 2026-11-05..11-10 and 0 is 2026-08-13..08-19. Calls per week:
  0:227 1:209 2:293 3:295 4:409 5:318 6:323 7:401 8:409 9:406 10:427 11:336 12:270.
- `worker_rules.md`: backfill rules that add to the skill's `references/worker-brief.md`:
  - one ask in flight at a time
  - compare only with evidence dated before the call
  - insert toggles in date order
  - always use the full template, split into two updates when it is too large
  - each worker writes only its own files
- `progress.md`: the coordinator's log, including incidents.
- `w12/`: week 12 state. `calls/*.json` holds the per-call records: 156 attempted, **124 done** (filed to thesis
  pages), **32 failed**. `summaries/` holds the GenSearch answers and assembled write-ups. `batches/` holds the plan;
  workers 14–23 (114 calls) were never launched.

## Resume steps

1. Copy this folder into the session's scratchpad run directory. Keep `w12/` as `chunks/w12/`.
2. Week 12:
   - Build retry batches from `calls/*.json` with `status != done` (32 calls; group by ticker, ≤12 per batch).
   - Launch those retries plus workers 14–23 from `w12/batches/plan.json`, using the skill's Step 5 prompt plus
     "follow worker_rules.md".
   - Run **at most 7 workers at once**.
   - Before re-filing, workers check the thesis page, which skips calls already there.
3. When all 270 calls are done or terminally failed, run skill Steps 6–10 for week 12:
   - collect, then filter (Datapoint Filter v1.4.1, which matches the Notion master)
   - run page `AlphaSense Expert Calls — 2026-11-10 (backfill week 2026-11-05..11-10)` under Anthropic Output
   - Supabase auto-load
   - Tech Daily `as_expert_runs` record

   At this volume, hand the filter step to agents split by sector, and record that in Inputs.
4. Repeat for weeks 11 → 0. Publish a run page per week.

## Notes for Inputs

- There is no "AlphaSense Expert Calls Feedback" toggle on the feedback page.
- Sweep: 392 result files validated by keyword and `has_more=false`. Agents hand-copied a few low-volume weekend days
  in batches 2, 4 and 5, so a typo could mean a missed match on those days.
- Week 12 near misses (5) were all dropped: Credo Ai, Siemens AG, Global Shop Solutions, SK Telecom and GE HealthCare.
- 3017 TT (Asia Vital Components): 6 toggles were filed in a trimmed form. Key numbers, Q&A and the other remaining
  sections are only in `w12/summaries/`.
- About 20 or more wave-1 and wave-2 asks timed out with no `conversation_id`. They were probably charged and can't be
  recovered.
- During wave 1, one worker's script overwrote every `calls/*.json`. The coordinator repaired status and filed page
  from `summaries/*.gensearch.md`. Datapoints were intact. Repaired records have `filed.page_id = null`.
- A GenSearch answer can cite a different document from the one asked about (seen on CRWD and VRT). Workers check
  `document_ids` before using an answer.
