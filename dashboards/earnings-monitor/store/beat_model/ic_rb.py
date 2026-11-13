#!/usr/bin/env python3
"""What predicts revenue surprise? Cross-sectional rank IC per calendar quarter (t across quarters), quintile spreads,
and halves (2019-22 vs 2023-26) consistency. Targets: raw surprise and surprise vs own typical beat."""
import json, math, statistics as st, sys
from collections import defaultdict

R = [r for r in json.load(open('panel_rb.json')) if r['d'] >= '2019-07-01']
for r in R:
    for k in ('sur', 'sur_x', 'last', 'hist4', 'hist8'):
        if r.get(k) is not None: r[k] = max(-25, min(25, r[k]))   # winsorize
    r['cq'] = r['d'][:4] + 'Q' + str((int(r['d'][5:7]) - 1) // 3 + 1)
FEATS = ['hist8', 'hist4', 'med8', 'hit8', 'last', 'sd8', 'yoy_prev', 'comp', 'comp_chg', 'impl_yoy', 'd2_impl', 'stack_chg', 'seas_gap',
         'cons_vs_guide', 'guide_vs_cons', 'guide_width', 'beat_guide_hist', 'exp_sur_guide', 'rev_q', 'rev_all', 'disp', 'hl', 'breadth', 'nest',
         'mom1', 'mom3', 'peer_sub', 'peer_sec']

def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i]); rk = [0.0] * len(xs); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]: j += 1
        for k in range(i, j + 1): rk[o[k]] = (i + j) / 2
        i = j + 1
    return rk
def spear(a, b):
    if len(a) < 12: return None
    ra, rb = rank(a), rank(b); ma, mb = st.mean(ra), st.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None

byq = defaultdict(list)
for r in R: byq[r['cq']].append(r)
Q = sorted(byq)

def ic(feat, tgt, qs):
    v = []
    for q in qs:
        pr = [(r[feat], r[tgt]) for r in byq[q] if r.get(feat) is not None and r.get(tgt) is not None]
        s = spear([p[0] for p in pr], [p[1] for p in pr])
        if s is not None: v.append(s)
    if len(v) < 6: return None
    m = st.mean(v); sd = st.pstdev(v) or 1e-9
    return {'ic': m, 't': m / (sd / math.sqrt(len(v))), 'hit': sum(x > 0 for x in v) / len(v), 'nq': len(v)}

def quint(feat, tgt):
    # pooled within-quarter quintiles: avg surprise and beat rate by quintile
    b = defaultdict(list)
    for q in Q:
        rs = [r for r in byq[q] if r.get(feat) is not None and r.get(tgt) is not None]
        if len(rs) < 15: continue
        rs.sort(key=lambda r: r[feat])
        for i, r in enumerate(rs): b[min(4, i * 5 // len(rs))].append(r)
    return [(round(st.mean(r[tgt] for r in b[k]), 2), round(sum(r['sur'] > 0 for r in b[k]) / len(b[k]) * 100), len(b[k])) for k in range(5)]

H1 = [q for q in Q if q < '2023'];  H2 = [q for q in Q if q >= '2023']
out = {}
for tgt in ('sur', 'sur_x'):
    print(f'\n=== target {tgt}  ({len(Q)} quarters {Q[0]}..{Q[-1]}, {sum(len(byq[q]) for q in Q)} prints)')
    res = []
    for f in FEATS:
        a = ic(f, tgt, Q)
        if not a: continue
        h1, h2 = ic(f, tgt, H1), ic(f, tgt, H2)
        n = sum(1 for r in R if r.get(f) is not None and r.get(tgt) is not None)
        res.append((f, a, h1, h2, n))
    res.sort(key=lambda x: -abs(x[1]['t']))
    for f, a, h1, h2, n in res:
        print(f"  {f:16s} IC {a['ic']:+.3f} t {a['t']:+5.1f} qhit {a['hit']:.0%} | 19-22 {h1['ic'] if h1 else float('nan'):+.3f} 23-26 {h2['ic'] if h2 else float('nan'):+.3f} | n {n}  Q {quint(f, tgt)}")
    out[tgt] = {f: {'all': a, 'h1': h1, 'h2': h2, 'n': n, 'quint': quint(f, tgt)} for f, a, h1, h2, n in res}
json.dump(out, open('ic_rb.json', 'w'), indent=1)
