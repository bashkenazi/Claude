#!/usr/bin/env python3
"""Extract the SRS AI models into the documents the Tech Daily AI tab reads (AI › SRS models).

Usage:
  python3 build_ai_models.py --master AI_Master_Model_vNN.xlsx --econ AI_Economics_Master_vNN.xlsx \
      --fin AI_Financings_vN.xlsx --out <dir>

Writes one JSON file per page-database document into <dir>: meta, capex, revisions, compute, econ, labs,
fin, supply. Load each into the Bobby Tech Daily page database, collection "ai_models", doc id = file stem
(ArtifactData "set", read first and pass if_version). The page reads them live; no rebuild or republish.

Rows are found by their label (and, for repeated labels, by the section they sit under), so inserted
rows in a new model version do not shift the output. If a label cannot be found the script stops and
names it: update the label here rather than guessing a row.
Values are the workbook's cached results (data_only), so save the workbooks in Excel before running.
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path

import openpyxl
from openpyxl.utils import column_index_from_string as CI

ERR = re.compile(r"^#(REF|N/A|VALUE|DIV/0|NAME|NUM|NULL)")


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


class Sheet:
    def __init__(self, name, rows):
        self.name, self.g = name, rows

    def v(self, r, c):
        if isinstance(c, str):
            c = CI(c)
        if r < 1 or r > len(self.g):
            return None
        row = self.g[r - 1]
        return row[c - 1] if c - 1 < len(row) else None

    def find(self, label, start=1, end=None, cols="A:H", exact=False, nth=1):
        """Row number of the nth row (from start) whose label cell matches. exact=False matches a prefix."""
        a, b = (CI(x) for x in cols.split(":"))
        want, hits = norm(label), 0
        for r in range(max(1, start), (end or len(self.g)) + 1):
            for c in range(a, b + 1):
                s = norm(self.v(r, c))
                if s and (s == want if exact else s.startswith(want)):
                    hits += 1
                    if hits == nth:
                        return r
                    break
        raise KeyError(f"{self.name}: label {label!r} not found in rows {start}-{end or len(self.g)}")

    def num(self, r, c):
        x = self.v(r, c)
        if isinstance(x, bool):
            return None
        if isinstance(x, (int, float)):
            return x
        if isinstance(x, str):
            t = x.strip().replace(",", "")
            if ERR.match(t) or not t:
                return None
            try:
                return float(t)
            except ValueError:
                return None
        return None

    def nums(self, r, cols, scale=1.0):
        out = []
        for c in cols:
            x = self.num(r, c)
            out.append(None if x is None else clean(x * scale))
        return out

    def text(self, r, c):
        x = self.v(r, c)
        if x is None:
            return ""
        if isinstance(x, (dt.datetime, dt.date)):
            return x.strftime("%Y-%m-%d")
        s = str(x).strip()
        return "" if ERR.match(s) else s


def clean(x):
    if x is None:
        return None
    if abs(x) >= 1000:
        return round(x, 1)
    if abs(x) >= 1:
        return round(x, 4)
    return round(x, 6)


def load(path, names):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    out = {}
    for n in names:
        ws = wb[n]
        out[n] = Sheet(n, [list(r) for r in ws.iter_rows(values_only=True)])
    return out


def cols(a, b):
    return list(range(CI(a), CI(b) + 1))


def R(label, values, f="num", b=False, ind=0, note=None):
    row = {"l": label, "v": values, "f": f}
    if b:
        row["b"] = 1
    if ind:
        row["ind"] = ind
    if note:
        row["note"] = note
    return row


def T(tid, title, columns, rows, src, unit="", note="", est_from=None):
    t = {"id": tid, "title": title, "cols": [str(c) for c in columns], "rows": rows, "src": src}
    if unit:
        t["unit"] = unit
    if note:
        t["note"] = note
    if est_from:
        t["est_from"] = str(est_from)  # first column that is a forecast (styled as estimate)
    return t


def growth(vals, floor=0.5):
    """y/y change; left blank off a tiny base (|prior| < floor) where the % would be noise."""
    out = [None]
    for p, c in zip(vals, vals[1:]):
        out.append(None if p is None or c is None or abs(p) < floor else clean(c / p - 1))
    return out


def years(a, b):
    return list(range(a, b + 1))


def build(master, econ, fin):
    MW = load(master, ["Overview", "Hyperscaler Capex Revisions", "XPU Model", "HBM Model", "Cowos chips and WFE", "WFE",
                       "LLM Model", "Circular Financings", "Debt Financing"])
    EW = load(econ, ["Summary", "AI Revenue", "Annuals", "GPU Rental", "Chips"])
    FW = load(fin, ["Sources Uses", "Project Finance Deals", "IG", "Yield Curves", "Baskets"])
    docs = {}
    M_SRC = "AI Master Model"
    E_SRC = "AI Economics Master"
    F_SRC = "AI Financings"

    # ------------------------------------------------------------------ capex & capacity (Master › Overview)
    ov = MW["Overview"]
    a = ov.find("AI Capex Model")
    yc = cols("C", "K")  # 2022..2030
    assert [str(ov.v(a, c)) for c in yc][:2] == ["2022", "2023"], "Overview header moved"
    yrs = [int(ov.v(a, c)) for c in yc]

    def orow(label, start=a, scale=1.0, nth=1, exact=False):
        return ov.nums(ov.find(label, start, start + 60, cols="B:B", exact=exact, nth=nth), yc, scale)

    nvda = orow("NVDA", exact=True)
    amd = orow("AMD", exact=True)
    merch = orow("Merchant GPU Revenue")
    asic = orow("ASIC Revenue")
    comp = orow("Compute", exact=True)
    hbm = orow("HBM Total")
    hbmc = orow("HBM (co")  # HBM the hyperscalers buy direct for their ASICs (the model spells it "cosignment")
    netw = orow("Networking", exact=True)
    oth = orow("Other (storage, power, cooling)")
    ite = orow("IT Equipment Capex")
    dcx = orow("DC Capex")
    tot = orow("Total AI Capex, $mm")  # the model labels it $mm but the values are $bn
    k = 1e-3
    capex_build = T("capex_build", "AI capex build by component", yrs, [
        R("NVDA", [clean(x * k) if x is not None else None for x in nvda], "bn", ind=1),
        R("AMD", [clean(x * k) if x is not None else None for x in amd], "bn", ind=1),
        R("Merchant GPUs", [clean(x * k) if x is not None else None for x in merch], "bn"),
        R("ASICs", [clean(x * k) if x is not None else None for x in asic], "bn"),
        R("Compute", [clean(x * k) if x is not None else None for x in comp], "bn", b=True),
        R("HBM bought direct (consigned)", [clean(x * k) if x is not None else None for x in hbmc], "bn"),
        R("Networking", [clean(x * k) if x is not None else None for x in netw], "bn"),
        R("Other IT (storage, power, cooling)", [clean(x * k) if x is not None else None for x in oth], "bn"),
        R("IT equipment", [clean(x * k) if x is not None else None for x in ite], "bn", b=True),
        R("Data center (shell, power, cooling)", [clean(x * k) if x is not None else None for x in dcx], "bn"),
        R("Total AI capex", tot, "bn", b=True),
        R("y/y", growth(tot), "pct", ind=1),
        R("HBM inside compute (memo)", [clean(x * k) if x is not None else None for x in hbm], "bn", ind=1),
    ], f"{M_SRC} › Overview (AI Capex Model)", "$bn",
        "Compute = merchant GPUs + ASICs. IT equipment = compute + HBM the hyperscalers buy direct + networking + other IT. "
        "Networking, other IT and DC capex are modeled as attach rates to compute.", 2026)

    hy = orow("Hyperscaler Capex", exact=True)
    sthy = orow("St Hyperscaler Capex", exact=True)
    vs = ov.nums(ov.find("Vs St", ov.find("St Hyperscaler Capex", a, cols="B:B", exact=True), cols="B:B", exact=True), yc)
    neo = orow("Neocloud Capex")
    chn = orow("China Capex", exact=True)
    stchn = orow("St China Capex", exact=True)
    tot2 = orow("Total AI Capex", exact=True)
    spenders = T("spenders", "Who spends it: hyperscalers, neoclouds and China", yrs, [
        R("Hyperscaler capex (SRS)", [clean(x * k) if x is not None else None for x in hy], "bn", b=True),
        R("y/y", growth(hy), "pct", ind=1),
        R("Street hyperscaler capex", [clean(x * k) if x is not None else None for x in sthy], "bn"),
        R("SRS vs Street", vs, "pct", ind=1),
        R("Neocloud capex (NBIS + CRWV)", [clean(x * k) if x is not None else None for x in neo], "bn"),
        R("y/y", growth(neo), "pct", ind=1),
        R("China capex (SRS)", [clean(x * k) if x is not None else None for x in chn], "bn"),
        R("Street China capex", [clean(x * k) if x is not None else None for x in stchn], "bn"),
        R("Total AI capex (spender view)", [clean(x * k) if x is not None else None for x in tot2], "bn", b=True),
        R("y/y", growth(tot2), "pct", ind=1),
    ], f"{M_SRC} › Overview", "$bn", "Hyperscalers = MSFT, META, GOOGL, AMZN, ORCL. The spender view and the component build are separate cuts and do not tie exactly.", 2026)

    g = ov.find("Global AI Compute Capacity, GW")
    gy = cols("D", "K")  # 2023..2030
    gyrs = [int(ov.v(g, c)) for c in gy]
    units = ov.nums(ov.find("Total XPU Units, mm", g, cols="B:B"), gy)
    kw = ov.nums(ov.find("(*) kW/XPU", g, cols="B:B"), gy)
    inc = ov.nums(ov.find("Incremental Global AI Compute Capacity, GW", g, cols="B:B"), gy)
    cum = ov.nums(ov.find("Cumulative AI compute capacity, GW", g, cols="B:B"), gy)
    cum_sa = ov.nums(ov.find("Cumulative Global AI compute, GW (SA)", g, cols="B:B"), gy)
    capacity = T("capacity", "Global AI compute capacity", gyrs, [
        R("XPUs shipped (mm)", units, "num2"),
        R("kW per XPU (all-in)", kw, "num2"),
        R("Incremental GW", inc, "gw", b=True),
        R("Cumulative GW (SRS)", cum, "gw", b=True),
        R("Cumulative GW (SemiAnalysis)", cum_sa, "gw", ind=1),
    ], f"{M_SRC} › Overview", "GW critical IT", "", 2026)

    b = ov.find("AI Capex by GW")
    per = T("capex_per_mw", "Capex per MW of compute deployed", gyrs, [
        R("Compute", ov.nums(ov.find("(*) Compute Rev / MW", b, cols="B:B"), gy), "num1"),
        R("Networking", ov.nums(ov.find("(*) Networking Capex / MW", b, cols="B:B"), gy), "num1"),
        R("Other IT", ov.nums(ov.find("(*) Other IT", b, cols="B:B"), gy), "num1"),
        R("IT equipment", ov.nums(ov.find("(*) IT Equipment Capex / MW", b, cols="B:B"), gy), "num1", b=True),
        R("Data center", ov.nums(ov.find("(*) DC Capex / MW", b, cols="B:B"), gy), "num1"),
        R("All-in AI capex per compute MW", ov.nums(ov.find("AI capex / compute MW", b, cols="B:B"), gy), "num1", b=True),
    ], f"{M_SRC} › Overview (AI Capex by GW)", "$mm per MW", "", 2026)

    # lab capacity and where it is hosted
    lc = ov.find("oAI / Anthropic Compute Capacity")
    labs_gw = T("lab_gw", "OpenAI and Anthropic compute capacity", gyrs, [
        R("OpenAI cumulative GW", ov.nums(ov.find("openAI cumulative capacity", lc, cols="B:B"), gy), "gw"),
        R("Anthropic cumulative GW", ov.nums(ov.find("Anthropic cumulative capacity", lc, cols="B:B"), gy), "gw"),
        R("Combined", ov.nums(ov.find("oAI + anthropic total compute capacity", lc, cols="B:B"), gy), "gw", b=True),
        R("Incremental GW", ov.nums(ov.find("incremental GW", lc, cols="B:B", exact=True), gy), "gw", ind=1),
        R("Share of global incremental GW", ov.nums(ov.find("% total incremental GW", lc, cols="B:B"), gy), "pct", ind=1),
    ], f"{M_SRC} › Overview", "GW", "", 2026)

    hosts = []
    cb = ov.find("Global AI DC Capacity by Customer")
    for lab, tag in [("AWS AI capacity, GW", "AWS"), ("GOOGL AI capacity, GW", "Google"), ("MSFT AI capacity, GW", "Microsoft"),
                     ("META AI capacity, GW", "Meta"), ("ORCL AI capacity, GW", "Oracle"), ("SPCX AI capacity, GW", "SpaceX / xAI")]:
        r = ov.find(lab, cb, cols="B:B")
        row = {"host": tag, "gw": ov.nums(r, gy)}
        for k2, lbl in (("oai", "% oAI"), ("anth", "% Anthropic")):
            try:
                rr = ov.find(lbl, r + 1, r + 2, cols="B:B", exact=True)
                row[k2] = ov.nums(rr, gy)
            except KeyError:
                pass
        hosts.append(row)

    sup = ov.find("Incremental GW By Chip Supplier")
    hy_cols = cols("D", "H")  # 2023..2027
    share = ov.find("% share", sup, cols="B:B")
    chip_share = T("hs_chip_share", "Hyperscaler incremental GW by chip supplier", years(2023, 2027), [
        R(n, ov.nums(ov.find(n, sup, sup + 7, cols="B:B", exact=True), hy_cols), "gw") for n in ("NVDA", "TPU", "AMD", "Trainium", "MTAI", "MAIA")
    ] + [R(f"{n} share", ov.nums(ov.find(n, share, share + 5, cols="B:B", exact=True), hy_cols), "pct", ind=1) for n in ("NVDA", "TPU", "AMD", "Trainium")],
        f"{M_SRC} › Overview (Incremental Hyperscaler Deployments)", "GW", "MSFT, META, AMZN, GOOGL and ORCL deployments by chip.", 2026)

    cpg = ov.find("Capex/GW, $bn")
    capex_gw = T("hs_capex_gw", "Hyperscaler capex per incremental GW", years(2023, 2027), [
        R(n, ov.nums(ov.find(n, cpg, cpg + 7, cols="B:B", exact=True), hy_cols), "num1") for n in ("MSFT", "META", "AMZN", "GOOGL", "ORCL")
    ] + [R("Blended", ov.nums(ov.find("Blended Avg.", cpg, cpg + 8, cols="B:B"), hy_cols), "num1", b=True)],
        f"{M_SRC} › Overview", "$bn per GW", "", 2026)

    docs["capex"] = {"tables": [capex_build, spenders, capacity, per, chip_share, capex_gw, labs_gw],
                     "hosts": {"years": gyrs, "rows": hosts, "src": f"{M_SRC} › Overview (Global AI DC Capacity by Customer)"}}

    # ------------------------------------------------------------------ Street capex revisions (Master › Hyperscaler Capex Revisions)
    rv = MW["Hyperscaler Capex Revisions"]
    snap_cols = cols("E", "W")
    snaps = [rv.text(4, c) for c in snap_cols]  # 3QCY22 ... 1QCY27
    dates = [rv.text(3, c) for c in snap_cols]
    cr = rv.find("Capex Revisions", cols="A:C")
    end = rv.find("Hyperscaler Capex Intensity", cols="A:C")
    series = []
    r = cr
    while r < end:
        hdr = {c: rv.text(r, c) for c in snap_cols}
        labs_ = [h for h in hdr.values() if h.startswith("CY")]
        if labs_ and norm(rv.v(r + 1, "B")) == "msft":
            fy = labs_[0]
            cos = {}
            for rr in range(r + 1, r + 9):
                name = rv.text(rr, "B")
                if name in ("MSFT", "META_US", "GOOGL", "ORCL", "AMZN", "Total"):
                    cos[name.replace("_US", "")] = [clean(rv.num(rr, c) / 1000) if rv.num(rr, c) is not None and hdr[c] else None for c in snap_cols]
            series.append({"fy": fy, "cos": cos})
            r += 8
        r += 1
    # the last snapshot column repeats the current read until that quarter happens; drop exact repeats at the tail
    last = len(snaps)
    while last > 1 and all((s["cos"]["Total"][last - 1] is None or s["cos"]["Total"][last - 1] == s["cos"]["Total"][last - 2]) for s in series):
        last -= 1
    snaps, dates = snaps[:last], dates[:last]
    for s in series:
        for kco in s["cos"]:
            s["cos"][kco] = s["cos"][kco][:last]

    ann = cols("AA", "AR")  # CY2013..CY2030
    ayrs = [int(rv.text(4, c)[2:]) for c in ann]
    keep = [i for i, y in enumerate(ayrs) if y >= 2022]
    ayrs2 = [ayrs[i] for i in keep]

    def arow(label, start, scale=1e-3, f="bn", **kw):
        r_ = rv.find(label, start, start + 12, cols="Y:Y", exact=True)
        vals = rv.nums(r_, ann, scale)
        return R(kw.pop("name", label), [vals[i] for i in keep], f, **kw)

    cap0 = rv.find("Capex", 5, 10, cols="Y:Y", exact=True)
    rev0 = rv.find("Total Revenue", cap0, cols="Y:Y")
    int0 = rv.find("Capex Intensity", cap0, cols="Y:Y")
    fcf0 = rv.find("Free Cash Flow", cap0, cols="Y:Y")
    street_by_co = T("street_by_co", "Street capex, revenue and FCF by hyperscaler", ayrs2,
                     [arow(n, cap0, name=f"{n.replace('_US', '')} capex") for n in ("MSFT", "META_US", "GOOGL", "ORCL", "AMZN")] +
                     [arow("Total", cap0, name="Big-5 capex", b=True)] +
                     [R("y/y", [rv.nums(rv.find("yy growth", cap0, cap0 + 10, cols="Y:Y", exact=True), ann)[i] for i in keep], "pct", ind=1)] +
                     [arow(n, int0, scale=1, f="pct", name=f"{n.replace('_US', '')} capex / revenue", ind=1) for n in ("MSFT", "META_US", "GOOGL", "ORCL", "AMZN")] +
                     [arow("Average", int0, scale=1, f="pct", name="Big-5 capex / revenue", b=True)] +
                     [arow("Total", fcf0, name="Big-5 free cash flow", b=True)] +
                     [arow("% rev", fcf0, scale=1, f="pct", name="FCF margin", ind=1)],
                     f"{M_SRC} › Hyperscaler Capex Revisions (Street consensus)", "$bn", "", 2026)

    srs0 = rv.find("SRS Estimates and Implieds", cols="Y:Y")

    def srow(label, scale=1e-3, f="bn", **kw):
        r_ = rv.find(label, srs0, srs0 + 25, cols="Y:Y", exact=True)
        vals = rv.nums(r_, ann, scale)
        return R(kw.pop("name", label), [vals[i] for i in keep], f, **kw)

    nv = rv.find("NVDA Stock Price", srs0, cols="Y:Y")
    vs_street = T("srs_vs_street", "SRS vs Street: hyperscaler capex, FCF and what it means for NVDA", ayrs2, [
        srow("Hyperscaler Capex (St)", name="Street Big-5 capex"),
        srow("Hyperscaler Capex (SRS)", name="SRS Big-5 capex", b=True),
        R("SRS vs Street", [rv.nums(rv.find("vs St", srs0, srs0 + 10, cols="Y:Y", exact=True), ann)[i] for i in keep], "pct", ind=1),
        srow("FCF on St Capex", name="FCF on Street capex"),
        srow("Implied FCF on SRS Capex", name="FCF on SRS capex", b=True),
        R("NVDA EPS, Street", [rv.nums(rv.find("NVDA St EPS", nv, cols="Y:Y"), ann)[i] for i in keep], "usd2"),
        R("NVDA EPS on Street capex", [rv.nums(rv.find("NVDA EPS on St Capex", nv, cols="Y:Y"), ann)[i] for i in keep], "usd2"),
        R("NVDA EPS on SRS capex", [rv.nums(rv.find("NVDA EPS on SRS Capex", nv, cols="Y:Y"), ann)[i] for i in keep], "usd2", b=True),
        R("Implied P/E on SRS EPS", [rv.nums(rv.find("Implied PE", rv.find("NVDA EPS on SRS Capex", nv, cols="Y:Y"), cols="Y:Y", exact=True), ann)[i] for i in keep], "x", ind=1),
    ], f"{M_SRC} › Hyperscaler Capex Revisions (SRS Estimates and Implieds)", "$bn",
        f"NVDA price used: ${rv.num(nv, ann[keep[1]]) or rv.num(nv, 'AL') or ''}".rstrip("$ "), 2026)
    nv_px = None
    for c in ann:
        if rv.num(nv, c):
            nv_px = rv.num(nv, c)
            break
    vs_street["note"] = f"NVDA share price in the model: ${nv_px:,.0f}." if nv_px else ""
    docs["revisions"] = {"snapshots": snaps, "dates": dates, "series": series, "tables": [vs_street, street_by_co],
                         "src": f"{M_SRC} › Hyperscaler Capex Revisions (consensus capex at each quarter-end)"}

    # ------------------------------------------------------------------ compute share (Master › XPU Model)
    xp = MW["XPU Model"]
    h = xp.find("XPU Units", cols="D:D", exact=True)
    xc = cols("G", "N")  # CY2023..CY2030
    xyrs = [int(xp.text(h, c)[2:]) for c in xc]

    def xrow(label, start, scale=1.0, f="num", **kw):
        r_ = xp.find(label, start, start + 30, cols="D:D", exact=True)
        return R(kw.pop("name", label), xp.nums(r_, xc, scale), f, **kw)

    u0, rv0 = h, xp.find("XPU Revenue", cols="D:D", exact=True)
    g0, rg0 = xp.find("XPU GW", cols="D:D", exact=True), xp.find("XPU Rev/GW", cols="D:D", exact=True)
    vendors = [("NVDA", "NVDA Units", "NVDA DC Compute Revenue", "NVDA GW", "NVDA"), ("AMD", "AMD Units", "AMD GPU Revenue, $mm", "AMD GW", "AMD"),
               ("Google TPU", "TPU", "TPU Revenue, $mm", "TPU GW", "TPU"), ("AWS Trainium", "Trainium", "Trainium Revenue, $mm", "Trainium GW", "Trainium"),
               ("OpenAI ASIC", "oAI", "oAI Revenue, $mm", "oAI GW", "oAI"), ("Other ASICs", "Other", "Other ASICs Revenue, $mm", "Other ASICs GW", "Other ASICs")]

    def find_prefix(start, label):
        return xp.find(label, start, start + 30, cols="D:D")

    rev_rows, gw_rows, unit_rows, rpg_rows = [], [], [], []
    for name, ul, rl, gl, pl in vendors:
        unit_rows.append(R(name, xp.nums(xp.find(ul, u0, u0 + 20, cols="D:D", exact=True), xc, 1e-6), "num2"))
        rev_rows.append(R(name, xp.nums(find_prefix(rv0, rl), xc, 1e-3), "bn"))
        gw_rows.append(R(name, xp.nums(xp.find(gl, g0, g0 + 30, cols="D:D", exact=True), xc), "gw"))
        rpg_rows.append(R(name, xp.nums(xp.find(pl, rg0, rg0 + 20, cols="D:D", exact=True), xc), "num1"))
    tot_rev = xp.nums(xp.find("Total XPU Revenue, $mm", rv0, cols="D:D"), xc, 1e-3)
    tot_gw = xp.nums(xp.find("Total XPU GW", g0, cols="D:D"), xc)
    tot_u = xp.nums(xp.find("Total XPU Units", u0, cols="D:D"), xc, 1e-6)
    merch_gw = xp.nums(xp.find("Merchant GW", g0, cols="D:D", exact=True), xc)
    asic_gw = xp.nums(xp.find("ASIC GW", g0, cols="D:D", exact=True), xc)
    xpu_rev = T("xpu_rev", "Accelerator (XPU) revenue by vendor", xyrs, rev_rows + [
        R("Total XPU revenue", tot_rev, "bn", b=True), R("y/y", growth(tot_rev), "pct", ind=1),
        R("ASIC share of revenue", xp.nums(xp.find("% revenue share", xp.find("ASIC Revenue, $mm", rv0, cols="D:D"), cols="D:D", exact=True), xc), "pct", ind=1),
    ], f"{M_SRC} › XPU Model", "$bn", "", 2026)
    xpu_gw = T("xpu_gw", "GW deployed by accelerator vendor", xyrs, gw_rows + [
        R("Total XPU GW", tot_gw, "gw", b=True),
        R("Merchant (NVDA + AMD) share", [None if m is None or t in (None, 0) else clean(m / t) for m, t in zip(merch_gw, tot_gw)], "pct", ind=1),
        R("ASIC share", [None if m is None or t in (None, 0) else clean(m / t) for m, t in zip(asic_gw, tot_gw)], "pct", ind=1),
    ], f"{M_SRC} › XPU Model", "GW", "", 2026)
    xpu_units = T("xpu_units", "Accelerator units by vendor", xyrs, unit_rows + [R("Total XPUs", tot_u, "num2", b=True), R("y/y", growth(tot_u), "pct", ind=1)],
                  f"{M_SRC} › XPU Model", "mm units", "", 2026)
    xpu_rpg = T("xpu_rpg", "Accelerator revenue per GW", xyrs, rpg_rows + [R("Blended", xp.nums(xp.find("Blended Rev / GW", rg0, cols="D:D"), xc), "num1", b=True)],
                f"{M_SRC} › XPU Model", "$bn per GW", "Merchant revenue per GW is ~2-3x ASIC revenue per GW: a GW that moves to ASICs is worth less to the chip vendor.", 2026)
    upd = xp.text(xp.find("Updated", cols="D:D"), "D")
    docs["compute"] = {"tables": [xpu_rev, xpu_gw, xpu_units, xpu_rpg], "updated": upd.replace("Updated:", "").strip()}

    # ------------------------------------------------------------------ AI economics (Econ › Summary, AI Revenue, Annuals, GPU Rental)
    sm = EW["Summary"]
    ec = cols("F", "L")  # 2024..2030
    eyrs = [int(sm.v(2, c)) for c in ec]

    def er(label, start=1, f="num1", nth=1, exact=False, scale=1.0, **kw):
        r_ = sm.find(label, start, cols="B:B", exact=exact, nth=nth)
        return R(kw.pop("name", label), sm.nums(r_, ec, scale), f, **kw)

    ind0 = sm.find("Industry (compute GW)", cols="B:B")
    buyer = sm.find("GPU Buyer", cols="B:B")
    prov = sm.find("Model Provider", cols="B:B")
    user = sm.find("End User", cols="B:B")
    hw = T("econ_hw", "Hardware layer: industry AI capex and GW", eyrs, [
        er("AI capex, $bn", ind0, "bn", name="Industry AI capex", b=True),
        er("( / ) GW deployed, GW CITL", ind0, "gw", name="Compute GW deployed"),
        er("Cumulative compute GW", ind0, "gw", name="Cumulative compute GW"),
        er("Industry capex / compute GW", ind0, "num1", name="Capex per compute GW ($bn)"),
        er("Capex, $bn", sm.find("ASICs (compute GW)", cols="B:B"), "bn", name="ASIC capex", ind=1),
        er("Capex, $bn", sm.find("Merchant (compute GW)", cols="B:B"), "bn", name="Merchant GPU capex", ind=1),
    ], f"{E_SRC} › Summary (Hardware)", "$bn", "", 2026)
    gpu = T("econ_buyer", "GPU buyer: what a GW of rented GPUs earns", eyrs, [
        er("Rev / GW, $bn (rental price)", buyer, "num1", name="Rental revenue per GW ($bn/yr)", b=True),
        er("Annualized capex / GW, $bn", buyer, "num1", name="Depreciation per GW ($bn/yr)"),
        er("Operating cost / GW, $bn", buyer, "num2", name="Operating cost per GW ($bn/yr)"),
        er("% margin", sm.find("Gross profit / GW", buyer, cols="B:B"), "pct", name="Gross margin"),
        er("% margin", sm.find("EBIT / GW", buyer, cols="B:B"), "pct", name="EBIT margin"),
        er("FCF / GW", buyer, "num1", name="Unlevered FCF per GW ($bn/yr)"),
        er("IRR", buyer, "pct", name="Unlevered IRR by vintage", b=True),
        er("Average payback years", buyer, "num1", name="Payback (years)"),
    ], f"{E_SRC} › Summary (GPU Buyer)", "", "Each column is a vintage: GPUs bought that year at that year's mix and rental price, 6-year life, all-equity.", 2026)

    # rental pricing by GPU generation ($/GPU-hr)
    p0 = sm.find("Chip SKU", buyer, cols="B:B")
    pc = cols("D", "L")
    skus = [sm.text(p0, c) for c in pc]
    pricing = T("rental_pricing", "Rental pricing by GPU generation", skus, [
        R("All-in server power per GPU (W)", sm.nums(sm.find("All in server TDP, W", p0, cols="B:B"), pc), "int"),
        R("Spot", sm.nums(sm.find("Spot pricing", p0, cols="B:B"), pc), "usd2"),
        R("Under 1 year", sm.nums(sm.find("<1y", p0, cols="B:B", exact=True), pc), "usd2"),
        R("18 months to 2 years", sm.nums(sm.find("18m-2y", p0, cols="B:B", exact=True), pc), "usd2"),
        R("3 years", sm.nums(sm.find("3y", p0, cols="B:B", exact=True), pc), "usd2"),
        R("4-5 years", sm.nums(sm.find("4-5y", p0, cols="B:B", exact=True), pc), "usd2"),
        R("Blended", sm.nums(sm.find("Blended pricing, $/hr/GPU", p0, cols="B:B"), pc), "usd2", b=True),
        R("Model assumption (life-of-asset average)", sm.nums(sm.find("Active pricing", p0, cols="B:B"), pc), "usd2", b=True),
        R("Revenue per GW per year ($bn)", sm.nums(sm.find("Pricing, $bn/GW/yr by gen", p0, cols="B:B"), pc), "num1"),
    ], f"{E_SRC} › Summary (Rental rev by gen)", "$ per GPU-hour", "Duration curve: 4-5yr ~5% below 3yr, 3yr ~9% below 18m-2yr, which is ~8% below <1yr; <1yr ~12% below spot.")

    mp = T("econ_provider", "Model providers: OpenAI + Anthropic (combined)", eyrs, [
        er("ARR, $bn", prov, "bn", name="ARR, year-end", b=True),
        er("NNARR, $bn", prov, "bn", name="Net new ARR"),
        er("Revenue, $bn", prov, "bn", name="Revenue", b=True),
        er("yy growth", sm.find("Revenue, $bn", prov, cols="B:B"), "pct", name="y/y", ind=1),
        er("% GM", sm.find("Inference COGS, $bn", prov, cols="B:B"), "pct", name="Inference gross margin"),
        er("Training opex, $bn", prov, "bn", name="Training compute"),
        er("% rev", sm.find("Total compute cost, $bn", prov, cols="B:B"), "pct", name="Total compute cost / revenue"),
        er("EBIT, $bn", prov, "bn", name="EBIT", b=True),
        er("% rev", sm.find("EBIT, $bn", prov, cols="B:B"), "pct", name="EBIT margin", ind=1),
        er("Hyperscaler capacity, GW", prov, "gw", name="Industry capacity at hyperscalers (GW)"),
        er("Neocloud capacity, GW", prov, "gw", name="Industry capacity at neoclouds (GW)"),
        er("% industry rental compute", prov, "pct", name="oAI + Anthropic share of rented compute"),
    ], f"{E_SRC} › Summary (Model Provider)", "$bn", "", 2026)
    eu = T("econ_user", "End users: tokens and what they cost", eyrs, [
        er("Cumulative inference industry", user, "int", name="Industry inference tokens per year (quadrillion)"),
        er("Blended cost $ / 1mm tokens", user, "usd2", name="Blended cost per 1M tokens ($)", b=True),
        er("Implied rev $ / 1mm tokens", user, "usd2", name="Implied price per 1M tokens ($)"),
        er("Implied model layer revenue", user, "bn", name="Implied model-layer revenue ($bn)", b=True),
        er("oAI + Anthropic rev, $bn", user, "bn", name="OpenAI + Anthropic revenue ($bn)"),
        er("oAI + anthropic % industry", user, "pct", name="Their share of industry revenue", ind=1),
    ], f"{E_SRC} › Summary (End User)", "", "Token costs fall to ~1/3 from 2026 to 2030 as Rubin/Feynman fleets replace Blackwell.", 2026)

    # AI revenue by company, no double counting ($mm -> $bn)
    an = EW["Annuals"]
    a0 = an.find("AI REVENUE NO DOUBLE", cols="A:A")
    acols = cols("D", "K")  # 2023..2030
    arev = []
    for n, lbl in [("OPEN AI", "OpenAI"), ("Anthropic", "Anthropic"), ("AMZN", "AWS Bedrock (3P models)"), ("GOOGL", "Google (Gemini Enterprise / agent platform)"),
                   ("MSFT", "Microsoft Foundry"), ("Coding Apps", "Coding apps (Cursor, Replit, …)"), ("OTHERS", "Other model hosts")]:
        arev.append(R(lbl, an.nums(an.find(n, a0, a0 + 10, cols="B:B", exact=True), acols, 1e-3), "bn"))
    totv = [clean(sum(x for x in col if x is not None)) if any(x is not None for x in col) else None for col in zip(*[r_["v"] for r_ in arev])]
    ai_rev = T("ai_revenue", "AI revenue by company (no double counting)", [int(an.v(a0, c)) for c in acols], arev + [R("Total", totv, "bn", b=True), R("y/y", growth(totv), "pct", ind=1)],
               f"{E_SRC} › Annuals", "$bn", "Model-layer and platform revenue; hyperscaler rental of GPUs to the labs is excluded so nothing is counted twice.", 2026)

    ar = EW["AI Revenue"]
    arc = cols("D", "J")  # 2024..2030
    hyp = []
    for lbl, name in [("AMZN AI Revenue", "Amazon AI revenue"), ("MSFT AI Revenue", "Microsoft AI revenue"), ("GOOGL AI Revenue", "Google AI revenue"),
                      ("Hyperscaler 1P revenu", "of which first-party models/apps")]:
        hyp.append(R(name, ar.nums(ar.find(lbl, cols="B:B"), arc), "bn", b=name.endswith("revenue") and not name.startswith("of")))
    hyper_ai = T("hyperscaler_ai_rev", "Hyperscaler AI revenue (rental + platform + first-party)", years(2024, 2030), hyp,
                 f"{E_SRC} › AI Revenue", "$bn", "", 2026)
    fr = ar.find("AI revenue implied by", cols="B:B")
    fleet = T("fleet_return", "Does the fleet pay back? Revenue implied by the deployed fleet vs capex", years(2024, 2030), [
        R("Merchant-compute capex", [None if x is None else clean(-x) for x in ar.nums(ar.find("Capex", fr, fr + 10, cols="B:B", exact=True), arc)], "bn"),
        R("AI revenue implied by the fleet", ar.nums(fr, arc), "bn", b=True),
        R("FCF from the fleet", ar.nums(ar.find("FCF", fr, cols="B:B", exact=True), arc), "bn"),
        R("FCF less capex", ar.nums(ar.find("FCF - capex", fr, cols="B:B"), arc), "bn", b=True),
    ], f"{E_SRC} › AI Revenue", "$bn", "", 2026)
    irr_r = ar.find("IRR", fr, cols="B:B", exact=True)
    fleet_irr = next((ar.num(irr_r, c) for c in range(3, 30) if ar.num(irr_r, c) is not None), None)
    fleet["note"] = (f"IRR on the 2024-2030 fleet, with each vintage earning for six years: {fleet_irr:.1%}." if fleet_irr is not None else "")

    # contracted compute deals (Econ › GPU Rental)
    gr = EW["GPU Rental"]
    name_r = 1
    lab_col = next(c for c in range(CI("P"), CI("W")) if any(norm(gr.text(r_, c)) == "contract value" for r_ in range(1, 8)))
    dcols = [c for c in range(lab_col + 2, lab_col + 30) if gr.text(name_r, c)]
    lab = {norm(gr.text(r_, lab_col)): r_ for r_ in range(1, 30) if gr.text(r_, lab_col)}

    def dval(key, c):
        r_ = lab.get(norm(key))
        if not r_:
            return None
        x = gr.v(r_, c)
        if isinstance(x, (int, float)):
            return clean(x)
        return gr.text(r_, c) or None

    deals = []
    for c in dcols:
        deals.append({
            "deal": gr.text(name_r, c), "date": gr.text(lab.get("announcement date", 2), c)[:10],
            "value_bn": (lambda v: clean(v / 1e9) if isinstance(v, (int, float)) else v)(dval("Contract Value", c)),
            "years": dval("Term Duration (Years)", c),
            "annual_bn": (lambda v: clean(v / 1e9) if isinstance(v, (int, float)) else v)(dval("Implied Annual Revenue", c)),
            "chip": dval("Chip Type", c), "mw": dval("Critical IT Power Consumption", c) or gr.text(7, c),
            "gpus": dval("Implied # of GPUs", c), "rev_mw": (lambda v: clean(v / 1e6) if isinstance(v, (int, float)) else v)(dval("Deal Revenue per MW per Year", c)),
            "gpu_hr": dval("Implied per Logical GPU-Hour Revenue", c), "prepay": dval("Prepay %", c),
            "irr": dval("Project IRR % over Depreciation Schedule", c), "ebitda": dval("EBITDA Margin", c),
        })
    # a few labels carry footnote digits or differ between versions; match those by prefix
    for d, c in zip(deals, dcols):
        for k3, pref in (("mw", "critical it power"), ("rev_mw", "deal revenue per mw"), ("gpu_hr", "implied per logical gpu"), ("irr", "project irr"), ("ebitda", "ebitda margin")):
            if d.get(k3) in (None, ""):
                r_ = next((rr for kk, rr in lab.items() if kk.startswith(pref)), None)
                if r_:
                    x = gr.v(r_, c)
                    d[k3] = clean(x / 1e6) if (k3 == "rev_mw" and isinstance(x, (int, float))) else (clean(x) if isinstance(x, (int, float)) else gr.text(r_, c) or None)
    for d in deals:
        d["deal"] = re.sub(r"(Deal \d)\d$", r"\1", re.sub(r"(?<=[A-Za-z])\d+$", "", d["deal"]))  # strip footnote digits
        for k3 in ("value_bn", "years", "annual_bn", "mw", "gpus", "rev_mw", "gpu_hr", "prepay", "irr", "ebitda"):
            if isinstance(d.get(k3), str):
                try:
                    d[k3] = clean(float(d[k3].replace(",", "")))
                except ValueError:
                    pass  # combined two-phase values stay as text, e.g. "30.0%/27.1%"
    docs["econ"] = {"tables": [hw, gpu, pricing, mp, eu, ai_rev, hyper_ai, fleet], "deals": deals,
                    "deals_src": f"{E_SRC} › GPU Rental (deal economics)"}

    # ------------------------------------------------------------------ labs (Master › LLM Model)
    ll = MW["LLM Model"]

    def monthly(header_label, row_label):
        h_ = ll.find(header_label, cols="B:B")
        r_ = ll.find(row_label, h_, h_ + 15, cols="B:B", exact=True)
        pts = []
        for c in range(3, 40):
            d_ = ll.v(h_, c)
            x = ll.num(r_, c)
            if isinstance(d_, (dt.datetime, dt.date)) and x is not None:
                pts.append([d_.strftime("%Y-%m-%d"), clean(x / 1000)])
        return pts

    arr = {"OpenAI": monthly("oAI Monthly Metrics", "ARR, $mm"), "Anthropic": monthly("Anthropic Monthly Metrics", "ARR, $mm")}
    # OpenAI revenue projections by vintage (The Information) and Anthropic revision history
    proj = []
    for lbl in ("Fall 2024 Projection", "Winter 2025 Projection", "Summer 2025 Projection", "Winter 2026 Projection"):
        try:
            r_ = ll.find(lbl, cols="B:B")
        except KeyError:
            continue
        tr = ll.find("Total Revenue", r_, r_ + 10, cols="B:B", exact=True)
        proj.append(R(ll.text(r_, "B"), ll.nums(tr, cols("C", "J")), "bn"))
    oai_proj = T("oai_projections", "OpenAI revenue projections, by vintage", years(2023, 2030), proj,
                 f"{M_SRC} › LLM Model (The Information projections)", "$bn")
    ar0 = ll.find("Anthropic Rev revisions", ll.find("Anthropic Rev revisions", cols="B:B") + 1, cols="B:B")
    hdr = [ll.text(ar0, c) for c in cols("C", "E")]
    an_rows = []
    for rr in range(ar0 + 1, ar0 + 8):
        y_ = ll.text(rr, "B")
        if re.match(r"^20\d\d$", y_):
            an_rows.append([int(y_)] + [None if ll.num(rr, c) is None else clean(ll.num(rr, c) / 1000) for c in cols("C", "E")])
    anth_rev = {"dates": hdr, "rows": an_rows, "src": f"{M_SRC} › LLM Model (Anthropic revenue revisions)"}

    c0 = ll.find("Total oAI Commitments", cols="B:B")
    com_cols = cols("F", "K")  # 2026..2031
    com = []
    for rr in range(c0 + 1, c0 + 12):
        nm = ll.text(rr, "B")
        if not nm or nm.lower().startswith("total"):
            if nm.lower().startswith("total"):
                tot_c = ll.num(rr, "M")
            break
        com.append({"who": nm, "how": ll.text(rr, "C"), "y": [None if ll.num(rr, c) is None else clean(ll.num(rr, c)) for c in com_cols], "total": clean(ll.num(rr, "M") or 0)})
    gw0 = ll.find("oAI Announced GW Deploy", cols="B:B")
    gwr = []
    for rr in range(gw0 + 3, gw0 + 12):
        nm = ll.text(rr, "B")
        if not nm:
            continue
        if nm.lower().startswith("incremental"):
            break
        gwr.append({"who": nm, "how": ll.text(rr, "C"), "y": [None if ll.num(rr, c) is None else clean(ll.num(rr, c)) for c in com_cols], "total": clean(ll.num(rr, "M") or 0)})
    su0 = ll.find("oAI Sources and Uses", cols="B:B")
    srcs, uses = [], []
    s1 = ll.find("Sources, $bn", su0, cols="B:B")
    u1 = ll.find("Uses, $bn", su0, cols="B:B")
    for rr in range(s1 + 1, u1):
        nm = ll.text(rr, "B")
        if nm and not nm.lower().startswith("total"):
            srcs.append({"item": nm, "date": ll.text(rr, "E"), "bn": clean(ll.num(rr, "F") or 0), "val": ll.num(rr, "H"), "who": ll.text(rr, "I")})
    gap = None
    for rr in range(u1 + 1, u1 + 14):
        nm = ll.text(rr, "B")
        if nm.lower().startswith("sources - uses"):
            gap = ll.num(rr, "F")
            break
        if nm and not nm.lower().startswith("total"):
            uses.append({"item": nm, "bn": clean(ll.num(rr, "F") or 0)})
    cash0 = ll.find("oAI Cash, $mm", cols="B:B")
    cash = T("oai_cash", "OpenAI cash runway (model)", years(2024, 2031), [
        R(ll.text(rr, "B"), ll.nums(rr, cols("D", "K")), "bn", b=ll.text(rr, "B").startswith("Cash EoP"))
        for rr in range(cash0 + 1, cash0 + 8) if ll.text(rr, "B")
    ], f"{M_SRC} › LLM Model", "$bn", "", 2026)
    # Anthropic planned GW by deal and the Sep-26 P&L
    pg0 = ll.find("Anthropic planned GW", cols="B:B")
    pg_map = [(c, int(ll.num(pg0, c))) for c in range(3, 16) if ll.num(pg0, c) and 2020 < ll.num(pg0, c) < 2040]
    pg_cols = [c for c, _ in pg_map]
    plan = []
    for rr in range(pg0 + 1, pg0 + 13):
        nm = ll.text(rr, "B")
        if not nm:
            continue
        plan.append(R(nm, ll.nums(rr, pg_cols), "gw", b=nm.lower().startswith(("total", "cumulative")), ind=0 if nm.lower().endswith("total") or nm.lower().startswith(("total", "cumulative", "target")) else 1))
    anth_gw = T("anth_gw", "Anthropic planned compute by deal", [y_ for _, y_ in pg_map], plan, f"{M_SRC} › LLM Model", "GW")
    pl0 = ll.find("Anthropic PnL, $mm", cols="B:B")
    sep = ll.find("Sep26", pl0, cols="B:B")
    pcols = cols("C", "I")  # 2023..2029
    pl_rows = []
    for lbl, nm, f in [("Revenue, $mm", "Revenue", "bn"), ("yy growth", "y/y", "pct"), ("Gross Profit", "Gross profit", "bn"), ("% rev", "Gross margin", "pct"),
                       ("Training Compute Cost", "Training compute", "bn"), ("Total Opex", "Total opex", "bn"), ("Adj. EBITDA / Operating", "Adj. EBITDA / operating profit", "bn"),
                       ("FCF", "FCF", "bn")]:
        try:
            rr = ll.find(lbl, sep, sep + 30, cols="B:B")
        except KeyError:
            continue
        vals = ll.nums(rr, pcols, 1e-3 if f == "bn" else 1)
        pl_rows.append(R(nm, vals, f, b=nm in ("Revenue", "Adj. EBITDA / operating profit"), ind=1 if f == "pct" else 0))
    anth_pl = T("anth_pl", "Anthropic P&L (model, Sep-26 version)", years(2023, 2029), pl_rows, f"{M_SRC} › LLM Model", "$bn", "", 2026)
    oai0 = ll.find("oAI PnL, $mm", cols="B:B")
    ocols = cols("C", "J")  # 2023..2030
    o_rows = []
    for lbl, nm, f in [("Revenue, $mm", "Revenue", "bn"), ("yy growth", "y/y", "pct"), ("Gross Profit", "Gross profit", "bn"), ("% rev", "Gross margin", "pct"),
                       ("Training compute cost", "Training compute", "bn"), ("Adj. EBITDA", "Adj. EBITDA", "bn"), ("(-) Capex", "Capex (self-build)", "bn"), ("FCF", "FCF", "bn")]:
        try:
            rr = ll.find(lbl, oai0, oai0 + 45, cols="B:B")
        except KeyError:
            continue
        vals = ll.nums(rr, ocols, 1e-3 if f == "bn" else 1)
        if lbl == "(-) Capex":
            vals = [None if x is None else -x for x in vals]
        o_rows.append(R(nm, vals, f, b=nm in ("Revenue", "FCF"), ind=1 if f == "pct" else 0))
    oai_pl = T("oai_pl", "OpenAI P&L (model, Feb-26 guide basis)", years(2023, 2030), o_rows, f"{M_SRC} › LLM Model", "$bn", "", 2026)
    docs["labs"] = {"arr": arr, "arr_src": f"{M_SRC} › LLM Model (monthly ARR; later months are the model's path, not reported)",
                    "tables": [oai_pl, anth_pl, oai_proj, cash, anth_gw], "anth_rev": anth_rev,
                    "commitments": {"rows": com, "years": years(2026, 2031), "src": f"{M_SRC} › LLM Model (total OpenAI commitments)"},
                    "oai_gw": {"rows": gwr, "years": years(2026, 2031)},
                    "sources_uses": {"sources": srcs, "uses": uses, "gap": gap, "src": f"{M_SRC} › LLM Model (OpenAI sources and uses)"}}

    # circular financings (Master)
    cf = MW["Circular Financings"]

    def deal_table(anchor):
        h_ = cf.find("Company", cf.find(anchor, cols="B:B"), cols="B:B", exact=True)
        out = []
        for rr in range(h_ + 1, h_ + 60):
            co = cf.text(rr, "B")
            if not co or co.lower() == "sources":
                if not co and not cf.text(rr, "H"):
                    break
                if co.lower() == "sources":
                    break
                continue
            out.append({"from": co, "to": cf.text(rr, "C"), "eco": cf.text(rr, "D"), "date": cf.text(rr, "E")[:10], "type": cf.text(rr, "F"),
                        "bn": clean(cf.num(rr, "G")) if cf.num(rr, "G") is not None else None, "deal": cf.text(rr, "H")})
        return out

    mega = deal_table("Mega Deal Circular Financ")
    s_ = cf.find("Sources", cols="B:B", exact=True)
    u_ = cf.find("Uses", s_, cols="B:B", exact=True)
    circ_src = [{"who": cf.text(rr, "B"), "bn": clean(cf.num(rr, "G") or 0)} for rr in range(s_ + 1, u_) if cf.text(rr, "B") and cf.text(rr, "B") != "Total"]
    circ_use = [{"who": cf.text(rr, "B"), "bn": clean(cf.num(rr, "G") or 0)} for rr in range(u_ + 1, u_ + 8) if cf.text(rr, "B") and cf.text(rr, "B") != "Total"]
    supply_chain = deal_table("Supply Chain Financings")
    df = MW["Debt Financing"]
    h_ = df.find("Hyperscaler", cols="B:B", exact=True)
    debt = []
    for rr in range(h_ + 1, h_ + 8):
        if df.text(rr, "B"):
            debt.append({"who": df.text(rr, "B"), "investors": df.text(rr, "C"), "date": df.text(rr, "D")[:10], "bn": clean(df.num(rr, "E") or 0),
                         "pricing": df.text(rr, "F"), "structure": df.text(rr, "G"), "notes": df.text(rr, "H")})

    # ------------------------------------------------------------------ financing (Financings model)
    su = FW["Sources Uses"]
    fc = cols("L", "R")  # CY2023..CY2029
    fyrs = [int(su.text(8, c)[2:]) for c in fc]

    def fr_(label, start=1, f="bn", nth=1, exact=False, **kw):
        r_ = su.find(label, start, cols="D:D", exact=exact, nth=nth)
        return R(kw.pop("name", label), su.nums(r_, fc), f, **kw)

    hs = su.find("Hyperscaler Sources", cols="D:D")
    tm = su.find("Total Market Sources", cols="D:D")
    tu = su.find("Total Market Uses", cols="D:D")
    hm = su.find("Hyperscaler Metrics", cols="D:D")
    hyper_su = T("hyper_su", "Hyperscaler sources and uses of cash for AI", fyrs, [
        fr_("CFO, $bn", hs, name="Operating cash flow applied to AI capex"),
        fr_("Public debt issuances", hs, name="Public (IG) debt issued"),
        fr_("Project financing, $bn", hs, name="Project financing"),
        fr_("Equity Issuances, $bn", hs, name="Equity issued"),
        fr_("Sources, $bn", hs, name="Total sources", b=True),
        fr_("Hyperscaler AI capex", hs, name="Hyperscaler AI capex (use)", b=True),
        fr_("Shortfall, $bn", hs, name="Sources minus uses", b=True),
        fr_("WACC", hs, "pct", name="Blended cost of capital", ind=1),
        fr_("Hyperscaler Leverage", hs, "x", name="Gross debt / EBITDA"),
        fr_("Hyperscaler Leverage", hs, "x", nth=2, name="Gross debt + leases / EBITDA"),
    ], f"{F_SRC} › Sources Uses (case: SRS hyperscaler capex)", "$bn", "Negative = AI capex the hyperscalers cannot fund from cash flow and the debt the model assumes.", 2026)
    market_su = T("market_su", "Whole market: sources of AI funding vs AI capex", fyrs, [
        fr_("Hyperscaler CFO used", tm, name="Hyperscaler cash flow"),
        fr_("AI-related Public Cre", tm, name="AI-related public credit (IG + HY)"),
        fr_("Equity/convert/pref", tm, name="Equity, converts and preferred"),
        fr_("Project Financing, $bn", tm, name="Project financing"),
        fr_("Private credit", tm, exact=True, name="Private credit"),
        fr_("Total Sources, $bn", tm, name="Total sources", b=True),
        fr_("Total Uses, $bn", tu, name="Total AI capex (uses)", b=True),
        fr_("Hyperscaler AI capex", tu, name="Hyperscaler AI capex", ind=1),
        fr_("Neocloud/other capex", tu, name="Neocloud and other AI capex", ind=1),
        fr_("Market Shortfall, $bn", tm, name="Sources minus uses", b=True),
        fr_("Incremental GW deploy", tu, "gw", name="Incremental GW deployed"),
        fr_("(*) $bn / GW", tu, "num1", name="Capex per GW ($bn)"),
    ], f"{F_SRC} › Sources Uses", "$bn", "", 2026)
    wfe = T("ai_wfe", "AI capex pulls through to wafer fab equipment", fyrs, [
        fr_("AI WFE, $bn", tu, name="AI WFE"), fr_("% total WFE", tu, "pct", name="AI share of WFE", ind=1),
        fr_("non-AI WFE, $bn", tu, name="Non-AI WFE"), fr_("WFE, $bn", tu, exact=True, name="Total WFE", b=True),
        fr_("yy growth", su.find("WFE, $bn", tu, cols="D:D", exact=True), "pct", name="y/y", ind=1),
    ], f"{F_SRC} › Sources Uses", "$bn", "", 2026)

    def co_rows(anchor, scale, f, **kw):
        r_ = su.find(anchor, hm, cols="D:D")
        out = []
        for rr in range(r_ + 1, r_ + 8):
            nm = su.text(rr, "D") or su.text(rr, "C")
            nm = nm.replace("META_US", "META")
            if not nm or nm.lower().startswith(("total", "blended")):
                if nm.lower().startswith(("total", "blended")):
                    out.append(R(kw.get("total", nm), su.nums(rr, fc, scale), f, b=True))
                break
            out.append(R(nm, su.nums(rr, fc, scale), f))
        return out

    lev = T("leverage", "Hyperscaler leverage: gross debt / EBITDA", fyrs, co_rows("Gross Debt / EBITDA", 1, "x", total="Blended"),
            f"{F_SRC} › Sources Uses (Hyperscaler Metrics)", "x", "", 2026)
    ai_capex_co = T("ai_capex_co", "Hyperscaler AI capex by company (SRS case)", fyrs, co_rows("Total Hyperscaler AI", 1e-3, "bn", total="Total"),
                    f"{F_SRC} › Sources Uses (Hyperscaler Metrics)", "$bn", "", 2026)

    ig = FW["IG"]
    t_ = ig.find("Total", cols="C:C", exact=True)
    igy = [int(ig.num(3, c)) for c in cols("D", "G")]
    igt = T("ig_share", "Hyperscalers in the investment-grade bond market", [str(y) for y in igy[:-1]] + [f"{igy[-1]} YTD"], [
        R("All IG issuance ($bn)", ig.nums(t_, cols("D", "G")), "bn"),
        R("Hyperscaler IG issuance ($bn)", ig.nums(t_, cols("J", "M")), "bn", b=True),
        R("Other AI issuers ($bn)", ig.nums(t_, cols("P", "S")), "bn"),
        R("Hyperscaler share of IG", ig.nums(ig.find("% hypers", t_, cols="C:C", exact=True), cols("D", "G")), "pct", b=True),
        R("AI share of IG", ig.nums(ig.find("% AI", t_, cols="C:C", exact=True), cols("D", "G")), "pct"),
        R("Hyperscaler share of bonds >10yr", ig.nums(ig.find("% hypers", ig.find(">10y", t_, cols="C:C"), cols="C:C"), cols("D", "G")), "pct", ind=1),
        R("Hyperscaler share of bonds 30yr+", ig.nums(ig.find("% hypers", ig.find("=>30y", t_, cols="C:C"), cols="C:C"), cols("D", "G")), "pct", ind=1),
    ], f"{F_SRC} › IG (weekly issuance)", "", "The latest year is year to date.")
    yc_ = FW["Yield Curves"]
    yh = yc_.find("10y Z Spread", cols="C:C")
    ycols = [c for c in cols("D", "L") if yc_.num(yh, c) is not None]
    yyrs = [int(yc_.num(yh, c)) for c in ycols]
    spread_rows = []
    for rr in range(yh + 1, yh + 12):
        nm = yc_.text(rr, "C")
        if not nm:
            continue
        nm2 = {"Hyperscaler": "Hyperscaler average", "IG Market Z": "IG market"}.get(next((k4 for k4 in ("Hyperscaler", "IG Market Z") if nm.startswith(k4)), ""), nm)
        if nm.startswith("Spread, %"):
            continue
        spread_rows.append(R("IG market minus hyperscaler average" if nm.startswith("Spread, bps") else nm2, yc_.nums(rr, ycols), "int",
                             b=nm.startswith(("Hyperscaler", "IG Market", "Spread"))))
    asof = yc_.text(3, ycols[-1]) if ycols else ""
    spreads = T("spreads", "10-year Z-spreads: hyperscalers vs the IG market", yyrs, spread_rows, f"{F_SRC} › Yield Curves", "bps",
                (f"Year-end readings; {yyrs[-1]} is as of {asof}. " if asof else "")
                + "IG market minus hyperscalers: positive = hyperscalers trade inside the IG market, negative = wide of it.")
    bk = FW["Baskets"]
    bh = bk.find("Bond", cols="C:C", exact=True)
    bonds = []
    for rr in range(bh + 1, bh + 10):
        nm = bk.text(rr, "C")
        if not nm:
            break
        bonds.append({"bond": nm.replace(" Corp", ""), "date": bk.text(rr, "D"), "size_bn": None if bk.num(rr, "F") is None else clean(bk.num(rr, "F") / 1000),
                      "tenor": bk.num(rr, "G"), "z": bk.num(rr, "H"), "pre": bk.num(rr, "I"), "nic": bk.num(rr, "J")})
    pf = FW["Project Finance Deals"]
    ph = pf.find("Company", cols="B:B", exact=True)
    pfd = [{"who": pf.text(rr, "B"), "what": pf.text(rr, "C"), "bn": clean(pf.num(rr, "D")) if pf.num(rr, "D") is not None else None,
            "date": pf.text(rr, "E")[:10], "detail": pf.text(rr, "F")} for rr in range(ph + 1, ph + 30) if pf.text(rr, "B")]
    docs["fin"] = {"tables": [market_su, hyper_su, ai_capex_co, lev, igt, spreads, wfe],
                   "bonds": bonds, "bonds_src": f"{F_SRC} › Baskets (30-year hyperscaler deals, new-issue concession)",
                   "project": pfd, "project_src": f"{F_SRC} › Project Finance Deals",
                   "debt": debt, "debt_src": f"{M_SRC} › Debt Financing",
                   "circular": {"mega": mega, "sources": circ_src, "uses": circ_use, "supply_chain": supply_chain, "src": f"{M_SRC} › Circular Financings"}}

    # ------------------------------------------------------------------ semis supply: HBM, CoWoS, WFE, semi capex
    hb = MW["HBM Model"]
    hc = cols("D", "H")  # 2023..2027
    hyrs = [int(hb.v(2, c)) for c in hc]
    dem = hb.find("HBM Demand by Customer", cols="B:B")
    sup0 = hb.find("HBM Supply", cols="B:B")
    rev_ = hb.find("HBM Revenue", cols="B:B")
    hbm_rows = [R(n, hb.nums(hb.find(n, dem, dem + 12, cols="B:B", exact=True), hc, 1e-3), "num1") for n in ("NVIDIA", "Google", "Amazon", "AMD", "Microsoft", "Meta", "Others")]
    hbm_rows.append(R("Total demand", hb.nums(hb.find("Total", dem, dem + 12, cols="B:B", exact=True), hc, 1e-3), "num1", b=True))
    hbm_rows += [R(f"{n} supply", hb.nums(hb.find(n, sup0, sup0 + 12, cols="B:B", exact=True), hc, 1e-6), "num1", ind=1) for n in ("SK Hynix", "Samsung", "Micron")]
    hbm_rows.append(R("Total supply", hb.nums(hb.find("Total", sup0, sup0 + 12, cols="B:B", exact=True), hc, 1e-6), "num1", b=True))
    hbm_rows.append(R("Supply vs demand", hb.nums(hb.find("% Delta vs Demand", sup0, cols="B:B"), hc), "pct", b=True))
    sup_g = hb.nums(hb.find("Y/Y %", hb.find("Total", sup0, sup0 + 12, cols="B:B", exact=True), cols="B:B", exact=True), hc)
    flat = sup_g[-1] is not None and all(abs((x or 0) - sup_g[-1]) < 1e-9 for x in hb.nums(hb.find("Y/Y %", hb.find("SK Hynix", sup0, cols="B:B", exact=True), cols="B:B", exact=True), hc)[-1:])
    hbm_bal = T("hbm_balance", "HBM demand by customer vs supply by vendor", hyrs, hbm_rows, f"{M_SRC} › HBM Model", "million GB",
                "Positive = supply above modeled demand." + (f" {hyrs[-1]} supply is the prior year grown at a flat {sup_g[-1]:.0%} placeholder, so treat the {hyrs[-1]} balance as indicative." if flat else ""), 2026)
    hrv = []
    for n in ("SK Hynix", "Samsung", "Micron"):
        r_ = hb.find(n, rev_, rev_ + 16, cols="B:B", exact=True)
        hrv.append(R(n, hb.nums(r_, hc, 1e-3), "bn"))
        sh = hb.find("% Total", r_, r_ + 3, cols="B:B", exact=True)
        hrv.append(R("share", hb.nums(sh, hc), "pct", ind=1))
    hrv.append(R("Total HBM revenue", hb.nums(hb.find("Total", rev_, rev_ + 16, cols="B:B", exact=True), hc, 1e-3), "bn", b=True))
    hbm_rev = T("hbm_rev", "HBM revenue by vendor", hyrs, hrv, f"{M_SRC} › HBM Model", "$bn", "", 2026)

    cw = MW["Cowos chips and WFE"]
    cc = cols("E", "P")  # CY2019..CY2030
    cyrs = [int(cw.text(5, c)[2:]) for c in cc]
    keepc = [i for i, y in enumerate(cyrs) if y >= 2022]
    sel = lambda vals: [vals[i] for i in keepc]
    cw_rows = []
    for lbl, nm, f, scale in [("TSMC CoWoS WPM, 000s", "TSMC CoWoS wafers per month (000s)", "num1", 1), ("TSMC cowos capacity, 000s", "TSMC CoWoS capacity, annual wafers (000s)", "int", 1),
                              ("TSMC cowos shipment capacity", "CoWoS wafers shipped after yield (000s)", "int", 1), ("NVDA cowos allocation", "NVDA allocation (000s)", "int", 1),
                              ("AMD cowos allocation", "AMD allocation (000s)", "int", 1), ("GOOGL cowos allocation", "Google allocation (000s)", "int", 1),
                              ("TSMC packaging capex, $mm", "TSMC packaging capex ($bn)", "num1", 1e-3)]:
        r_ = cw.find(lbl, cols="D:D")
        cw_rows.append(R(nm, sel(cw.nums(r_, cc, scale)), f, b=nm.startswith("TSMC CoWoS wafers per month")))
        if lbl.endswith("allocation"):
            cw_rows.append(R("share", sel(cw.nums(cw.find("% allocation", r_, r_ + 1, cols="D:D"), cc)), "pct", ind=1))
    cowos = T("cowos", "CoWoS: TSMC advanced-packaging capacity and allocation", [cyrs[i] for i in keepc], cw_rows, f"{M_SRC} › CoWoS chips and WFE", "", "", 2026)
    sc_rows = []
    s0 = cw.find("Capex by Customer", cols="D:D")
    for nm in ("TSMC", "Samsung", "SK Hynix", "Micron", "Intel", "SMIC", "CXMT", "Rapidus", "Kioxia", "SNDK"):
        r_ = cw.find(nm, s0, s0 + 20, cols="D:D", exact=True)
        sc_rows.append(R(nm, sel(cw.nums(r_, cc, 1e-3)), "bn"))
    tot_sc = sel(cw.nums(cw.find("Total Capex, $mm", s0, cols="D:D"), cc, 1e-3))
    sc_rows += [R("Total", tot_sc, "bn", b=True), R("y/y", growth(tot_sc), "pct", ind=1),
                R("Foundry / logic", sel(cw.nums(cw.find("Foundry/Logic", s0, cols="D:D", exact=True), cc, 1e-3)), "bn", ind=1),
                R("Memory", sel(cw.nums(cw.find("Memory", s0, cols="D:D", exact=True), cc, 1e-3)), "bn", ind=1)]
    semi_capex = T("semi_capex", "Semiconductor capex by company", [cyrs[i] for i in keepc], sc_rows, f"{M_SRC} › CoWoS chips and WFE", "$bn", "", 2026)

    wf = MW["WFE"]
    wc = cols("W", "AH")  # CY2017..CY2028
    wyrs = [int(wf.text(5, c)[2:]) for c in wc]
    keepw = [i for i, y in enumerate(wyrs) if y >= 2022]
    wsel = lambda vals: [vals[i] for i in keepw]
    wr0 = wf.find("WFE Breakdown", cols="B:B")

    def wrow(lbl, nm, f="bn", start=wr0, **kw):
        r_ = wf.find(lbl, start, cols="F:F", exact=True)
        return R(nm, wsel(wf.nums(r_, wc, 1e-3 if f == "bn" else 1)), f, **kw)

    base = wf.find("SRS Base Case W", wr0, cols="F:F")
    w_rows = [wrow("Foundry/Logic WFE", "Foundry / logic WFE"), wrow("DRAM WFE", "DRAM WFE"), wrow("NAND WFE", "NAND WFE"),
              R("SRS base-case WFE", wsel(wf.nums(base, wc, 1e-3)), "bn", b=True),
              R("y/y", wsel(wf.nums(base + 1, wc)), "pct", ind=1)]
    for lbl, nm in (("St", "Street"), ("LRCX", "Lam (3Q26 call)"), ("Semianalysis", "SemiAnalysis"), ("Buyside", "Buy-side")):
        r_ = wf.find(lbl, base, base + 10, cols="F:F")
        vals = []
        for c in wc:
            x = wf.v(r_, c)
            vals.append(clean(x / 1000) if isinstance(x, (int, float)) else (str(x) if x not in (None, "") else None))
        w_rows.append(R(nm, wsel(vals), "bn", ind=1))
    for lbl in ("Bluesky", "Upside", "Base", "Downside", "Double Downside"):
        r_ = wf.find(lbl, base, base + 20, cols="F:F", exact=True)
        w_rows.append(R(f"Scenario: {lbl.lower()}", wsel(wf.nums(r_, wc, 1e-3)), "bn", ind=1))
    wfe_t = T("wfe", "Wafer fab equipment: SRS base case vs Street and others", [wyrs[i] for i in keepw], w_rows, f"{M_SRC} › WFE", "$bn", "", 2026)
    # implied semicap upside at the base-case WFE (CY2027 $225bn column AP, CY2028 $300bn column AV)
    vb = []
    for tkr, r_name in (("ASML", "ASML, EUR"), ("AMAT", "AMAT"), ("LRCX", "LRCX"), ("KLAC", "KLAC")):
        r_ = wf.find(r_name, cols="AK:AK", exact=True)
        rows_ = {norm(wf.text(rr, "AK")): rr for rr in range(r_ + 1, r_ + 8)}
        for col, wfe_lvl in (("AP", wf.num(5, "AP")), ("AV", wf.num(5, "AV"))):
            yr = 2027 if col == "AP" else 2028
            vb.append({"t": tkr, "year": yr, "wfe": wfe_lvl, "px": wf.num(r_, "AL"),
                       "eps_st": clean(wf.num(rows_["eps st"], col)), "eps_srs": clean(wf.num(rows_["eps srs"], col)),
                       "vs_st": clean(wf.num(rows_["vs st"], col)), "pe": wf.num(rows_["pe"], col),
                       "target": clean(wf.num(rows_["share price"], col)), "updown": clean(wf.num(rows_["% u/d"], col))})
    # networking pieces that are intact in the model (optical TAM, copper connectivity)
    nmod = None
    try:
        nmod = load(master, ["Networking Model"])["Networking Model"]
    except KeyError:
        pass
    net_rows = []
    if nmod:
        nh = nmod.find("AI Networking, $mm", cols="B:B")
        nc = cols("D", "K")  # 2023..2030
        for lbl, nm in (("AI Optical TAM, $mm", "AI optical TAM"), ("AI Copper Connectivity", "AI copper connectivity")):
            try:
                r_ = nmod.find(lbl, nh, cols="B:B")
                vals = nmod.nums(r_, nc, 1e-3)
                net_rows.append(R(nm, vals, "bn", b=True))
                net_rows.append(R("y/y", growth(vals), "pct", ind=1))
            except KeyError:
                pass
    net_t = T("net_tam", "AI networking: optical and copper TAM", years(2023, 2030), net_rows, f"{M_SRC} › Networking Model", "$bn",
              "Switching and total AI-networking rows are broken (#REF!) in this version of the model and are left out.", 2026) if net_rows else None
    docs["supply"] = {"tables": [t for t in (wfe_t, hbm_bal, hbm_rev, cowos, semi_capex, net_t) if t],
                      "semicap": vb, "semicap_src": f"{M_SRC} › WFE (implied share prices at SRS WFE)"}

    # ------------------------------------------------------------------ headline calls (computed from the tables above)
    def pick(t, label, year):
        row = next(r_ for r_ in t["rows"] if r_["l"] == label)
        return row["v"][t["cols"].index(str(year))]

    calls = []
    tc26, tc27 = pick(capex_build, "Total AI capex", 2026), pick(capex_build, "Total AI capex", 2027)
    calls.append({"k": "capex", "v": f"${tc27 / 1000:.2f}T" if tc27 >= 1000 else f"${tc27:,.0f}bn", "l": f"AI capex 2027E ({(tc27 / tc26 - 1):+.0%} y/y)", "view": "capex"})
    g26 = pick(capacity, "Cumulative GW (SRS)", 2026)
    g28 = pick(capacity, "Cumulative GW (SRS)", 2028)
    calls.append({"k": "gw", "v": f"{g26:,.0f} → {g28:,.0f} GW", "l": "Global AI compute, 2026E → 2028E", "view": "capex"})
    v27 = pick(vs_street, "SRS vs Street", 2027)
    calls.append({"k": "street", "v": f"{v27:+.0%}".replace("-", "\u2212"), "l": "SRS vs Street Big-5 capex, 2027E", "tone": "neg" if v27 < 0 else "pos", "view": "revisions"})
    a26, a28 = pick(xpu_gw, "ASIC share", 2026), pick(xpu_gw, "ASIC share", 2028)
    calls.append({"k": "asic", "v": f"{a26:.0%} → {a28:.0%}", "l": "ASIC share of GW deployed, 2026E → 2028E", "view": "compute"})
    irr26 = pick(gpu, "Unlevered IRR by vintage", 2026)
    irr24 = pick(gpu, "Unlevered IRR by vintage", 2024)
    calls.append({"k": "irr", "v": f"{irr26:.1%}", "l": f"GPU rental IRR, 2026 vintage (2024: {irr24:.1%})", "tone": "neg" if irr26 < irr24 else "pos", "view": "econ"})
    gap28 = pick(market_su, "Sources minus uses", 2028)
    gap_first = next((y_ for y_, x in zip(market_su["cols"], next(r_ for r_ in market_su["rows"] if r_["l"] == "Sources minus uses")["v"]) if x is not None and x < 0), None)
    calls.append({"k": "gap", "v": (f"\u2212${abs(gap28):,.0f}bn" if gap28 < 0 else f"+${gap28:,.0f}bn"),
                  "l": "AI funding gap, 2028E (sources less AI capex)" + (f"; first gap in {gap_first}" if gap_first and gap_first != "2028" else ""),
                  "tone": "neg" if gap28 < 0 else "pos", "view": "fin"})
    hs26 = pick(igt, "Hyperscaler share of IG", f"{igy[-1]} YTD")
    calls.append({"k": "ig", "v": f"{hs26:.0%}", "l": f"Hyperscaler share of IG issuance, {igy[-1]} YTD", "view": "fin"})
    asof = {"compute": docs["compute"].get("updated", ""),
            "econ_chips": EW["Chips"].text(EW["Chips"].find("Updated", cols="A:C"), "B").replace("Updated", "").strip(),
            "spreads": next((t_["note"] for t_ in docs["fin"]["tables"] if t_["id"] == "spreads"), ""),
            "revisions": docs["revisions"]["snapshots"][-1] if docs["revisions"]["snapshots"] else ""}
    return docs, calls, asof


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--econ", required=True)
    ap.add_argument("--fin", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    docs, calls, asof = build(a.master, a.econ, a.fin)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    files = []
    for p in (a.master, a.econ, a.fin):
        st = Path(p)
        files.append({"name": re.sub(r"^[0-9a-f]{8}-", "", st.name)})
    meta = {"built_at": now, "files": files, "calls": calls, "views": list(docs.keys()), "asof": asof}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    for k, v in docs.items():
        v["built_at"] = now
        (out / f"{k}.json").write_text(json.dumps(v, ensure_ascii=False, separators=(",", ":")))
    sizes = {f.name: f.stat().st_size for f in sorted(out.glob("*.json"))}
    print(json.dumps({"out": str(out), "sizes": sizes}, indent=1))


if __name__ == "__main__":
    main()
