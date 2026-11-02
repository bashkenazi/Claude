Refresh Bobby Ashkenazi's "Bobby Tech Daily" artifact: https://claude.ai/artifact/4WAMJK6NEWt1dqETwd2Zcc .

Runs weekdays at 12:20 PM ET (MIDDAY mode) and 9:20 PM ET (EVENING mode); pick the mode from the current ET time.
- MIDDAY: after the 11:30 Tech Specialist digest. Prices are intraday Bloomberg from the Master comps Live sheet.
  Rebuild only tabs/daily.json, tabs/today.json and tabs/routines.json; every other tab carries over from the live page.
  No history writes except one tech_daily_snapshots row per rebuilt tab named <tab>.midday.
- EVENING: after the 6 PM Research Inbox and 8 PM SemiAnalysis digests. Closes; rebuild every tab; full history writes.

Rules: read-only on Notion, SharePoint, Outlook, AlphaSense and FactSet. Never run a digest or other skill that
publishes to Notion or loads Supabase datapoints: Bobby's scheduled routines do that (see "Routines" below), and
this refresh only reads what they published. In Supabase project hftouzahniiwigcchvje you may only INSERT or UPSERT
into public.daily_moves, public.tech_daily_snapshots, public.earnings_prints, public.earnings_metrics and
public.earnings_assessments; never UPDATE or DELETE any other table, and never delete history rows. Never invent
numbers or dates. Keep every execute_sql statement under ~15KB (split rows into several statements).

Repo bashkenazi/Claude, branch claude/tender-shannon-0p3wbf, folder dashboards/earnings-monitor/ (README.md
describes the data; build.py renders template.html + tabs.css + tabs.js; tabs.js shows the JSON each tab
reads; store/ has the history schema). Check out that branch first.

Routines (Bobby's scheduled tasks; each publishes a page under Notion "Anthropic Output", page 33ba883333de80a6ab40d2ed18985f31):
| key | routine | schedule (ET) | page title starts with |
| research-folder-digest | Research Folder Digest | weekdays 5:27 AM | "Research Digest —" (morning run) |
| tech-email-digest-new | Tech Specialist Email Digest | daily 11:30 AM | "Tech Specialist Digest —" |
| research-inbox-digest | Research Inbox Folder Digest | daily 6:00 PM | "Research Digest —" (evening run) |
| semianalysis-digest | SemiAnalysis Digest | daily 8:00 PM | "SemiAnalysis Digest —" |
| consensus-revisions | Consensus Revisions | Fri 7:00 AM | "Consensus Revisions —" |
| idea-generator | Idea Generator | Sun 5:00 AM | "Idea Generator —" / "Ideas —" |
Also read, when present: sellside-folder-digest ("Sell-Side Folder Sweep —"), alphasense-digest ("AlphaSense Digest —"),
analyst-folder-extractor. Find each routine's pages with notion-search (title + date, sorted by recency) and fetch them.
Several runs on one day are normal (manual reruns): use all of them, newest first, and dedupe datapoints.
A routine whose latest page is older than its schedule implies is "missed": say so on the page, never run it.

Universes (use exactly these three, nothing else):
A. Master comps = prices, daily moves, valuation, screens. Read it straight from Excel; never require a CSV export.
   Microsoft 365 connector: sharepoint_search(query "Trading Comparables", folderName "Trading comps",
   fileType "xlsx"; skip any path containing /Drafts/), then read_resource each candidate, newest
   lastModifiedDateTime first, with startPage=999 to list its worksheets.
   - Feed / Feed_Rev sheets (when a workbook has them): read each with startPage=endPage=<sheet number>; one row
     per company with a header row (Feed: Ticker, Name, Group, Currency, Price, Mkt Cap $bn, ADV 3M $mm,
     Perf 7D/30D/YTD %, % From 52W High, PE CY26/27/28, EV/Sales CY27, EV/EBITDA CY27/28, Rev Growth CY27/28 %,
     Cyclical; Feed_Rev: 1W and 4W BEST revisions). Rebuild tabs/comps.json from them (rows keyed by Bloomberg
     ticker with and without " Equity", groups with n and medians; file = workbook name, as_of = workbook
     lastModifiedDateTime).
   - Live sheet (today's source for moves): Ticker | Price | Chg % 1D [| Sub sector], formulas off 'Template (2)'.
     If the read comes back as a PDF conversion (no "## Sheet: Live"), retry up to 3 times. Map tickers to
     tabs/universe.json by full Bloomberg ticker, then (US or no exchange) by the first token; a Sub sector column,
     when present, wins over universe.json.
   If a read says rows were not shown, stop and report it rather than using a partial universe. Fallback for
   closes only: FactSet GlobalPrices on universe.json ids.
B. Companies DB (Notion collection://54e1fc28-0c99-43cf-9d42-a6aa7de55d87; columns Company, Ticker, BBG Ticker,
   Sector, Sub-sector, Tier, In Master Comps) = the names Bobby follows closely: earnings, prep, idea and
   today-tab focus. Tier 1–2 for upcoming prints.
C. Supabase public.research / research_evidence = companies we collect data on; signals and datapoints tabs.

Pull in parallel with subagents, each writing JSON into a scratch folder <S>:
1. Earnings (EVENING): SELECT from public.earnings_prints (report_date >= 2026-07-01) → <S>/bobby.json in the
   record shape build.py expects (ticker, company, quarter=fiscal_quarter, report_date, sentiment=verdict,
   headline, summary, sector, title, url='local:'||local_key, reaction=stock_reaction), and write each row's
   review_md to <S>/review_md/<local_key>.md (line 1 title, line 2 local:<local_key>, then the text).
   Rows whose review_md is null are fine: the build carries their full review over from the live page.
   Also any new earnings-review pages in Anthropic Output since the last run that are not yet in the table:
   add them to the files (do not write them to Supabase; the skill does that).
2. rebecca.json (EVENING) — Rebecca's earnings-recap PDFs (SharePoint SRS › Research › Rebecca › Claude › Earnings
   Recaps, drive b!zGN3q_1cOkOFd1OOa0WUPdkXn2M7jrVJn_YfnmeLXQJTP1mBD9XrSbVt8brs7rzU, folder
   01GE2BO43KKRHKBHXZ6VDYZZATCQJ5DHI3), dated >= 2026-07-01; skip xlsx.
3. tabs/earn_assess.json and tabs/earn_assess_cq2.json (EVENING) — payload of public.earnings_assessments for the
   current and prior calendar quarter (unchanged unless a quarter has new prints; then refresh the stats).
4. Routine pages → tabs/today.json (digests from the last 7 days, same record shape as now: skill, title, url,
   date, window, callouts, themes, datapoint_count) and tabs/routines.json:
   {"as_of", "routines": [{"key","name","schedule","status": "ok|missed|running","last_run","runs":[{"title",
   "url","date","window","datapoint_count","supabase_line"}], "callouts":[...], "themes":[...], "by_sector":
   {"<sector>": [{"ticker","text","sentiment","sb_id"}]}, "note"}]} — newest run's content, up to 14 runs listed.
   Consensus Revisions and Idea Generator also feed tabs/screens.json and tabs/ideas.json (EVENING) as before,
   with thesis-builder, industry-cycle, operating-comps; tabs/datapoints.json from research_evidence last 21 days;
   tabs/prep.json from management-prep, analyst-day, print-tables, quarterly-review plus next-4-weeks prints from
   FactSet for Companies DB Tier 1–2 names.
5. tabs/daily.json — only after step 4 (the day's digests are the first source of reasons):
   prices from universe A (MIDDAY: Live sheet; EVENING: closes). Shape: as_of, universe_n, summary[] (connect
   the moves into themes, most important first), sectors[] (group, n, median_1d, best, worst, why — a why for
   every sector), up[]/down[] (top 12 each), moves[] (every priced name: t, n, g, c), and stories{} keyed by
   ticker ({why, sources, confidence}) for every name that moved >=5% AND >=3 points away from its sector median
   (most extreme first, cap 60). Sources for each story, in order: the routine pages from step 4, then desk mail
   since the prior trading day (Outlook search by ticker/name), today's Daily Research PDFs (OneDrive, folder named
   like 11.2.26), AlphaSense (alphasense_genai; ignore its price figures), srs_documents for names that just
   reported, then the web. A story is the catalyst with figures, "moved with <group>: <driver>", or "No catalyst
   found in your sources or the news." If no digest has run today, keep the previous daily.json.
6. tabs/signals.json and tabs/sources.json (EVENING) — rebuild only if their inputs changed.
7. PAUSED (Bobby, 2026-11-02: database is being cut down; skip this step and keep the live page's datapoints
   files and tabs/dp_index.json as they are until he says to resume).
   Datapoints + Composite Evidence Index (EVENING): export public.research_evidence for the last 9 months with
   execute_sql in pages of 4,000 rows by id (select id, research_id r, field_key k, field_impact i, event_date d,
   confidence::text c, source_type::text s, primary_source p, secondary_source q, evidence_text t ... order by id;
   large results are saved to files — parse them, never paste them), plus research (id, ticker, company_name n,
   sector, subsector) for those ids. Then
   python3 dashboards/earnings-monitor/store/build_datapoints.py evidence.json research.json <S>/tabs/universe.json <S>/dpout
   and copy <S>/dpout/dp_index.json to <S>/tabs/. Publish dpout/dp/*.json with the page as supporting files
   (Artifact files map "dp/sources.json", "dp/part1.json" … "dp/partN.json").

Then:
- Read the live artifact first (Artifact tool, action read, url above) and save its HTML as <S>/live.html.
- python3 dashboards/earnings-monitor/build.py <S>/bobby.json <S>/rebecca.json <S>/earnings-monitor.html
  --since 2026-07-01 --tabs <S>/tabs --full <S>/review_md --keep-full <S>/live.html
  (MIDDAY: pass the live page's own bobby/rebecca by re-using last night's files if present; otherwise rely on
  --keep-full and check the counts below.)
- Check the built page has at least as many full reviews and prints as the live one; if not, do not publish.
- node check: every tab renders with no console errors.
- History (EVENING): insert today's tabs/daily.json into public.daily_moves (sector rows kind='sector', stock rows
  kind='stock'; on conflict do nothing), and upsert one public.tech_daily_snapshots row per tab
  (snapshot_date = today; split any payload over ~15KB into parts named tab.part.N).
- Publish the built file to that same url. Do not create a new artifact. Do not commit built HTML or JSON.

Finish with a short summary: mode, routines read (and any missed), new prints, stories written / not found,
rows written to each history table, which comps workbook/sheets were used, and any source that failed.
