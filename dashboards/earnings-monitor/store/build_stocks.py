#!/usr/bin/env python3
"""Stocks tab data: one entry per Companies DB Tier 1-2 name.

Usage: python3 build_stocks.py <tiers.json> <research.json> <labels.json> <aliases.json> <metrics.json> <out.json>

tiers.json    Companies DB rows [{t (Ticker), b (BBG Ticker), c (Company), s (Sector), u (Sub-sector JSON list), r (Tier)}]
research.json public.research [{id, ticker, n}]  (the research ids that have evidence)
labels.json   public.research driver names [{id, g1..g5, m1..m4, c1..c3, t1..t2, r1..r6}]
aliases.json  public.research driver aliases [{id, a1..a5, am2, at1, at2}]
metrics.json  earnings_metrics joined to earnings_prints [{ticker, cq, fq, d, verdict, section, metric, actual,
              street, bogey, vs_st, vs_bg, marker}]

Each company gets: key, t (display ticker), bbg, name, tier, sector, sub, rids (research ids matched by ticker or
name), drivers [{k, fam, label, kw}] (named drivers with match keywords from label + aliases), metrics (its earnings
review table rows). The page joins these to the datapoint rows it already loads (dp/part*.json) by research id.
"""
import json, re, sys

FAMS = [("g", "Growth", 5), ("t", "TAM", 2), ("m", "Margins", 4), ("c", "Competition", 3), ("r", "Risk", 6)]
STOP = set("the and for with from into over lt guidance revenue growth market share new long term of to in on by a an vs fy".split())


def norm(t):
    t = (t or "").upper().replace(" EQUITY", "").strip()
    t = re.sub(r"\s+JP$", " JT", t)
    return re.sub(r"\s+(US|UW|UN|UQ)$", "", t)


def kws(*texts):
    out = []
    for t in texts:
        if not t: continue
        t = re.sub(r'[\[\]{}"]', "", str(t))
        for part in re.split(r"[;,]", t):
            p = part.strip().lower()
            if len(p) >= 3 and p not in STOP and not re.fullmatch(r"[\d$€¥%.\-–+ ]+", p) and not p.startswith(("fy2", "q1 ", "q2 ", "q3 ", "q4 ")):
                out.append(p)
    return list(dict.fromkeys(out))[:40]


def main():
    tiers, research, labels, aliases, metrics = (json.load(open(a)) for a in sys.argv[1:6])
    lab = {r["id"]: r for r in labels}; ali = {r["id"]: r for r in aliases}
    by_t, by_n = {}, {}
    for r in research:
        by_t.setdefault(norm(r.get("ticker")), []).append(r["id"])
        if r.get("n"): by_n.setdefault(re.sub(r"[^a-z0-9]", "", r["n"].lower())[:10], []).append(r["id"])
    mt = {}
    for m in metrics: mt.setdefault(norm(m["ticker"]), []).append(m)
    out = []
    for c in tiers:
        bbg = c.get("b") or ""
        keys = [k for k in {norm(bbg), norm(c.get("t")), norm(bbg).split()[0] if bbg and (len(bbg.split()) < 2 or bbg.split()[1] == "US") else None} if k]
        rids = []
        for k in keys: rids += by_t.get(k, [])
        nm = re.sub(r"\s*\(.*?\)", "", c.get("c") or "")
        nk = re.sub(r"[^a-z0-9]", "", nm.lower())[:10]
        if not rids and len(nk) >= 4: rids += by_n.get(nk, [])
        rids = sorted(set(rids))
        drivers = []
        for rid in rids[:1]:
            L, A = lab.get(rid, {}), ali.get(rid, {})
            for pre, fam, n in FAMS:
                for i in range(1, n + 1):
                    label = L.get(f"{pre}{i}")
                    if not label: continue
                    alias = A.get(f"a{i}") if pre == "g" else A.get("am2") if (pre == "m" and i == 2) else A.get(f"at{i}") if pre == "t" else None
                    drivers.append({"k": f"{pre}{i}", "fam": fam, "label": label, "kw": kws(label.replace("/", ","), alias)})
        try: sub = json.loads(c.get("u") or "[]")
        except Exception: sub = [c.get("u")]
        disp = bbg.replace(" US", "") if bbg else (c.get("t") or "")
        ms = []
        for k in keys: ms += mt.get(k, [])
        seen, mrows = set(), []
        for m in ms:
            key = (m["cq"], m["section"], m["metric"])
            if key in seen: continue
            seen.add(key)
            mrows.append({x: m.get(x) for x in ("cq", "fq", "d", "verdict", "section", "metric", "actual", "street", "bogey", "vs_st", "vs_bg", "marker")})
        out.append({"key": re.sub(r"[^A-Za-z0-9]+", "-", disp).strip("-"), "t": disp, "bbg": bbg, "name": nm or c.get("t"), "tier": c.get("r"),
                    "sector": c.get("s") or "", "sub": ", ".join(x for x in sub if x), "rids": rids, "drivers": drivers, "metrics": mrows})
    out.sort(key=lambda x: (x["tier"] or 9, x["t"]))
    json.dump({"companies": out}, open(sys.argv[6], "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} companies · {sum(1 for x in out if x['rids'])} with evidence · {sum(1 for x in out if x['metrics'])} with earnings tables · "
          f"{sum(len(x['drivers']) for x in out)} named drivers")
    print("no evidence:", [x["t"] for x in out if not x["rids"]])


if __name__ == "__main__":
    main()
