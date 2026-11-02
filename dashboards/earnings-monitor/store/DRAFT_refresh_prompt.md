# DRAFT — new prompt for the scheduled task "Research Desk refresh" (trig_01EAEb5pVZLn1SUWKR7z3r4u)

Status: draft for Bobby's review; the task still has the old prompt. Weekdays 7:35pm ET.
Needs connectors attached before it can run: Notion, Microsoft 365, SRS MCP, FactSet, Supabase.

What changes vs the current prompt:
- builds Bobby Tech Daily (not "Research Desk"), from 2026-07-01, with the full reviews and every tab;
- reads earnings reviews from Supabase `earnings_prints` (the new source of truth) instead of Notion pages;
- writes today's history: `daily_moves` rows and one `tech_daily_snapshots` row per tab;
- may INSERT/UPSERT only into the five history tables; still never edits or deletes anything else.

---

Refresh Bobby Ashkenazi's "Bobby Tech Daily" artifact: https://claude.ai/artifact/4WAMJK6NEWt1dqETwd2Zcc .

Rules: read-only on Notion, SharePoint, Outlook and FactSet. In Supabase project hftouzahniiwigcchvje you may
only INSERT or UPSERT into public.daily_moves, public.tech_daily_snapshots, public.earnings_prints,
public.earnings_metrics and public.earnings_assessments; never UPDATE or DELETE any other table, and never
delete history rows. Never invent numbers or dates. Keep every execute_sql statement under ~15KB (split rows
into several statements).

Repo bashkenazi/Claude, branch claude/tender-shannon-0p3wbf, folder dashboards/earnings-monitor/ (README.md
describes the data; build.py renders template.html + tabs.css + tabs.js; tabs.js shows the JSON each tab
reads; store/ has the history schema). Check out that branch first.

Pull in parallel with subagents, each writing JSON into a scratch folder <S>:
1. Earnings: SELECT from public.earnings_prints (report_date >= 2026-07-01) → <S>/bobby.json in the record
   shape build.py expects (ticker, company, quarter=fiscal_quarter, report_date, sentiment=verdict, headline,
   summary, sector, title, url='local:'||local_key, reaction=stock_reaction), and write each row's review_md
   to <S>/review_md/<local_key>.md (line 1 title, line 2 local:<local_key>, then the text).
   Also any new earnings-review pages in Anthropic Output since the last run that are not yet in the table:
   add them to the files (do not write them to Supabase; the skill does that).
2. rebecca.json — Rebecca's earnings-recap PDFs (SharePoint SRS › Research › Rebecca › Claude › Earnings
   Recaps, drive b!zGN3q_1cOkOFd1OOa0WUPdkXn2M7jrVJn_YfnmeLXQJTP1mBD9XrSbVt8brs7rzU, folder
   01GE2BO43KKRHKBHXZ6VDYZZATCQJ5DHI3), dated >= 2026-07-01; skip xlsx.
3. tabs/earn_assess.json and tabs/earn_assess_cq2.json — payload of public.earnings_assessments for the
   current and prior calendar quarter (unchanged unless a quarter has new prints; then refresh the stats).
4. tabs/today.json, tabs/datapoints.json, tabs/screens.json, tabs/ideas.json, tabs/prep.json — as before
   (digest pages from the last 7 days; research_evidence last 21 days; consensus-revisions and comps-screen;
   idea-generator, thesis-builder, industry-cycle, operating-comps; management-prep, analyst-day,
   print-tables, quarterly-review plus next-4-weeks Tier 1–2 prints from FactSet).
5. tabs/daily.json — biggest company and sector moves today for the Master comps universe (FactSet closes),
   with the reason for each (news, desk mail, filings).
6. tabs/signals.json, tabs/comps.json, tabs/sources.json — rebuild only if their inputs changed.

Then:
- python3 dashboards/earnings-monitor/build.py <S>/bobby.json <S>/rebecca.json <S>/earnings-monitor.html
  --since 2026-07-01 --tabs <S>/tabs --full <S>/review_md
- node check: every tab renders with no console errors.
- History: insert today's tabs/daily.json into public.daily_moves (sector rows kind='sector', stock rows
  kind='stock'; on conflict do nothing), and upsert one public.tech_daily_snapshots row per tab
  (snapshot_date = today; split any payload over ~15KB into parts named tab.part.N).
- Read the artifact (Artifact tool, action read, url above), then publish the built file to that same url.
  Do not create a new artifact. Do not commit built HTML or JSON.

Finish with a short summary: new prints, rows written to each history table, and any source that failed.
