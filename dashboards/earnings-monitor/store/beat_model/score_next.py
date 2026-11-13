#!/usr/bin/env python3
"""Score each company's next unreported quarter with the beat model, using data as of today."""
import json, statistics as st
from collections import defaultdict
from datetime import date, timedelta
from model_rb import vec, W
import numpy as np

TODAY = date(2026, 11, 13)
D = lambda s: date.fromisoformat(s[:10])
coef = json.load(open('model_rb.json'))['coef']; b = np.array(list(coef.values()))
S = json.load(open('sales_surprise.json')); G = json.load(open('guidance.json')); C = json.load(open('cons_fq1.json'))
PW = json.load(open('../prices_w.json'))
cos = {c['fs']: c for c in json.load(open('../companies.json')) if c.get('fs')}
panel = json.load(open('panel_rb.json'))
ev = defaultdict(list)
for r in S:
    if r['surpriseBefore'] and r['surpriseAfter'] and r['surpriseBefore'] > 0:
        r['d'] = D(r['surpriseDate']); r['fe'] = D(r['fiscalEndDate']); r['sur'] = (r['surpriseAfter'] / r['surpriseBefore'] - 1) * 100
        ev[r['requestId']].append(r)
for k in ev: ev[k].sort(key=lambda r: r['fe'])
gd = {(g['requestId'], g['fiscalYear'], g['fiscalPeriod']): g for g in G}
cons = defaultdict(list)
for c in C: cons[c['requestId']].append(c)
for k in cons: cons[k].sort(key=lambda c: c['estimateDate'])

def by_fe(lst, fe, months):
    tgt = fe - timedelta(days=round(months * 30.44))
    return next((r for r in reversed(lst) if abs((r['fe'] - tgt).days) <= 20), None)

out = []
for tk, lst in ev.items():
    cs = cons.get(tk)
    if not cs or len(lst) < 6: continue
    nxt = cs[-1]                                           # latest FQ1 snapshot (2026-11-01)
    if any(r['fiscalYear'] == nxt['fiscalYear'] and r['fiscalPeriod'] == nxt['fiscalPeriod'] for r in lst): continue   # already reported
    fe = D(nxt['fiscalEndDate']); last = lst[-1]
    if (fe - last['fe']).days > 120: continue
    ps = [r['sur'] for r in lst]
    f = {'tk': tk, 'name': cos.get(tk, {}).get('name'), 'sub': (cos.get(tk, {}).get('subs') or [cos.get(tk, {}).get('sub')])[0], 'tier': cos.get(tk, {}).get('tier'),
         'fy': nxt['fiscalYear'], 'fp': nxt['fiscalPeriod'], 'fe': fe.isoformat(),
         'med8': st.median(ps[-8:]), 'last': ps[-1], 'hit8': sum(x > 0 for x in ps[-8:]) / len(ps[-8:])}
    ya = by_fe(lst, fe, 12)
    f['est_print'] = (ya['d'] + timedelta(days=364)).isoformat() if ya else (last['d'] + timedelta(days=91)).isoformat()
    first = next((c for c in cs if c['fiscalYear'] == nxt['fiscalYear'] and c['fiscalPeriod'] == nxt['fiscalPeriod'] and D(c['estimateDate']) > last['d'] + timedelta(days=3)), None)
    f['cons'] = nxt['mean']; f['rev_q'] = (nxt['mean'] / first['mean'] - 1) * 100 if first and first['mean'] else 0.0
    g = gd.get((tk, nxt['fiscalYear'], nxt['fiscalPeriod']))
    f['guided'] = 1 if g and g['guidanceMidpoint'] else 0
    f['guide_mid'] = g['guidanceMidpoint'] if f['guided'] else None
    f['guide_vs_cons'] = (g['meanSurpriseAmtPercent'] or 0) * 100 if f['guided'] and g['meanSurpriseAmtPercent'] is not None else None
    f['cons_vs_guide'] = (nxt['mean'] / g['guidanceMidpoint'] - 1) * 100 if f['guided'] else None
    q1, q4, q5, q8 = (by_fe(lst, fe, m) for m in (3, 12, 15, 24))
    yy = lambda x, y: (x['surpriseAfter'] / y['surpriseAfter'] - 1) * 100 if x and y else None
    f['yoy_prev'] = yy(q1, q5); f['comp'] = yy(q4, q8); f['impl_yoy'] = (nxt['mean'] / q4['surpriseAfter'] - 1) * 100 if q4 else None
    p = sorted((D(d), v[0]) for d, v in PW.get(tk, {}).items() if v and v[0])
    p0 = p[-1][1] if p else None; p3 = next((v for d, v in reversed(p) if d <= TODAY - timedelta(days=92)), None)
    f['mom3'] = (p0 / p3 - 1) * 100 if p0 and p3 else None
    sub = f['sub']
    xs = [(r['sur'] - r['med8']) for r in panel if r['sub'] == sub and r['tk'] != tk and r['med8'] is not None and TODAY - timedelta(days=45) <= D(r['d']) <= TODAY]
    f['peer_sub'] = st.mean(xs) if len(xs) >= 2 else None
    f['pred'] = float(b[0] + np.dot(b[1:], vec(f)))
    out.append(f)
out.sort(key=lambda f: f['est_print'])
json.dump(out, open('next_scores.json', 'w'), indent=1, default=str)
soon = [f for f in out if f['est_print'] <= '2027-01-15']
print(len(out), 'scored;', len(soon), 'est. printing by mid-Jan')
for f in sorted(soon, key=lambda f: -f['pred']):
    print(f"{f['tk']:10s} {str(f['name'])[:16]:16s} {f['est_print']}  pred {f['pred']:+.1f}%  med8 {f['med8']:+.1f} last {f['last']:+.1f} hit {f['hit8']:.0%} rev {f['rev_q']:+.1f} "
          f"g/c {f['guide_vs_cons'] if f['guide_vs_cons'] is not None else float('nan'):+.1f} c/g {f['cons_vs_guide'] if f['cons_vs_guide'] is not None else float('nan'):+.1f} mom3 {f['mom3'] if f['mom3'] is not None else float('nan'):+.0f} peer {f['peer_sub'] if f['peer_sub'] is not None else float('nan'):+.1f}")
