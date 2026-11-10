Refresh Bobby Ashkenazi's "Bobby Tech Daily" artifact: https://claude.ai/artifact/4WAMJK6NEWt1dqETwd2Zcc .

SCHEDULE — runs weekdays at 10:00, 11:00, 12:00, 14:00 and 16:00 ET (Bobby's schedule, 2026-11-03). Decide what to
rebuild from the current ET hour; every tab not rebuilt carries over from the live page (--keep-full <S>/live.html).
| ET run | Rebuild |
| 10:00, 12:00, 14:00 | Daily moves (step 5, intraday Live sheet) and then Today's market commentary (step 4, "market" only) |
| 11:00               | Routines (step 4: tabs/routines.json, full run pages, and today.json digests/call-outs) |
| 16:00               | Daily moves + market commentary (near-close Live sheet), Routines, Datapoints & index (step 7), Stocks (6b), |
|                     | Earnings (steps 1–3), history writes (snapshots + daily_moves) |
| every run           | the WHEN-CHANGED checks below |
| first run of the week (Monday 10:00, or the first run after a holiday) | Pipeline, Ideas & themes, Estimates & screens and Valuation in full, even if unchanged |

WHEN-CHANGED checks (every run, cheap): rebuild a tab only if its source has something newer than the last build. The
last build's source stamps are stored in public.tech_daily_snapshots tab 'build.state' (payload {source: stamp}; insert a
new row per date, on conflict do nothing, and read the latest one first).
- Pipeline (tabs/pipeline.json): the Notion page Pipeline/Active/Ideas (dd4260f087554ddca72eaad2a0a0aa15) last_edited, the
  Shorts database, any new Idea Generator or Thesis - Revised page under Anthropic Output since the stamp, and any
  public.research_ideas row with created_at after the stamp (stamp key 'research_ideas' = max(created_at)).
- Ideas & themes (tabs/ideas.json + digest themes in today.json): any new Idea Generator, thesis-builder, industry-cycle or
  operating-comps page since the stamp, or any new public.research_ideas row since the stamp.
- Earnings (steps 1–3): any public.earnings_prints row with created_at or updated_at after the stamp (stamp key
  'earnings_prints' = max(greatest(created_at, updated_at))). The "Earnings Review — New Prints" routine writes these
  rows as each review finishes, so a new review shows on the Earnings tab at the next run (within ~2 hours) instead of
  waiting for 16:00. Rebuild Earnings (and the Stocks earnings metrics for those tickers) whenever this check fires.
- Estimates & screens (tabs/screens.json): a new Consensus Revisions or Comps Screen page since the stamp.
- Valuation (tabs/comps.json, the valuation lines on every card): the Master comps workbook's lastModifiedDateTime, or a
  new Comps Screen / Consensus Revisions page since the stamp. Read the values from the workbook's 'Template (2)' sheet
  (or Feed sheets if a workbook has them); never require a CSV export.
- Stocks debates and draft tenets: re-write a company's debate (bull/bear/decides/tenets, 25-word bullets, only from its
  datapoints) when it has 5+ new important datapoints since the stamp, a new earnings review, or a new Thesis - Revised page.

Prices are intraday Bloomberg from the Master comps Live sheet; the Live sheet only changes when the workbook is saved,
so say in the Daily moves status line when the file's lastModifiedDateTime is more than 30 minutes old.
In the steps below, "(EVENING)" means the 16:00 run and "(MIDDAY)" means the 10:00/12:00/14:00 runs.

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
| research-folder-digest | Research Inbox Folder Digest | daily 9:30 AM | "Research Digest —" |
| semianalysis-digest | SemiAnalysis Digest | daily 10:00 AM | "SemiAnalysis Digest —" |
| tech-email-digest-new | Tech Specialist Email Digest | daily 10:30 AM | "Tech Specialist Digest —" |
| feedly-digest | Feedly Daily | daily 8:00 AM | "Feedly" |
| consensus-revisions | Consensus Revisions | Fri 7:00 AM | "Consensus Revisions —" |
| idea-generator | Idea Generator | Sun 5:00 AM | "Idea Generator —" / "Ideas —" |
| x-scan | Grok X bot (outside Claude) | varies | "X Idea Scan", "X List Monitor" |
| output-sweep | Anthropic Output Sweep | daily 11:00 AM | (writes Supabase only; no Notion page) |

Archiving (from 2026-11-03): the daily Anthropic Output Sweep reads every run page, loads its datapoints to
public.research_evidence, its ideas/themes/theses to public.research_ideas, saves the full page to
public.output_sweep_ledger (content_md), then MOVES the page to Anthropic Output › Archived
(40da883333de81a28d02ca1fdae930d5). Bobby may delete archived pages, so:
- Search Archived as well as Anthropic Output when finding a routine's pages.
- If a page cannot be fetched (deleted), use output_sweep_ledger.content_md for that url/page_id instead; a run listed in
  the ledger is never "missed".
- tabs/ideas.json ideas[] and the theme lists come FIRST from public.research_ideas (kind idea/callout -> ideas[] using
  payload when present; kind thesis -> theses[]; kind theme -> digest themes), last 60 days by source_date, then any
  run page newer than the sweep that is not yet in the table. Dedupe on dedupe_key / (ticker, source_url).
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
   today-tab focus. Upcoming prints (Prep & calendar, and the Earnings tab's "Reported, review not run yet" panel):
   every Companies DB row with Tier 1–3 or In Master Comps checked (Bobby, 2026-11-09), each carrying its tier.
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
   Also save the FULL content of every run listed (notion-fetch, the <content> markdown unchanged) as
   <S>/routine_md/<key>__<NN>.md (line 1 title, line 2 url, then the content) and pass --routines <S>/routine_md
   to build.py, so the Routines tab shows each run in full.
   tabs/today.json also gets "market" — the WHY, not the tape (Bobby, 2026-11-03: he has prices and moves on his
   Bloomberg monitor, so never list index levels, % moves, stock moves or subsector performance):
   {as_of, headline (≤ 18 words: the one thing driving the session), drivers[] ("Why it's moving": 3–4 bullets on flows,
   positioning, systematic/CTA/risk-control activity, macro and policy catalysts — the causes), under[] ("Under the
   surface": 4–5 bullets on rotations and why, narrative shifts, funding/positioning tells, read-throughs between names
   and sectors, what the desks are debating), watch[] ("What to watch": 2–3 bullets — tonight's prints and the bar,
   data points that would change the read), sources[{label,url}]}. Each bullet ≤ 22 words, ends with its source tag in
   [brackets]. Written from the routine pages, desk morning/midday wraps (TMTB, MS TMT, BofA TMT, Gugg, Jefferies, RBC,
   UBS), SemiAnalysis and Daily Research; a figure is fine only when it explains a cause (e.g. "$85–115B of systematic
   selling"), never a price move.
   Consensus Revisions and Idea Generator also feed tabs/screens.json and tabs/ideas.json (EVENING) as before,
   with thesis-builder, industry-cycle, operating-comps; tabs/datapoints.json from research_evidence last 21 days;
   tabs/prep.json from management-prep, analyst-day, print-tables, quarterly-review plus next-4-weeks prints from
   FactSet for Companies DB names with Tier 1–3 or In Master Comps checked (same set as B).
5. tabs/daily.json — only after step 4 (the day's digests are the first source of reasons):
   prices from universe A (MIDDAY: Live sheet; EVENING: closes). Shape: as_of, universe_n, summary[] (connect
   the moves into themes, most important first), sectors[] (group, n, median_1d, best, worst, why — empty when no driver is found), up[]/down[] (top 12 each), moves[] (every priced name: t, n, g, c), and stories{} keyed by
   ticker ({why, sources, confidence}) for every name that moved >=5% AND >=3 points away from its sector median
   (most extreme first, cap 60). Sources for each story, in order: the routine pages from step 4, then desk mail
   since the prior trading day (Outlook search by ticker/name), today's Daily Research PDFs (OneDrive, folder named
   like 11.2.26), AlphaSense (alphasense_genai; ignore its price figures), srs_documents for names that just
   reported, then the web. A story is ONE sentence (≤ 30 words; Bobby, 2026-11-03) on why it moved: the
   specific catalyst with its key figure. If no source gives a company-specific reason, leave why EMPTY ("") —
   never write "moved with the market/sector/group", "in line with peers" or "No catalyst found" (Bobby, 2026-11-10).
   The same rule applies to sectors[].why: name the driver or leave it empty. If no digest has run today, keep the previous daily.json.
6. tabs/sources.json (EVENING) — rebuild only if its inputs changed. (The Signals tab was removed 2026-11-03; skip
   tabs/signals.json. Pipeline now shows inside the "Pipeline, ideas & themes" tab; tabs/pipeline.json is unchanged.)
6b. tabs/stocks.json (EVENING): Companies DB Tier 1–2 rows (Ticker, BBG Ticker, Company, Sector, Sub-sector, Tier),
   public.research driver names (growth_driver_1..5, margin_driver_1..4, competition_1..3, tam_1..2, risk_1..6) and
   aliases, and earnings_metrics joined to earnings_prints; then
   Debate agent pages: notion-search "Tech Specialist Debate History" and "Stock Debate"; for every page whose title
   has that phrase (not "dry run" unless it is the only page on the ticker), notion-fetch it and save
   <S>/debate_raw/<slug>.md (line 1 title, line 2 url, then the <content> markdown unchanged). Then
   python3 dashboards/earnings-monitor/store/prep_debates.py <S>/debate_raw <S>/routine_md/debates
   and copy <S>/routine_md/debates/*.md into <S>/routine_md (build.py --routines shows them on the Debate tab).
   Revised thesis pages (every 16:00 run): notion-search "Thesis - Revised" and "Thesis Revised" and keep pages whose
   title is "<Company> - Thesis Revised - <date>" (the current name) or an older form ("<TICKER> Thesis - Revised",
   "<TICKER> Thesis Revised — <date>", "<Company> Thesis - Revised"), and whose
   last_edited is after the stamp 'theses' in build.state (first run: all of them). notion-fetch each and extract
   {company, ticker, url, updated (last edited, YYYY-MM-DD), summary_pitch (the Summary thesis / pitch block, ≤ 600 chars),
   stance (e.g. "Long, conviction 7/10"), tenets: [{tenet, conviction (1–10), status (lean/status as written), why
   (the tenet's investment read, ≤ 300 chars)}]} exactly as written — never invent a tenet or a number. Merge with the
   theses already on the live page (data.stocks.companies[].thesis, keyed by url; a newly fetched page replaces the old
   entry) into <S>/theses.json as {"pages": [...]}, and pass --theses <S>/theses.json below. Bobby edits tenets in
   Notion, so a page edited since the stamp must be re-fetched even if it was read before.
   Save the live page's stocks JSON (data.stocks) as <S>/prev_stocks.json, then
   python3 dashboards/earnings-monitor/store/build_stocks.py tiers.json research.json labels.json aliases.json metrics.json <S>/tabs/stocks.json \
     --debpages <S>/routine_md/debates/index.json --theses <S>/theses.json --keep <S>/prev_stocks.json
   (--keep carries each company's written debate and revised-thesis tenets forward; never drop them.)
   Never run the stock-debate skill or any digest from the refresh; only read the pages it has published.
7. Datapoints + Composite Evidence Index (16:00 run; resumed 2026-11-03 after the cleanup — rows tagged
   "[ARCHIVED dup_of=…]" are skipped by the builder): export public.research_evidence for the last 9 months with
   execute_sql in pages of 4,000 rows by id (select id, research_id r, field_key k, field_impact i, event_date d,
   confidence::text c, source_type::text s, primary_source p, secondary_source q, evidence_text t ... order by id;
   large results are saved to files — parse them, never paste them), plus research (id, ticker, company_name n,
   sector, subsector) for those ids. Then
   python3 dashboards/earnings-monitor/store/build_datapoints.py evidence.json research.json <S>/tabs/universe.json <S>/dpout
   and copy <S>/dpout/dp_index.json to <S>/tabs/. Publish dpout/dp/*.json with the page as supporting files
   (Artifact files map "dp/sources.json", "dp/part1.json" … "dp/partN.json").

Then:
- History for the page's "As of" picker: for each of the last 30 snapshot dates in public.tech_daily_snapshots,
  rebuild that day's Daily moves read (tab 'daily', or 'daily.midday' + '.stories' + '.moves' parts joined) and write it
  as <S>/tabs/daily_YYYY-MM-DD.json. Store every tab you rebuild as a snapshot row (insert, on conflict do nothing):
  daily, today, routines.index, pipeline, ideas, screens, prep, signals, comps, earn_assess — so any day can be replayed.
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
- AI thesis tab (#thesis): its content lives only in the page database (collection "thesis", doc "ai", and collection
  "thesis_updates"), written by the "AI thesis tracker" scheduled task. The code comes from tabs.js/template.html; never
  write, rebuild or delete those database documents from this refresh.
- DC permits & financing tab (#dcrisk): a research report kept only in the page database (collection "dc_risk", doc
  "report"). The code comes from tabs.js/template.html; never write, rebuild or delete that document from this refresh.
- AI tab › SRS models (#ai/models): the numbers from SRS's AI industry models (AI Master Model, AI Economics Master,
  AI Financings) live only in the page database (collection "ai_models", docs meta, capex, revisions, compute, econ,
  labs, fin, supply). The code comes from tabs.js; never write, rebuild or delete those documents from this refresh.
  They change only when Bobby shares new model versions: run store/build_ai_models.py on the new workbooks and write
  each output JSON to its document (ArtifactData update with file_path).

Finish with a short summary: mode, routines read (and any missed), new prints, stories written / not found,
rows written to each history table, which comps workbook/sheets were used, and any source that failed.
