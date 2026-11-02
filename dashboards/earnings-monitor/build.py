#!/usr/bin/env python3
"""Build the Earnings Monitor artifact page.

Usage: python3 build.py <bobby.json> <rebecca.json> <out.html> [--since YYYY-MM-DD] [--tabs DIR]

--keep-full HTML  previously built page whose full reviews are carried over
--full DIR   folder of full review pages as Notion markdown (<TICKER>_<date>.md; line 1 title, line 2 url)
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


TONES = [("🟢🟢", "very_positive"), ("🔴🔴", "very_negative"), ("🟢", "positive"), ("🔴", "negative"), ("🟠", "mixed"), ("🟡", "mixed")]


def _plain(h):
    import re, html as _h
    return _h.unescape(re.sub(r"<[^>]+>", " ", h)).replace("  ", " ").strip()


# sector for review pages whose ticker has no extracted record to borrow a sector from
SECTOR_FALLBACK = {
    "Semis": "3661 6515 3680 IFX WOLF GFS LSCC MKSI NVTS SITM SMTC SOI TSEM ONTO AEHR MTSI AAOI WAF 3436 5347 CBRS 2337 6920 6857 005930 2408 2454 2337 2330 TSM 6920 8035 AIXA ASML ASM BESI ENTG FORM KLAC MPWR NXPI RMBS SNDK STM TXN UCTT AMD NVDA AVGO MRVL MU QCOM ADI ON MCHP AMAT LRCX TER 6857 6146 CRDO ALAB COHR LITE ARM SMCI",
    "Hardware": "2313 3665 3017 3081 3110 2345 2059 5801 5803 992 6976 5706 SANM P FN HPE DELL 2382 009150 300308 APH TEL GLW CLS FLEX JBL VRT STX WDC TTMI 3037 2383 4062 285A ANET CSCO DELL HPE NTAP PSTG HPQ AAPL CIEN FN 2317 2382 3231",
    "Power & DC infra": "FRMI HUT FPS BE GEV ETN PWR NVT HUBB MOD SBGSY TT CEG VST TLN OKLO",
    "IT Services": "CTSH HCLT TCS WPRO INFY ACN EPAM IBM",
    "Software": "SHOP RBRK IOT DDOG MDB INTU CRWD NET FFIV MSFT NOW CDNS SNPS ORCL CRM ADBE PANW CRWD FTNT ZS NET DDOG SNOW MDB PLTR TWLO WDAY INTU",
    "Internet": "CRWV NBIS DOCN GOOGL GOOG META AMZN NFLX UBER",
    "Holding cos": "9984",
    "Autos & space": "TSLA SPCX",
}
SECTOR_OF = {t: sec for sec, ts in SECTOR_FALLBACK.items() for t in ts.split()}


def record_from_page(title, url, sections, known):
    """Minimal Earnings-tab record from a review page: tone, ticker, quarter, date, summary bullets."""
    import re
    m = re.search(r"^([🟢🔴🟠🟡\s]*)(.+?)\s+\(([^)]+)\)\s+—\s+(.+?)\s+Earnings(?: Review)?\s+—\s+(\d{4}-\d{2}-\d{2})", title)
    if not m:
        return None
    dots = m.group(1).replace(" ", "")
    tone = next((t for k, t in TONES if k in dots), "mixed")
    ticker = m.group(3).split("/")[0].strip()
    if ticker.endswith(" JT"):  # one Tokyo listing, two suffixes in use
        ticker = ticker[:-3] + " JP"
    flat = []
    for s in sections:
        flat += s.get("subs", [s])
    summ = next((s for s in flat if "summary" in s["title"].lower()), flat[0] if flat else None)
    bullets = re.findall(r"<li>\s*(.*?)\s*(?=<ul>|</li>)", summ["html"], re.S) if summ else []
    bullets = [_plain(x) for x in bullets if _plain(x)][:6]
    paras = [_plain(x) for x in re.findall(r"<p>(.*?)</p>", summ["html"], re.S)] if summ else []
    headline = (paras[0] if paras else (bullets[0] if bullets else ""))[:260]
    sector = SECTOR_OF.get(ticker.split()[0]) or next((r.get("sector") for r in known if r.get("ticker", "").split()[0] == ticker.split()[0] and r.get("sector")), "Other")
    return {"source": "bobby", "ticker": ticker, "company": m.group(2).strip(), "quarter": m.group(4).strip(),
            "report_date": m.group(5), "sentiment": tone, "headline": headline, "summary": [b for b in bullets if b != headline][:6],
            "whats_changing": [], "numbers": [], "reaction": None, "pass": None, "sector": sector,
            "title": title, "url": url, "sources": [], "skill": "earnings-review"}


def main():
    args = sys.argv[1:]
    since = "2026-10-01"
    if "--since" in args:
        i = args.index("--since")
        since = args[i + 1]
        del args[i:i + 2]
    full_dir = None
    if "--full" in args:
        i = args.index("--full")
        full_dir = Path(args[i + 1])
        del args[i:i + 2]
    keep_full = None
    if "--keep-full" in args:  # a previously built page: its full reviews are kept unless a newer md replaces them
        i = args.index("--keep-full")
        keep_full = Path(args[i + 1])
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
    for name in ("today", "datapoints", "screens", "ideas", "prep", "sources", "earn_assess", "signals", "comps", "daily", "earn_assess_cq2"):
        f = tabs / f"{name}.json" if tabs else None
        payload[name] = json.loads(f.read_text()) if f and f.exists() else {}
    payload["full"] = {}
    if keep_full and keep_full.exists():
        import base64, gzip, re as _re
        m = _re.search(r'<script id="data"[^>]*>(.*?)</script>', keep_full.read_text(), _re.S)
        prev = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
        if prev.get("full_gz"):
            payload["full"].update(json.loads(gzip.decompress(base64.b64decode(prev["full_gz"]))))
        else:
            payload["full"].update(prev.get("full") or {})
    if full_dir and full_dir.exists():
        sys.path.insert(0, str(HERE))
        from md2html import convert
        for f in sorted(full_dir.glob("*.md")):
            title, url, sections = convert(f.read_text())
            if url and sections:
                payload["full"][url.split("?")[0]] = {"title": title, "sections": sections}
                # a review page with no extracted record yet gets a minimal card built from the page itself
                known = {r.get("url", "").split("?")[0] for r in bobby}
                if url.split("?")[0] not in known:
                    rec = record_from_page(title, url, sections, bobby + rebecca)
                    if rec and rec["report_date"] >= since:
                        bobby.append(rec)
    # a local earnings-review page supersedes older preview/review notes on the same print (same ticker, same date)
    key = lambda r: (r.get("ticker", "").split("/")[0].split()[0] if r.get("ticker") else "", r.get("report_date", ""))
    fresh = {key(r) for r in bobby if str(r.get("url", "")).startswith("local:")}
    dropped = [r for r in bobby if key(r) in fresh and not str(r.get("url", "")).startswith("local:")]
    bobby[:] = [r for r in bobby if r not in dropped]
    for r in dropped:
        payload["full"].pop(str(r.get("url", "")).split("?")[0], None)
    payload["bobby"] = bobby
    # ship the full review pages compressed; the page unpacks them in the browser
    import base64, gzip
    payload["full_gz"] = base64.b64encode(gzip.compress(json.dumps(payload["full"], ensure_ascii=False).encode(), 9)).decode()
    payload["full"] = {}
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
