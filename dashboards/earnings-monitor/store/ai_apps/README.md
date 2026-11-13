# AI Apps Data (nightly routine)

Copies the AI dashboards on apps.srsinvest.com/ai (S3 bucket `srsinvest-apps`, prefix `ai/`) into the Bobby Tech Daily page
database, document `ai/apps_signals`, which the page reads live:

- **AI › SRS apps data** (`#ai/apps`): headline numbers, callouts (what changed since the previous run), GPU rental indices
  (Ornn, Silicon Data, Nebius spot), LLM token prices, OpenRouter token share, lab ARR claims, every dashboard's headlines.
- **AI thesis › Signposts**: an "SRS apps" reading under the arr, gpu, china and capex signposts (`signposts` in the doc).
- **Routines / Today**: the routine's Notion run page ("AI Apps Data — YYYY-MM-DD", key `ai-apps-data`) carries the callouts,
  which the Tech Daily refresh reads like any other routine page.

## Files read (SRS MCP `s3` download, `keys`, 5 per call; run the returned script from <apps_dir>)
```
ai/gpu_spot_rental/data.json  ai/arr_estimates/data.json  ai/openrouter/data.json  ai/silicon_data/data.json
ai/taiwan_monthly/data.json   ai/dc_buildout/insights.json  ai/nvda_alternatives/insights.json  ai/silicon_data/insights.json
ai/ramp_ai/insights.json      ai/ai_web_signals/insights.json  ai/korean_memory/insights.json
ai/incremental_research/insights.json  ai/ai_server_trade/insights.json
```
The download script saves each file at its path relative to `ai/`. A missing `insights.json` is skipped; a missing
`data.json` stops the build (say which and do not write).

## Steps
1. Download the files above into a fresh empty folder `<apps_dir>`.
2. ArtifactData `get` collection `ai`, doc `apps_signals` with `out_dir` → previous doc (note its version).
3. `python3 -I build_apps_signals.py <apps_dir> <out>/apps_signals.json <prev>/ai/apps_signals.json`
4. ArtifactData `set` `ai/apps_signals` from the file with `if_version`; also `set` a dated copy `ai/apps_signals_YYYY-MM-DD`
   (no if_version when new).
5. Notion page under Anthropic Output (33ba883333de80a6ab40d2ed18985f31), title `AI Apps Data — YYYY-MM-DD`:
   `## Callouts` (one bullet per callout: `**AI** — text [dashboard]`), `## Key numbers` (calls), `## Thesis signposts`
   (signposts), `## Dashboards` (one line per dashboard with its link). Escape `$` as `\$`.
6. Do not publish or rebuild the artifact page; do not touch Supabase.

Owner of the source dashboards: see each page's `.srsdoc`. Compute Index GPU series are excluded (stale since 2026-09-08).
