# Earnings Monitor

A Claude artifact that puts Bobby's earnings reviews and Rebecca's earnings recaps side by side, newest first, from a start date (default 2026-10-01).

## Sources

| Side | Skill | Where the output lives |
|---|---|---|
| Bobby | `earnings-preview` | Notion › Work Process › Anthropic › Anthropic Output, pages titled `🟢 Company (TICKER) — 3Q26 Earnings — YYYY-MM-DD` (title emoji = tone) |
| Rebecca | `earnings-recap` | SharePoint › SRS › Research › Rebecca › Claude › Earnings Recaps, PDFs named `Company_Quarter_YYYY-MM-DD.pdf` |

## Build

1. Extract each source into a JSON array (`bobby.json`, `rebecca.json`) of records:

```json
{
  "source": "bobby | rebecca",
  "ticker": "GOOGL", "company": "Alphabet", "quarter": "3Q26", "report_date": "2026-10-28",
  "sentiment": "very_positive | positive | mixed | negative | very_negative",
  "sentiment_label": "Rebecca's exact label (optional)",
  "headline": "one-sentence verdict",
  "summary": ["3-6 bullets"],
  "whats_changing": ["0-5 bullets"],
  "numbers": [{"metric": "", "actual": "", "street": "", "vs_street": "", "note": ""}],
  "tenets": [{"tenet": "", "status": "improved | deteriorated | no change | new | dropped"}],
  "questions": ["up to 3"],
  "reaction": "stock move or null", "pass": "Pass 1 or null",
  "sector": "Semis | Hardware | Software | Internet | IT Services | Other",
  "title": "", "url": "link to the Notion page or SharePoint PDF"
}
```

2. Render the page:

```bash
python3 build.py bobby.json rebecca.json earnings-monitor.html --since 2026-10-01
```

3. Publish `earnings-monitor.html` to the existing artifact URL with the Artifact tool. Read the artifact first, then republish to the same URL so the link stays the same.

Pairing: a review and a recap are matched when the tickers agree and the print dates are within 3 days. Split view = one side positive, the other negative.

The built HTML embeds research content, so don't commit it. Only the template and the build script live here.

## History in Supabase

Everything the page shows is also written to Supabase so it can be read back as a time series:
`earnings_prints`, `earnings_metrics`, `earnings_assessments`, `daily_moves`, `tech_daily_snapshots`
(see `store/schema.sql`). `store/parse_reviews.py <scratch>` parses the built page plus the review
markdown into `parsed.json`; `store/reviews_to_sql.py <scratch>` turns that into idempotent upsert batches.
Full review text (`earnings_prints.review_md`) loads once the Supabase host is reachable from the session.

## SRS AI models (AI tab › SRS models)

The AI tab's first section shows SRS's AI industry models (AI Master Model, AI Economics Master, AI Financings).
The numbers live in the page database, collection `ai_models` (docs `meta`, `capex`, `revisions`, `compute`, `econ`,
`labs`, `fin`, `supply`), not in the built HTML, so the scheduled refreshes never touch them. To load new model versions:

```bash
python3 store/build_ai_models.py --master AI_Master_Model_vNN.xlsx --econ AI_Economics_Master_vNN.xlsx \
    --fin AI_Financings_vN.xlsx --out <dir>
```

then write each `<dir>/<doc>.json` to its document in `ai_models` (ArtifactData `set` with `file_path`, pinned to the
current version). The extractor finds rows by their labels, so it survives inserted rows; it stops with an error if a
label it needs is renamed.
