#!/usr/bin/env python3
"""Fit signal weights on the first half, test the composite on the second half (beta-adjusted 4w and 12w returns)."""
import json, math, statistics as st
from ic import by, dates, ics, summ, spear, target, SIG

def z(rows, s):
    v = [r.get(s) for r in rows]; ok = [x for x in v if x is not None]
    if len(ok) < 10: return [0.0] * len(rows)
    srt = sorted(ok); n = len(srt)
    def q(x):  # rank -> approx normal score
        lo = sum(1 for y in srt if y < x); eq = sum(1 for y in srt if y == x)
        p = (lo + eq / 2) / n; p = min(max(p, 0.01), 0.99)
        return math.sqrt(2) * erfinv(2 * p - 1)
    return [q(x) if x is not None else 0.0 for x in v]
def erfinv(y):
    a = 0.147; ln = math.log(1 - y * y); t = 2 / (math.pi * a) + ln / 2
    return math.copysign(math.sqrt(math.sqrt(t * t - ln / a) - t), y)

def comp_ic(weights, h, rel, ds):
    out = []
    for d in ds:
        rows = by[d]; y = target(rows, h, rel)
        Z = {s: z(rows, s) for s in weights}
        sc = [sum(w * Z[s][i] for s, w in weights.items()) for i in range(len(rows))]
        pr = [(a, b) for a, b in zip(sc, y) if b is not None]
        v = spear([p[0] for p in pr], [p[1] for p in pr])
        if v is not None: out.append((d, v, len(pr)))
    return out

def fit(h, ov, rel, ds, cands, tmin=1.0):
    w = {}
    for s in cands:
        r = summ(ics(s, h, rel, ds), ov)
        if r and abs(r['t']) >= tmin: w[s] = r['ic']
    tot = sum(abs(x) for x in w.values()) or 1
    return {s: x / tot for s, x in w.items()}

CANDS = [s for s in SIG if s not in ('evc_comp', 'evc_flow30', 'ins_sellers', 'ins_csuite_np', 'ins_buyers')]
if __name__ == '__main__':
    for h, ov in (('f4b', 4), ('f12b', 12)):
        ds = [d for d in dates if any(r[h] is not None for r in by[d])]
        k = len(ds) // 2; tr, te = ds[:k], ds[k + (ov // 4 if h == 'f12b' else 1):]   # gap so train returns don't overlap test
        for rel in ('universe', 'sector'):
            w = fit(h, ov, rel, tr, CANDS)
            a = summ(comp_ic(w, h, rel, te), ov); b = summ(comp_ic({'ev_comp': 1}, h, rel, te), ov)
            print(f"{h} {rel}: train {tr[0]}..{tr[-1]} test {te[0]}..{te[-1]}")
            print('   weights', {s: round(x, 2) for s, x in sorted(w.items(), key=lambda kv: -abs(kv[1]))})
            print(f"   TEST composite IC {a['ic']:+.3f} t {a['t']:+.2f} hit {a['hit']:.0%} | current evidence index IC {b['ic']:+.3f} t {b['t']:+.2f}")
