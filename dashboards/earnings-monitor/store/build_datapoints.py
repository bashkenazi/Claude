#!/usr/bin/env python3
"""Datapoints tab data + Composite Evidence Index (v3) from a research_evidence export.

Usage: python3 build_datapoints.py <evidence.json> <research.json> <universe.json> <out_dir> [--asof YYYY-MM-DD]

evidence.json : [{id, r (research_id), k (field_key), i (field_impact), d (event_date), c (confidence),
                  s (source_type), p (primary_source), q (secondary_source), t (evidence_text)}]
research.json : [{id, ticker, n (company name), sector, subsector}]
universe.json : the Master comps universe (tabs/universe.json: names[{id, t, n, g}])

Writes <out_dir>/dp_index.json (embedded in the page: companies, sectors, weekly index series) and
<out_dir>/dp/part<N>.json (the rows, fetched by the page on demand; each part < 6 MB).

Composite Evidence Index v3 (based on Bobby's Hex "Composite Index v2 — reliability x decay x shrinkage"):
  signal    = direction (positive +1, negative -1, mixed 0) x confidence (high 1.0, medium 0.75, low 0.5)
              [Hex v2 used an LLM 5-point score; a stored LLM score can replace this term later]
  weight    = source reliability x 0.5 ** (age_days / 90)
              reliability: company/management/filings 1.0, channel checks & independent research 1.0,
              sell-side 0.6, news/substack/email 0.5, evernote 0.6, twitter 0.3, reddit 0.2,
              anything marked inferred/estimate 0.3
  pillar    = shrunk weighted mean per pillar: raw * W / (W + 5)          (W = sum of weights)
              pillars: Growth (growth drivers + TAM) 0.40, Margins 0.25, Competition 0.20, Risk 0.15
  composite = sum(pillar weight x pillar), x100 -> -100..+100
  excess    = composite minus the same calculation on the whole universe at that date (removes the
              ~75% positive skew of sell-side evidence, so 0 = "as positive as everything else")
  Series are weekly (Fridays) from the first week with data; also 30-day change and evidence count.
"""
import json, re, sys, math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

HALF_LIFE, SHRINK_K = 90.0, 5.0
PILLARS = {"Growth": 0.40, "Margins": 0.25, "Competition": 0.20, "Risk": 0.15}
CONF = {"high": 1.0, "medium": 0.75, "low": 0.5}
REL_TYPE = {"company": 1.0, "independent_research": 1.0, "sell_side": 0.6, "news": 0.5, "substack": 0.5,
            "email": 0.5, "evernote": 0.6, "fintool": 0.5, "twitter": 0.3, "reddit": 0.2}
CHANNEL = re.compile(r"semianalysis|cleveland|\bbwg\b|trendforce|\bidc\b|counterpoint|gartner|expert call|third bridge|"
                     r"guidepoint|tegus|digitimes|sensor tower|yipit|channel check|supply chain check|distributor", re.I)
GUIDE = re.compile(r"management|earnings call|transcript|\bir\b|investor day|analyst day|\bcfo\b|\bceo\b|10-k|10-q|8-k|"
                   r"press release|filing|guidance", re.I)
INFER = re.compile(r"\(inferred\)|inferred|extrapolat|triangulat|speculat", re.I)

FAMILY = {
    "Semis": "Analog|Power Semis|Autos & Industrial Semis|CPU & Other Compute|Parallel Compute|DRAM|NAND|Foundry|Wireless Semis|"
             "Other Semis|WFE Vendors|WFE Suppliers|Packaging Equipment|Testing|OSAT & Packaging|Wafers",
    "Hardware": "Optical|Optical Upstream|Networking|ODMs/OEMs|PCB Substrates|MLCCs|HDDs|Storage Systems|Distributors|Connectors|Devices",
    "Power & DC infra": "DataCenter Power and HVAC|Power EPC|Power Generation & EPC|IPPs|Nuclear and Other|DC Infra, Colo & Bitminers|"
                        "DC Infra / Colo & Bitminers|GPU Rental",
    "Software": "Software|Holding Cos|AI Labs (private)",
    "IT Services": "IT Services",
    "Internet": "Internet",
}
FAM_OF = {s: f for f, ss in FAMILY.items() for s in ss.split("|")}


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from build import SECTOR_FALLBACK as _SF
    FALLBACK = {t: ("Power & DC infra" if f == "Power & DC infra" else f if f in FAMILY else ("Software" if f == "Holding cos" else "Other"))
                for f, ts in _SF.items() for t in ts.split()}
except Exception:
    FALLBACK = {}
KW = [("Semis", r"semicon|chip|foundry|memory|dram|nand|wafer|analog|lithograph|equipment|wfe|eda"),
      ("Hardware", r"hardware|optical|network|storage|substrate|pcb|passive|mlcc|connector|server|odm|oem|electronic comp|communications equip|display"),
      ("Power & DC infra", r"power|energy|utilit|electric|nuclear|data ?cent|colo|bitcoin|miner|hvac|cooling"),
      ("Software", r"software|saas|cyber|security|cloud|database|ai lab"),
      ("IT Services", r"it services|consult|outsourc"),
      ("Internet", r"internet|e-?commerce|social|search|advertis|marketplace|streaming")]


def kw_family(*vals):
    v = " ".join(str(x) for x in vals if x).lower()
    if v.upper().startswith("INDUSTRY") or "industry_" in v: return "Industry"
    for f, rx in KW:
        if re.search(rx, v): return f
    return "Other"


def pillar(k):
    k = (k or "").lower()
    if k.startswith("growth") or k.startswith("tam"): return "Growth"
    if k.startswith("margin"): return "Margins"
    if k.startswith("competition"): return "Competition"
    if k.startswith("risk"): return "Risk"
    return None


def reliability(st, p):
    p = p or ""
    if INFER.search(p): return 0.3
    if CHANNEL.search(p): return 1.0
    if GUIDE.search(p): return 1.0
    return REL_TYPE.get(st or "", 0.5)


def norm(t):
    t = (t or "").upper().replace(" EQUITY", "").strip()
    t = re.sub(r"\s+JP$", " JT", t)
    return re.sub(r"\s+US$", "", t)


def fridays(start, end):
    d = start + timedelta(days=(4 - start.weekday()) % 7)
    while d <= end:
        yield d; d += timedelta(days=7)
    if d - timedelta(days=7) < end: yield end


def series(evs, dates):
    """evs: list of (date, pillar, signal, rel). Returns per-date composite, pillars, n (decayed weight)."""
    evs = sorted(evs)
    out = []
    for D in dates:
        acc = {p: [0.0, 0.0] for p in PILLARS}
        n90 = 0
        for (d, p, s, r) in evs:
            if d > D: break
            age = (D - d).days
            w = r * 0.5 ** (age / HALF_LIFE)
            acc[p][0] += s * w; acc[p][1] += w
            if age <= 90: n90 += 1
        pv = {}
        comp = 0.0
        for p, (sw, w) in acc.items():
            raw = sw / w if w else 0.0
            pv[p] = raw * w / (w + SHRINK_K)
            comp += PILLARS[p] * pv[p]
        out.append((round(comp * 100, 1), {p: round(v * 100, 1) for p, v in pv.items()}, n90))
    return out


def main():
    a = sys.argv[1:]
    asof = None
    if "--asof" in a:
        i = a.index("--asof"); asof = date.fromisoformat(a[i + 1]); del a[i:i + 2]
    ev, rs, un, out = json.load(open(a[0])), json.load(open(a[1])), json.load(open(a[2])), Path(a[3])
    out.mkdir(parents=True, exist_ok=True); (out / "dp").mkdir(exist_ok=True)
    uni = {}
    for n in un.get("names", []):
        uni.setdefault(norm(n["t"]), n); uni.setdefault(norm(n["t"]).split()[0], n)
    ov = {}
    try:
        for f, ts in json.load(open(Path(__file__).with_name("sector_overrides.json"))).items():
            if not f.startswith("_"): ov.update({t.upper(): f for t in ts})
    except Exception:
        pass
    comp = {}
    for r in rs:
        k = norm(r.get("ticker"))
        u = uni.get(k) or (uni.get(k.split()[0]) if k and len(k.split()) == 1 else None) or {}
        sub = u.get("g") or ""
        sec = ov.get((r.get("ticker") or "").upper()) or FAM_OF.get(sub) or FALLBACK.get(k.split()[0] if k else "") or kw_family(r.get("subsector"), r.get("sector"), r.get("n"), k)
        comp[r["id"]] = {"t": r.get("ticker") or r.get("n") or str(r["id"]), "n": r.get("n") or u.get("n") or "",
                         "sub": sub or r.get("subsector") or sec, "sec": sec}
    # rows the cleanup tagged "[ARCHIVED dup_of=…]" are duplicates kept in Supabase for audit; leave them out
    ev = [e for e in ev if e.get("d") and not str(e.get("t") or "").lstrip().startswith("[ARCHIVED")]
    last = asof or max(date.fromisoformat(e["d"]) for e in ev)
    first = min(date.fromisoformat(e["d"]) for e in ev)
    dates = list(fridays(first, last))
    # rows (columnar, sources interned)
    src_ix, srcs = {}, []
    def sx(v):
        if not v: return -1
        if v not in src_ix: src_ix[v] = len(srcs); srcs.append(v)
        return src_ix[v]
    ev.sort(key=lambda e: (e["d"], e["id"]), reverse=True)
    rows = [[e["id"], e["r"], e["d"], e.get("k") or "", {"positive": 1, "negative": -1, "mixed": 0}.get(e.get("i"), None),
             (e.get("c") or "")[:1], e.get("s") or "", sx(e.get("p")), sx(e.get("q")), e.get("t") or ""] for e in ev]
    parts, cur, size = [], [], 0
    for r in rows:
        cur.append(r); size += len(r[9]) + 40
        if size > 4_500_000: parts.append(cur); cur, size = [], 0
    if cur: parts.append(cur)
    # sources split across parts by id range is awkward; ship the full source table with each part's index
    for i, p in enumerate(parts, 1):
        json.dump({"cols": ["id", "rid", "date", "field", "dir", "conf", "stype", "psrc", "ssrc", "text"], "rows": p},
                  open(out / "dp" / f"part{i}.json", "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump({"sources": srcs}, open(out / "dp" / "sources.json", "w"), ensure_ascii=False, separators=(",", ":"))
    # index
    by_r, by_sec, allv = defaultdict(list), defaultdict(list), []
    cnt = defaultdict(int)
    for e in ev:
        p = pillar(e.get("k")); cnt[e["r"]] += 1
        if not p: continue
        d = date.fromisoformat(e["d"])
        sig = {"positive": 1, "negative": -1}.get(e.get("i"), 0) * CONF.get(e.get("c") or "", 0.75)
        x = (d, p, sig, reliability(e.get("s"), e.get("p")))
        by_r[e["r"]].append(x); allv.append(x)
        by_sec[(comp.get(e["r"]) or {}).get("sec", "Other")].append(x)
    base = series(allv, dates)
    def pack(s):
        c = [v[0] for v in s]
        ex = [round(v[0] - b[0], 1) for v, b in zip(s, base)]
        return {"c": c, "x": ex, "g": [v[1]["Growth"] for v in s], "m": [v[1]["Margins"] for v in s],
                "k": [v[1]["Competition"] for v in s], "r": [v[1]["Risk"] for v in s], "e": [v[2] for v in s]}
    cos = []
    for rid, evs in by_r.items():
        if len(evs) < 5: continue
        m = comp.get(rid, {"t": str(rid), "n": "", "sub": "Other", "sec": "Other"})
        s = pack(series(evs, dates))
        cos.append({"rid": rid, "t": m["t"], "n": m["n"], "sec": m["sec"], "sub": m["sub"], "count": cnt[rid], **s})
    secs = [{"sec": k, **pack(series(v, dates))} for k, v in by_sec.items()]
    meta = [{"rid": rid, **{k: v for k, v in m.items()}, "count": cnt.get(rid, 0)} for rid, m in comp.items() if cnt.get(rid)]
    json.dump({"as_of": last.isoformat(), "since": first.isoformat(), "n_rows": len(rows), "parts": len(parts),
               "dates": [d.isoformat() for d in dates], "universe": pack(base), "companies": cos, "sectors": secs,
               "meta": meta, "method": __doc__.split("Composite Evidence Index v3", 1)[1].strip()},
              open(out / "dp_index.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"rows {len(rows)} in {len(parts)} parts · {len(cos)} companies indexed · {len(secs)} sectors · {len(dates)} weeks")


if __name__ == "__main__":
    main()
