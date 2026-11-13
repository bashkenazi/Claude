#!/usr/bin/env python3
"""Interpretable beat model in % units: pooled OLS of revenue surprise on the inputs that survived the multivariate test.
Fit <=2023, test 2024+; then refit on all and score each company's next unreported quarter."""
import json, math, statistics as st
from collections import defaultdict
from datetime import date, timedelta
import numpy as np

D = lambda s: date.fromisoformat(s[:10])
R = [r for r in json.load(open('panel_rb.json')) if r['d'] >= '2019-07-01' and r.get('med8') is not None]
W = lambda x, a=10: None if x is None else max(-a, min(a, x))
FE = ['med8', 'last', 'rev_q', 'guided', 'guide_vs_cons', 'mom3', 'easy_comp', 'peer_sub']

def vec(r):
    return [W(r['med8']), W(r['last']), W(r.get('rev_q') or 0, 8), r['guided'], W(r.get('guide_vs_cons') or 0, 15),
            W((r.get('mom3') or 0) / 10, 4), W(-(r['comp'] - (r.get('yoy_prev') or 0)) / 10 if r.get('comp') is not None and r.get('yoy_prev') is not None else 0, 5),
            W(r.get('peer_sub') or 0, 5)]

def fit(rows):
    A = np.array([[1] + vec(r) for r in rows]); y = np.array([W(r['sur'], 15) for r in rows])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ b; s2 = res @ res / (len(y) - A.shape[1])
    se = np.sqrt(np.diag(s2 * np.linalg.inv(A.T @ A)))
    return b, se

def pred(b, r): return float(b[0] + np.dot(b[1:], vec(r)))

if __name__ == '__main__':
    tr = [r for r in R if r['d'] < '2024-01-01']; te = [r for r in R if r['d'] >= '2024-01-01']
    b, se = fit(tr)
    p = [pred(b, r) for r in te]; y = [r['sur'] for r in te]
    o = np.argsort(p); k = len(o) // 5
    print('OOS 2024-26 (fit 2019-23):', len(te), 'prints')
    for name, idx in (('predicted top 20%', o[-k:]), ('middle', o[k:-k]), ('predicted bottom 20%', o[:k])):
        ys = [y[i] for i in idx]; ps = [p[i] for i in idx]
        print(f'  {name:22s} predicted {st.mean(ps):+.2f}%  actual median {st.median(ys):+.2f}%  beat-rate {sum(v > 0 for v in ys) / len(ys):.0%}  miss>1% {sum(v < -1 for v in ys) / len(ys):.0%}')
    # baseline: median of last 8 only
    base = [r['med8'] for r in te]; ob = np.argsort(base)
    print(f"  baseline (own median beat) top 20% actual {st.median([y[i] for i in ob[-k:]]):+.2f}% beat-rate {sum(y[i] > 0 for i in ob[-k:]) / k:.0%} | bottom {st.median([y[i] for i in ob[:k]]):+.2f}% beat-rate {sum(y[i] > 0 for i in ob[:k]) / k:.0%}")
    b, se = fit(R)
    print('\nFull-sample coefficients (% surprise per unit):')
    for n, c, s in zip(['const'] + FE, b, se): print(f'  {n:14s} {c:+.3f}  (t {c / s:+.1f})')
    json.dump({'coef': dict(zip(['const'] + FE, map(float, b))), 't': dict(zip(['const'] + FE, map(float, b / se)))}, open('model_rb.json', 'w'), indent=1)
