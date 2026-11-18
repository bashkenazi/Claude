# Markets weekly (Bobby Tech Daily › Markets tab)

Weekly read of macro and technical indicators to judge market direction (drawdown risk) and cyclicals vs defensives.
It feeds the **Markets** tab of Bobby Tech Daily (https://claude.ai/artifact/4WAMJK6NEWt1dqETwd2Zcc) and Supabase.

## Data

| Layer | Source | Span |
|---|---|---|
| History | Bloomberg "Market historicals" exports (`raw/bbg_*.csv`, parsed by `parse_bbg.py`) | 1970 – Jul 2018 |
| Macro extension | FactSet Macroeconomics (Fed H.15 yields, BLS, Census, DOL claims, Michigan, regional Fed surveys, H.8, M2) | to latest release |
| Prices | FactSet Global Prices: SPY, RSP, sector SPDRs, HYG/IEF, gold, copper, dollar, factor ETFs (weekly from 2006, daily last 14 months, monthly total returns) | 2006 – today |
| Breadth | Technicals tab page doc `technicals/breadth` (Hex project "Market breadth: advance/decline by market") | May 2025 – today |

S&P 500 after July 2018 is SPY rescaled to SPX at the overlap. ISM after July 2018 is a proxy fitted on the Empire State,
Dallas and Kansas City Fed surveys (R² about 0.73) until the Bloomberg sheet is extended.

**Still missing (FactSet does not carry them):** ISM PMI and new orders, Conference Board confidence and LEI, S&P and
Nasdaq forward P/E, HY OAS, global PMIs, NYSE advance/decline, put/call, AAII. To close the gaps, add these Bloomberg
tickers to the sheet, re-export to `raw/` and re-run `parse_bbg.py`: NAPMPMI, NAPMNEWO, CONCCONF, LEI TOTL,
SPX/CCMP BEST_PE_RATIO, LF98OAS, MOODCBAA, MPMIEZMA, CPMINDX, NYA ADV/DECL, PCUSEQTR, AAIIBULL.

## Pipeline

1. `parse_bbg.py`: Bloomberg CSVs → `data/bbg_monthly.csv` (one-off, or when a new export lands).
2. FactSet pulls (`fetch_plan.json`): history is committed in `data/factset_raw/`. Each weekly run pulls from 2024 and
   saves to `data/factset_new/`, which overlays the history.
3. `build_panel.py`: splice into a monthly panel (`data/panel.csv`).
4. `study.py`: signals, backtests (`data/study.json`), composites and the scorecard (`data/scorecard.json`).
5. `make_outputs.py`: call-outs, page-db docs (`out/pagedb/*.json`, each < 256 KiB) and Supabase upserts (`out/sql/*.sql`).
   `--full` writes all history; the default writes the last 18 months.

## Storage

Supabase project `hftouzahniiwigcchvje` (migration `migrations/20261118140000_markets_macro.sql`):
`macro_series`, `macro_observations` (series × month-end), `market_signal_snapshots` (weekly state of each signal),
`market_regime_snapshots` (weekly composite scores, headline and call-outs).

Page database of Bobby Tech Daily, collection `markets`: `summary`, `study`, `series_macro`, `series_sig`, `series_px`.
The tab code is `page/markets.js`, published as `mk/markets.js` beside the page.

## Running it

- **Scheduled:** the scheduled task "Markets weekly refresh" runs Sundays, prompt in [`PROMPT.md`](PROMPT.md).
- **On demand:** in a Claude Code session on this repo, "run the markets weekly refresh".

## Method notes

- Market signals are scored against the S&P's next-12-month price return and the odds of a 15%+ drawdown within
  12 months (1970 onward). Rotation signals are scored against cyclicals (XLY XLI XLB XLF XLE) minus defensives
  (XLP XLU XLV), next 6 months, total return, 2006 onward.
- The t-statistics shrink the sample by the window overlap. Most single signals sort drawdown risk better than
  they forecast returns.
- Market composite: trend (10-month average), yield curve, claims vs 12-month low, HYG/IEF trend, permits, core-CPI
  direction, forward P/E. Rotation composite: ISM and Empire 6-month change, core-CPI direction, sentiment, and
  contrarian claims and ISM level. A signal with data more than 3 months old does not vote.
