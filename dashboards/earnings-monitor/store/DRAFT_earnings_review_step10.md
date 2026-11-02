# DRAFT — earnings-review skill: new §10 "Earnings history load"

Status: draft for Bobby's review. Not yet applied to the skill.
Where it goes: `earnings-review/SKILL.md`, after "### 9. Datapoints and Supabase load". Also add one line to
**Publish** step 4, one line to **Report back in chat**, and two checklist items (all at the bottom of this file).

---

### 10. Earnings history load (Supabase)

Every run also records the print in the earnings history tables, so prints can be compared quarter over
quarter. This is separate from the datapoint load in §9: beats and misses are stored here even though they
fail datapoint admission.

Project `hftouzahniiwigcchvje`, tables `public.earnings_prints` (one row per ticker × calendar quarter) and
`public.earnings_metrics` (one row per Part A table row). Write with `mcp__Supabase__execute_sql`, after the
page is published. Keep each statement under ~15KB; split metrics into several inserts if needed.

1. **Print row.** Upsert on `(ticker, calendar_quarter)`:
   - `ticker` as on the Companies DB row; `research_id` = `public.research.id` for the company (same id §9 uses).
   - `calendar_quarter` = the calendar quarter the fiscal quarter mostly falls in, as `YYYYQn` (Jun-Q → `2026Q2`).
   - `fiscal_quarter` (the page label, e.g. `2Q FY27 (Jul-Q)`), `report_date`, `company_name`, `sector`.
   - `verdict` from the Part A dot: 🟢🟢 `very_positive`, 🟢 `positive`, none `mixed`, 🔴 `negative`, 🔴🔴 `very_negative`;
     `verdict_marker` = the dots as written; `call_tone` = the Call Notes characterization.
   - `headline` = the Summary line; `summary` = the Summary bullets as a JSON array; `stock_reaction` = §6 one-liner.
   - `title` = page title; `local_key` = `<TICKER>_<YYYY-MM-DD>` with spaces as `_`; `source_skill` = `earnings-review`.
   - `review_md` = the full page text, `thesis_filing_md` = what was filed to the thesis page (if the statement
     would exceed the size limit, write these two in a separate `update` by `local_key`).
   - On a rerun (Pass 2), the upsert replaces the row; set `updated_at = now()`.
2. **Metric rows.** Delete existing rows for the print (`delete from public.earnings_metrics where print_id = …`),
   then insert one row per table row in §2 (`section='quarter'`), §3 (`next_q_guide`) and §4 (`fy_guide`):
   `metric` (row label without the dot), `actual` (Act / Guide / New cell as text), `street` (📊), `bogey` (🎯),
   `vs_street_pct` and `vs_bogey_pct` as numbers (percent; convert bp to percent ÷100; null for `—`), `marker`
   (the row's dot).
3. **Read back:** `select id from public.earnings_prints where ticker=… and calendar_quarter=…` and the metric
   count; report them.
4. If Supabase is unreachable, stage the two statements in a **📥 History rows — <TICKER>** toggle and say so.

**Publish** step 4 — add: "Then run the history load (§10)."
**Report back in chat** — add after the Supabase line: `History: print #<id> · M metric rows`.
**Checklist** — add:
- [ ] History print row upserted (ticker × calendar quarter) with verdict, headline, summary, review text
- [ ] Metric rows match the Part A tables (sections 2–4), read back
