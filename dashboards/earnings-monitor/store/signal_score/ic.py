#!/usr/bin/env python3
"""Weekly cross-sectional rank ICs of each signal vs forward relative returns; fit + out-of-sample combo."""
import json, math, statistics as st, sys
from collections import defaultdict

R = json.load(open('panel.json'))
SIG = ['beta', 'ev_comp', 'ev_g', 'ev_m', 'ev_k', 'ev_r', 'ev_s', 'ev_flow30', 'ev_neg30', 'ev_n90', 'ev_sell', 'ev_channel', 'ev_mgmt', 'ev_social', 'evc_comp', 'evc_flow30',
       'mom1', 'mom3', 'mom6x1', 'dist_hi', 'vol12', 'size', 'rev_eps4', 'rev_eps12', 'rev_sales4', 'rev_sales12', 'ey', 'pt_up', 'sur_sales', 'sur_eps',
       'ins_sellers_np', 'ins_sellers', 'ins_buyers', 'ins_csuite_np']
by = defaultdict(list)
for r in R: by[r['date']].append(r)
dates = sorted(by)

def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); rk = [0] * len(xs); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]: j += 1
        for k in range(i, j + 1): rk[o[k]] = (i + j) / 2
        i = j + 1
    return rk
def spear(a, b):
    if len(a) < 15: return None
    ra, rb = rank(a), rank(b)
    ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None

def target(rows, h, rel):
    ys = [r[h] for r in rows]
    if rel == 'sector':
        sec = defaultdict(list)
        for r in rows:
            if r[h] is not None: sec[r['sector']].append(r[h])
        med = {k: st.median(v) for k, v in sec.items()}
        return [None if r[h] is None else r[h] - med[r['sector']] for r in rows]
    vals = [y for y in ys if y is not None]
    m = st.median(vals) if vals else 0
    return [None if y is None else y - m for y in ys]

def ics(sig, h, rel, ds):
    out = []
    for d in ds:
        rows = by[d]; y = target(rows, h, rel)
        pr = [(r.get(sig), yy) for r, yy in zip(rows, y) if r.get(sig) is not None and yy is not None]
        if len(pr) < 15 or len({p[0] for p in pr}) < 5: continue
        v = spear([p[0] for p in pr], [p[1] for p in pr])
        if v is not None: out.append((d, v, len(pr)))
    return out

def summ(xs, overlap):
    v = [x[1] for x in xs]
    if len(v) < 4: return None
    m, s = st.mean(v), st.pstdev(v) or 1e-9
    neff = max(1, len(v) / overlap)
    return {'ic': m, 't': m / (s / math.sqrt(neff)), 'hit': sum(1 for x in v if x > 0) / len(v), 'n_dates': len(v), 'n_names': round(st.mean(x[2] for x in xs))}

if __name__ == '__main__':
    out = {}
    for h, ov in (('f4b', 4), ('f12b', 12)):
        for rel in ('universe', 'sector'):
            ds = [d for d in dates if any(r[h] is not None for r in by[d])]
            res = {s: summ(ics(s, h, rel, ds), ov) for s in SIG}
            out[f'{h}_{rel}'] = res
            print(f'\n== {h} vs {rel} ({len(ds)} dates {ds[0]}..{ds[-1]})')
            for s, v in sorted(res.items(), key=lambda kv: -abs(kv[1]['ic']) if kv[1] else 0):
                if v: print(f"  {s:15s} IC {v['ic']:+.3f}  t {v['t']:+.2f}  hit {v['hit']:.0%}  names {v['n_names']}")
    json.dump(out, open('ic_results.json', 'w'), indent=1)
