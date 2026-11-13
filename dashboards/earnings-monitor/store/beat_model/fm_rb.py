#!/usr/bin/env python3
"""Fama-MacBeth: per calendar quarter, regress rank(surprise) on within-quarter ranks of all setup features at once.
Shows which inputs add information once beat tendency is controlled. Then out-of-sample test (fit <=2023, test 2024+)."""
import json, math, statistics as st
from collections import defaultdict
import numpy as np

R = [r for r in json.load(open('panel_rb.json')) if r['d'] >= '2019-07-01']
for r in R: r['cq'] = r['d'][:4] + 'Q' + str((int(r['d'][5:7]) - 1) // 3 + 1)
byq = defaultdict(list)
for r in R: byq[r['cq']].append(r)
Q = sorted(byq)
X = ['last', 'hist8', 'hit8', 'sd8', 'guide_vs_cons', 'cons_vs_guide', 'guide_width', 'beat_guide_hist', 'rev_q', 'breadth',
     'd2_impl', 'comp', 'seas_gap', 'yoy_prev', 'mom3', 'peer_sub', 'disp']

def rk(vals):  # within-quarter rank in [-0.5,0.5]; missing -> 0
    idx = [i for i, v in enumerate(vals) if v is not None]
    out = [0.0] * len(vals)
    if len(idx) < 5: return out
    srt = sorted(idx, key=lambda i: vals[i])
    for j, i in enumerate(srt): out[i] = j / (len(srt) - 1) - 0.5
    return out

def design(rows, feats):
    cols = [rk([r.get(f) for r in rows]) for f in feats]
    A = np.array(cols).T
    y = np.array(rk([r['sur'] for r in rows]))
    return np.column_stack([np.ones(len(rows)), A]), y

def fm(qs, feats):
    B = []
    for q in qs:
        rows = byq[q]
        if len(rows) < 40: continue
        A, y = design(rows, feats)
        b, *_ = np.linalg.lstsq(A, y, rcond=None); B.append(b[1:])
    B = np.array(B); m = B.mean(0); se = B.std(0) / math.sqrt(len(B))
    return m, m / se, len(B)

def spear(a, b):
    a, b = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(a, b)[0, 1])

if __name__ == '__main__':
    m, t, n = fm(Q, X)
    print(f'Fama-MacBeth over {n} quarters (target = rank of revenue surprise)')
    for f, b, tt in sorted(zip(X, m, t), key=lambda z: -abs(z[2])):
        print(f'  {f:16s} coef {b:+.3f}  t {tt:+5.1f}')
    # out of sample
    tr = [q for q in Q if q < '2024']; te = [q for q in Q if q >= '2024']
    res = {}
    for name, feats in (('beat history only', ['last', 'hist8', 'hit8']), ('full setup', X)):
        mm, tt, _ = fm(tr, feats)
        ics, spreads, top, bot = [], [], [], []
        for q in te:
            rows = byq[q]
            if len(rows) < 40: continue
            A, y = design(rows, feats)
            p = A[:, 1:] @ mm
            ics.append(spear(p, [r['sur'] for r in rows]))
            o = np.argsort(p); k = len(o) // 5
            top += [rows[i]['sur'] for i in o[-k:]]; bot += [rows[i]['sur'] for i in o[:k]]
        res[name] = ics
        print(f"\nOOS 2024-26 [{name}]: IC {st.mean(ics):+.3f} (t {st.mean(ics) / (st.pstdev(ics) / math.sqrt(len(ics))):+.1f}, {len(ics)} qtrs)"
              f" | top quintile avg beat {st.median(top):+.2f}% beat-rate {sum(x > 0 for x in top) / len(top):.0%}"
              f" | bottom {st.median(bot):+.2f}% beat-rate {sum(x > 0 for x in bot) / len(bot):.0%}")
    json.dump({'fm': {f: [float(b), float(tt)] for f, b, tt in zip(X, m, t)}}, open('fm_rb.json', 'w'), indent=1)
