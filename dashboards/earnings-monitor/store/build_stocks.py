#!/usr/bin/env python3
"""Stocks tab data: one entry per Companies DB Tier 1-2 name.

Usage: python3 build_stocks.py <tiers.json> <research.json> <labels.json> <aliases.json> <metrics.json> <out.json>
       [--debate a.json,b.json,...] [--theses theses_revised.json]

--debate   written debates {key: {bull[], bear[], decides[], tenets[{tenet, conviction, lean, evidence}]}}
--theses   tenets from the Notion "Thesis - Revised" pages {pages: [{company, ticker, url, summary_pitch, stance, tenets[]}]}

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
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_datapoints import FAM_OF

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
    args = sys.argv[1:]
    opt = {}
    for flag in ("--debate", "--theses"):
        if flag in args:
            i = args.index(flag); opt[flag] = args[i + 1]; del args[i:i + 2]
    sys.argv[1:] = args
    tiers, research, labels, aliases, metrics = (json.load(open(a)) for a in sys.argv[1:6])
    debate = {}
    for f in (opt.get("--debate") or "").split(","):
        if f:
            try: debate.update(json.load(open(f)))
            except Exception as e: print("skip", f, e)
    theses = []
    if opt.get("--theses"):
        try: theses = [p for p in json.load(open(opt["--theses"])).get("pages", []) if p.get("tenets")]
        except Exception as e: print("skip theses", e)
        # several revised pages per company: the newest wins (dates appear in "updated" as written)
        theses.sort(key=lambda p: max(re.findall(r"\d{4}-\d{2}-\d{2}", str(p.get("updated") or "")) or [""]), reverse=True)
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
        subs = [x for x in sub if x]
        fam = next((FAM_OF[x] for x in subs if x in FAM_OF), None) or ("Software" if "AI Labs (private)" in subs or "Holding Cos" in subs else "Other")
        out.append({"key": re.sub(r"[^A-Za-z0-9]+", "-", disp).strip("-"), "t": disp, "bbg": bbg, "name": nm or c.get("t"), "tier": c.get("r"),
                    "sector": fam, "sub": ", ".join(subs), "subs": subs, "coverage": c.get("s") or "", "rids": rids, "drivers": drivers, "metrics": mrows})
    def match_thesis(c):
        keys = {norm(c["t"]), norm(c["bbg"]), norm(c["t"]).split()[0] if c["t"] else ""}
        nm = re.sub(r"[^a-z0-9]", "", (c["name"] or "").lower())
        for p in theses:
            pt = norm(p.get("ticker") or "")
            pc = re.sub(r"[^a-z0-9]", "", re.sub(r"thesis.*$", "", (p.get("company") or "").lower()))
            if (pt and (pt in keys or pt.split()[0] in keys)) or (pc and len(pc) >= 3 and (nm.startswith(pc) or pc.startswith(nm[:max(4, len(pc))]))):
                return p
        return None
    for c in out:
        if c["key"] in debate: c["debate"] = debate[c["key"]]
        p = match_thesis(c)
        if p: c["thesis"] = {k: p.get(k) for k in ("url", "summary_pitch", "stance", "tenets", "updated", "company")}
    print(f"debates {sum(1 for c in out if c.get('debate'))} · revised theses {sum(1 for c in out if c.get('thesis'))}")
    out.sort(key=lambda x: (x["tier"] or 9, x["t"]))
    json.dump({"companies": out}, open(sys.argv[6], "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out)} companies · {sum(1 for x in out if x['rids'])} with evidence · {sum(1 for x in out if x['metrics'])} with earnings tables · "
          f"{sum(len(x['drivers']) for x in out)} named drivers")
    print("no evidence:", [x["t"] for x in out if not x["rids"]])


if __name__ == "__main__":
    main()
