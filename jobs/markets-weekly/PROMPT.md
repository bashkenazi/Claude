Run the weekly Markets refresh for Bobby Tech Daily (job: `jobs/markets-weekly` in this repo). Work from that directory.
Today's date is the run date (`ASOF`). Be precise: never retype or round a number a tool returned.

1. Load tools with ToolSearch: `select:mcp__FactSet__FactSet_Macroeconomics,mcp__FactSet__FactSet_GlobalPrices,mcp__Supabase__execute_sql,ArtifactData`.
   If FactSet or Supabase is missing, stop and report which connector is not connected.

2. FactSet pulls, from `fetch_plan.json`. FactSet rate-limits: at most 3 FactSet calls per message; on a 429, retry that call in the
   next message. Use one request_id (a new uuid4) for the whole run. Save every result with
   `python3 -I save_result.py <path> <name>`, where `<path>` is the file the harness saved an oversized result to. If a result
   came back inline, write it exactly as returned to a scratch file with the Write tool and pass that path.
   - `macro`: `FactSet_Macroeconomics`, data_type `as_reported_economics`, `seriesId`, `startDate` = `macro_start`, `endDate` = ASOF,
     `paginationLimit` 1000, plus `frequency` when it is not null. Save as `<name>`.
   - `prices_weekly`: `FactSet_GlobalPrices`, data_type `prices`, ids = batch, startDate from the plan, endDate ASOF, frequency `W`,
     fields `["price"]`, currency `USD`, adjust `SPLIT`. Save as `px_<batch>`.
   - `prices_daily`: same, frequency `D`, startDate = ASOF minus 14 months. Save as `px_<batch>` (batch names already start with `d_`).
   - `returns_monthly`: `FactSet_GlobalPrices`, data_type `returns`, frequency `M`, startDate from the plan, endDate = the last
     calendar month-end before ASOF, currency `USD`, dividendAdjust `EXDATE_C`. Save as `px_<batch>`.
   A series that errors twice is skipped and listed in the report; its committed history in `data/factset_raw` still applies.

3. Read the page database of Bobby Tech Daily (`https://claude.ai/artifact/4WAMJK6NEWt1dqETwd2Zcc`) with ArtifactData:
   `get` collection `technicals` doc `breadth`, and `list` collection `markets`, both with `out_dir` = `data/pagedb`.
   Note each `markets/*` document's `version` from the list result.

4. Build: `python3 -I build_panel.py && python3 -I study.py && python3 -I make_outputs.py --asof <ASOF>`.
   Check before loading anything: the scorecard has at least 25 signals; `SPX` has a value for the latest month-end;
   no page-db file is over 250 KiB (make_outputs asserts this). If a check fails, stop and report; do not load.

5. Supabase project `hftouzahniiwigcchvje`: run each file in `out/sql` in name order with `execute_sql`, passing the file's
   contents exactly (Read it, then send it unchanged). They are idempotent upserts into `macro_series`, `macro_observations`
   (last 18 months), `market_signal_snapshots` and `market_regime_snapshots`.

6. Page database: one ArtifactData `batch` of `set` writes to collection `markets` for `summary`, `study`, `series_macro`,
   `series_sig` and `series_px`, each with `file_path` = `out/pagedb/<doc>.json` and `if_version` = the version from step 3
   (omit `if_version` only for a document that did not exist). If the batch reports a version conflict, re-list and retry once.

7. Final message (this is what Bobby reads): the headline, the two composite scores with last week's values, and every
   call-out title from `out/pagedb/summary.json` as bullets. Then a one-line run note: series pulled, any skipped, rows loaded.
   Do not commit or push anything.
