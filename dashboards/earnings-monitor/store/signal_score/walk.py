#!/usr/bin/env python3
"""Walk-forward: at each date, weight signals by their IC measured only on returns already known (expanding window,
4-week gap), shrunk by t-stat; score the date; report the out-of-sample IC of the composite."""
import json, math, statistics as st
from datetime import date, timedelta
from ic import by, dates, ics, summ, spear, target, SIG
from combo import z, comp_ic

def run(h, ov, rel, cands, gapw, minhist=8, shrink=2.0, label=''):
    ds = [d for d in dates if any(r[h] is not None for r in by[d])]
    res, wlog = [], []
    hist = {s: ics(s, h, rel, ds) for s in cands}
    for i, d in enumerate(ds):
        cut = (date.fromisoformat(d) - timedelta(weeks=gapw)).isoformat()
        w = {}
        for s in cands:
            xs = [x for x in hist[s] if x[0] <= cut]
            if len(xs) < minhist: continue
            r = summ(xs, ov)
            w[s] = r['ic'] * min(1.0, abs(r['t']) / shrink)
        if not w: continue
        tot = sum(abs(x) for x in w.values()) or 1
        w = {s: x / tot for s, x in w.items()}
        v = comp_ic(w, h, rel, [d])
        if v: res.append(v[0]); wlog.append((d, w))
    s = summ(res, ov); b = summ([x for x in ics('ev_comp', h, rel, ds) if x[0] in {r[0] for r in res}], ov)
    print(f"{label} {h} {rel}: OOS dates {res[0][0]}..{res[-1][0]} ({len(res)})  composite IC {s['ic']:+.3f} t {s['t']:+.2f} hit {s['hit']:.0%} | current index {b['ic']:+.3f} t {b['t']:+.2f}")
    return res, wlog

ALL = [s for s in SIG if s not in ('evc_comp', 'evc_flow30', 'ins_sellers', 'ins_csuite_np', 'ins_buyers')]
CORE = ['sur_sales', 'sur_eps', 'ey', 'pt_up', 'ins_sellers_np', 'ev_neg30', 'ev_sell', 'ev_channel', 'ev_g', 'ev_r', 'ev_n90', 'rev_eps4', 'rev_sales4', 'vol12']
if __name__ == '__main__':
    for nm, c in (('ALL', ALL), ('CORE(no momentum)', CORE)):
        run('f4b', 4, 'universe', c, 4, label=nm); run('f4b', 4, 'sector', c, 4, label=nm)
        pass
