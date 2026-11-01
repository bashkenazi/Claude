#!/usr/bin/env python3
"""Build the Earnings Monitor artifact page.

Usage: python3 build.py <bobby.json> <rebecca.json> <out.html> [--since YYYY-MM-DD] [--tabs DIR]

--tabs DIR   folder holding today.json, datapoints.json, screens.json, ideas.json, prep.json, sources.json
             (any missing file renders as an empty tab)

bobby.json   -- earnings reviews extracted from the earnings-preview skill's Notion pages
rebecca.json -- earnings recaps extracted from Rebecca's earnings-recap PDFs (SharePoint)
Both are JSON arrays of records; see README.md for the record shape.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(p):
    data = json.loads(Path(p).read_text())
    if not isinstance(data, list):
        raise SystemExit(f"{p}: expected a JSON array")
    return data


def main():
    args = sys.argv[1:]
    since = "2026-10-01"
    if "--since" in args:
        i = args.index("--since")
        since = args[i + 1]
        del args[i:i + 2]
    tabs = None
    if "--tabs" in args:
        i = args.index("--tabs")
        tabs = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 3:
        raise SystemExit(__doc__)
    bobby, rebecca, out = load(args[0]), load(args[1]), Path(args[2])
    bobby = [r for r in bobby if r.get("report_date", "") >= since]
    rebecca = [r for r in rebecca if r.get("report_date", "") >= since]
    payload = {
        "since": since,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "bobby": bobby,
        "rebecca": rebecca,
    }
    for name in ("today", "datapoints", "screens", "ideas", "prep", "sources", "earn_assess"):
        f = tabs / f"{name}.json" if tabs else None
        payload[name] = json.loads(f.read_text()) if f and f.exists() else {}
    # Escape "</" so the JSON can't close the <script> block.
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = (HERE / "template.html").read_text()
    html = html.replace("/*__EXTRA_CSS__*/", (HERE / "tabs.css").read_text())
    html = html.replace("/*__EXTRA_JS__*/", (HERE / "tabs.js").read_text())
    html = html.replace("/*__DATA__*/", blob)
    out.write_text(html)
    print(f"wrote {out} ({len(html):,} bytes): {len(bobby)} reviews, {len(rebecca)} recaps")


if __name__ == "__main__":
    main()
