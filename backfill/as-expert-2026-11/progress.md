# Backfill progress (alphasense-expert-calls, 90 days 2026-08-13..2026-11-10 ET, Tier 1-3, live)
Bobby chose option 4 (full backfill) on 2026-11-11 after cost estimate (6k-15k calls, 0.6-1.5B tokens).
Plan: free sweep (7 agents, daily windows) -> match -> weekly chunks newest first; per chunk waves of 10 workers x ~10 calls;
per chunk: filter, run page, Supabase, Tech Daily record. Workers insert toggles in date order (newest first).
## Inputs so far
- Feedback page fetched (feedback.txt). Global Feedback read. No "AlphaSense Expert Calls Feedback" toggle exists -> note in Inputs.
- Datapoint Filter v1.4.1; Notion master also v1.4.1 (no drift). Calibration toggle at char 47835 of feedback_plain.txt (read before filtering).
- Tech Daily as_expert_runs: empty (no prior processed calls).
- Universe: 224 Tier 1-3 names (universe.json). Batches in sweep/batchN.txt.
## Status
- [running] Sweep: 7 agents writing sweep/bN_<date>.json + bN_status.json
- Next: match all sweep files -> calls_all.json; split into weekly chunks newest first; per chunk plan waves of 10 workers x 10 calls.
- Deviation for scale: Step 7 filtering delegated to filter agents per chunk (note in Inputs).
- 13:20 batch-4 resume agent bulk-copied ~78 unrelated tool-result files into sweep/ as b4_*_*.json (mtime>=13:20:30). NOT deleted (agent's delete was blocked; left for Bobby). Use only b4_trusted.txt + sweep_b4v2/ for batch 4. Batch 4 relaunched for 08-22..11-10 into sweep_b4v2/.
## Sweep DONE: 392 files validated (files_ok.json), calls_all.json: 4,323 Tier1-3 calls (T1 442/T2 2439/T3 1442), 146 near misses.
Weekly chunk idx 0..12 (plan_week.py <idx>), counts: 0:227 1:209 2:293 3:295 4:409 5:318 6:323 7:401 8:409 9:406 10:427 11:336 12:270
Caveats for Inputs: b2/b4/b5 some weekend days hand-transcribed by agents (possible typo -> missed match).
## Week 12 (2026-11-05..11-10): 270 calls, 23 workers (chunks/w12). Near misses w12: 5, all dropped (Credo Ai, Siemens AG, Global Shop Solutions, SK Telecom, GE HealthCare).
- Wave 1 launched: workers 1-10 (120 calls). Pending: workers 11-23.
- Wave 1 result: 67/120 done, 53 failed (GenSearch overload at 10 parallel workers; ~20 timeouts w/o conv id may have been charged). Worker tokens ~3.67M (~55k per filed call). ~25 min.
  Incidents: worker-4 script overwrote all calls/*.json at 13:47 & 13:53 -> repaired from summaries/*.gensearch.md (backup in chunks/w12_calls_backup). AVC (3017 TT) 6 toggles filed in "lean form" (Key numbers/Q&A only in local summaries). CRWD: GenSearch cross-wired answer, handled.
- worker_rules.md added (1 ask in flight, retry unavailable x2, own files only, full template in 2 updates).
- Wave 2 launched: r1-r5 (53 retries) + workers 11,12. Queue: workers 13-23.
