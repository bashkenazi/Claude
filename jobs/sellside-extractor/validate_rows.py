#!/usr/bin/env python3
"""Mechanical checks on sellside-pdf-extractor output.

Usage: python3 -I validate_rows.py OUT.json IN.json [IN.json ...]

Each IN file is one subagent's JSON reply. OUT gets, per file, the parse status, coverage
flags and, per row, a list of contract errors. Judgment (admission, dedup, mapping) stays
with the orchestrator; this only catches what a script can catch reliably.
"""
import datetime
import json
import re
import sys

FIELDS = ("research_id", "field_key", "evidence_text", "field_impact", "event_date",
          "primary_source", "secondary_source", "source_type", "confidence")
VALIDATION_ONLY = ("ticker", "company", "source_quotes", "page_hint", "disposition", "hold_reason")
FIELD_KEYS = {"growth_driver", "margin_driver", "competition", "shareholder_return", "tam", "risk"}
IMPACTS = {"positive", "negative", "mixed"}
SOURCE_TYPES = {"sell_side", "independent_research", "company"}
CONFIDENCE = {"high", "medium", "low"}
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def norm_numbers(text):
    return {n.replace(",", "") for n in NUMBER.findall(text or "")}


def parse_date(value):
    try:
        return datetime.date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def check_row(row, today):
    errors = []
    extra = set(row) - set(FIELDS) - set(VALIDATION_ONLY)
    if extra:
        errors.append(f"unexpected keys: {sorted(extra)}")
    missing = [f for f in FIELDS if f not in row]
    if missing:
        errors.append(f"missing keys: {missing}")
    rid = row.get("research_id")
    if rid is not None and not (isinstance(rid, int) and rid >= 1):
        errors.append("research_id not a positive integer or null")
    if row.get("field_key") not in FIELD_KEYS:
        errors.append(f"bad field_key: {row.get('field_key')!r}")
    if row.get("field_impact") not in IMPACTS:
        errors.append(f"bad field_impact: {row.get('field_impact')!r}")
    if row.get("source_type") not in SOURCE_TYPES:
        errors.append(f"bad source_type: {row.get('source_type')!r}")
    if row.get("confidence") not in CONFIDENCE:
        errors.append(f"bad confidence: {row.get('confidence')!r}")
    event = parse_date(row.get("event_date"))
    if event is None:
        errors.append(f"bad event_date: {row.get('event_date')!r}")
    elif event > today + datetime.timedelta(days=7):
        errors.append("event_date more than 7 days in the future")
    if not (row.get("evidence_text") or "").strip():
        errors.append("empty evidence_text")
    if not (row.get("primary_source") or "").strip():
        errors.append("empty primary_source")
    if row.get("secondary_source") == "" or (isinstance(row.get("secondary_source"), str)
                                             and not row["secondary_source"].strip()):
        errors.append("secondary_source is an empty string (use null)")
    quotes = row.get("source_quotes") or []
    if not quotes or not all(isinstance(q, str) and q.strip() for q in quotes):
        errors.append("no source_quotes")
    unsupported = norm_numbers(row.get("evidence_text")) - norm_numbers(" ".join(quotes))
    if unsupported:
        errors.append(f"numbers not found in quotes: {sorted(unsupported)}")
    if row.get("disposition") not in ("keep", "hold"):
        errors.append(f"bad disposition: {row.get('disposition')!r}")
    if rid is None and not (row.get("ticker") and row.get("company")):
        errors.append("research_id null without ticker and company")
    return errors


def check_file(entry, today):
    rows = entry.get("rows") or []
    return {
        "drive_item_id": entry.get("drive_item_id"),
        "complete_read": entry.get("complete_read") is True,
        "pages": f"{entry.get('pages_read')}/{entry.get('page_count')}",
        "publication_date": entry.get("publication_date"),
        "publication_date_basis": entry.get("publication_date_basis"),
        "rows": [{"index": i, "errors": check_row(r, today)} for i, r in enumerate(rows)],
        "row_count": len(rows),
        "cut_count": len(entry.get("cuts") or []),
    }


def main(out_path, in_paths):
    today = datetime.date.today()
    report = []
    for path in in_paths:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            files = data["files"]
            if not isinstance(files, list):
                raise ValueError("'files' is not a list")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report.append({"input": path, "parse_error": str(exc)})
            continue
        report.append({"input": path, "files": [check_file(f, today) for f in files]})
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    bad_rows = sum(1 for r in report for f in r.get("files", []) for row in f["rows"] if row["errors"])
    parse_errors = sum(1 for r in report if "parse_error" in r)
    incomplete = sum(1 for r in report for f in r.get("files", []) if not f["complete_read"])
    print(f"inputs={len(report)} parse_errors={parse_errors} incomplete_files={incomplete} rows_with_errors={bad_rows}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
