#!/usr/bin/env python3
"""Event panel: one row per reported quarter (revenue). Target = revenue surprise vs final consensus.
All features use only information available before the print date."""
import json, math, statistics as st
from collections import defaultdict
from datetime import date, timedelta

D = lambda s: date.fromisoformat(s[:10])
S = json.load(open('sales_surprise.json'))
G = json.load(open('guidance.json'))
C = json.load(open('cons_fq1.json'))
P = json.load(open('prices_m.json'))
cos = {c['fs']: c for c in json.load(open('../companies.json')) if c.get('fs')}

ev = defaultdict(list)
for r in S:
    if not r['surpriseBefore'] or not r['surpriseAfter'] or r['surpriseBefore'] <= 0: continue
    r['d'] = D(r['surpriseDate']); r['fe'] = D(r['fiscalEndDate'])
    r['sur'] = (r['surpriseAfter'] / r['surpriseBefore'] - 1) * 100
    ev[r['requestId']].append(r)
for k in ev: ev[k].sort(key=lambda r: r['fe'])
gd = {(g['requestId'], g['fiscalYear'], g['fiscalPeriod']): g for g in G}
cons = defaultdict(list)
for c in C: cons[(c['requestId'], c['fiscalYear'], c['fiscalPeriod'])].append(c)
for k in cons: cons[k].sort(key=lambda c: c['estimateDate'])
px = {k: sorted((D(d), v) for d, v in m.items()) for k, m in P.items()}

def asof(sr, t):
    v = None
    for d, x in sr:
        if d > t: break
        v = x
    return v

def by_fe(lst, fe, months):  # find event whose fiscal end is ~months earlier
    tgt = fe - timedelta(days=round(months * 30.44))
    best = None
    for r in lst:
        if abs((r['fe'] - tgt).days) <= 20: best = r
    return best

rows = []
for tk, lst in ev.items():
    co = cos.get(tk, {})
    for i, e in enumerate(lst):
        prior = [r for r in lst[:i] if r['d'] < e['d']]
        f = {'tk': tk, 'd': e['d'].isoformat(), 'fe': e['fe'].isoformat(), 'fy': e['fiscalYear'], 'fp': e['fiscalPeriod'],
             'sector': co.get('sector'), 'sub': (co.get('subs') or [co.get('sub')])[0], 'tier': co.get('tier'), 'sur': e['sur']}
        # --- beat tendency
        ps = [r['sur'] for r in prior]
        f['hist4'] = st.mean(ps[-4:]) if len(ps) >= 4 else None
        f['hist8'] = st.mean(ps[-8:]) if len(ps) >= 6 else None
        f['med8'] = st.median(ps[-8:]) if len(ps) >= 6 else None
        f['hit8'] = sum(x > 0 for x in ps[-8:]) / len(ps[-8:]) if len(ps) >= 6 else None
        f['last'] = ps[-1] if ps else None
        f['sd8'] = st.pstdev(ps[-8:]) if len(ps) >= 6 else None
        # --- comps & second derivative (actuals known before print)
        q1, q4, q5, q8, q9 = (by_fe(prior, e['fe'], m) for m in (3, 12, 15, 24, 27))
        a = lambda r: r['surpriseAfter'] if r else None
        cons_ = e['surpriseBefore']
        yoy = lambda x, y: (x / y - 1) * 100 if x and y and y > 0 else None
        f['yoy_prev'] = yoy(a(q1), a(q5))                      # last reported y/y
        f['comp'] = yoy(a(q4), a(q8))                          # year-ago quarter's y/y (the comp)
        f['comp_prev'] = yoy(a(q5), a(q9))
        f['impl_yoy'] = yoy(cons_, a(q4))                      # y/y implied by consensus
        f['d2_impl'] = f['impl_yoy'] - f['yoy_prev'] if f['impl_yoy'] is not None and f['yoy_prev'] is not None else None
        f['comp_chg'] = f['comp'] - f['comp_prev'] if f['comp'] is not None and f['comp_prev'] is not None else None
        if None not in (f['impl_yoy'], f['comp'], f['yoy_prev'], f['comp_prev']):
            f['stack_chg'] = ((1 + f['impl_yoy'] / 100) * (1 + f['comp'] / 100) - (1 + f['yoy_prev'] / 100) * (1 + f['comp_prev'] / 100)) * 100
        else: f['stack_chg'] = None
        # implied q/q vs normal seasonality for this fiscal period
        f['impl_qoq'] = yoy(cons_, a(q1))
        seas = []
        for yrs in (1, 2, 3):
            x, y = by_fe(prior, e['fe'], 12 * yrs), by_fe(prior, e['fe'], 12 * yrs + 3)
            v = yoy(a(x), a(y))
            if v is not None: seas.append(v)
        f['seas_gap'] = f['impl_qoq'] - st.median(seas) if seas and f['impl_qoq'] is not None else None
        # --- guidance
        g = gd.get((tk, e['fiscalYear'], e['fiscalPeriod']))
        if g and g['guidanceMidpoint'] and D(g['guidanceDate']) < e['d']:
            f['guided'] = 1
            f['cons_vs_guide'] = (cons_ / g['guidanceMidpoint'] - 1) * 100
            f['guide_vs_cons'] = (g['meanSurpriseAmtPercent'] or 0) * 100 if g['meanSurpriseAmtPercent'] is not None else None
            f['guide_width'] = (g['guidanceHigh'] - g['guidanceLow']) / g['guidanceMidpoint'] * 100 if g['guidanceHigh'] and g['guidanceLow'] else None
            # history of beating own guide midpoint
            bg = []
            for r in prior[-8:]:
                gg = gd.get((tk, r['fiscalYear'], r['fiscalPeriod']))
                if gg and gg['guidanceMidpoint']: bg.append((r['surpriseAfter'] / gg['guidanceMidpoint'] - 1) * 100)
            f['beat_guide_hist'] = st.mean(bg) if len(bg) >= 4 else None
            f['exp_sur_guide'] = ((1 + f['beat_guide_hist'] / 100) * g['guidanceMidpoint'] / cons_ - 1) * 100 if f['beat_guide_hist'] is not None else None
        else:
            f['guided'] = 0
            for k in ('cons_vs_guide', 'guide_vs_cons', 'guide_width', 'beat_guide_hist', 'exp_sur_guide'): f[k] = None
        # --- consensus drift, breadth, dispersion
        cs = [c for c in cons.get((tk, e['fiscalYear'], e['fiscalPeriod']), []) if D(c['estimateDate']) < e['d']]
        if cs:
            last = cs[-1]
            prevd = prior[-1]['d'] if prior else None
            first = next((c for c in cs if prevd is None or D(c['estimateDate']) > prevd + timedelta(days=3)), None)
            f['rev_q'] = (cons_ / first['mean'] - 1) * 100 if first and first['mean'] else None
            early = cs[0]
            f['rev_all'] = (cons_ / early['mean'] - 1) * 100 if early['mean'] else None
            f['disp'] = last['standardDeviation'] / last['mean'] * 100 if last['standardDeviation'] and last['mean'] else None
            f['hl'] = (last['high'] - last['low']) / last['mean'] * 100 if last['high'] and last['low'] and last['mean'] else None
            u, dn = last['up'] or 0, last['down'] or 0
            f['breadth'] = (u - dn) / (u + dn) if u + dn else None
            f['nest'] = last['estimateCount']
        else:
            for k in ('rev_q', 'rev_all', 'disp', 'hl', 'breadth', 'nest'): f[k] = None
        # --- price into print (month-end closes)
        s = px.get(tk, [])
        p0 = asof(s, e['d'] - timedelta(days=1)); p1 = asof(s, e['d'] - timedelta(days=31)); p3 = asof(s, e['d'] - timedelta(days=92))
        f['mom1'] = (p0 / p1 - 1) * 100 if p0 and p1 else None
        f['mom3'] = (p0 / p3 - 1) * 100 if p0 and p3 else None
        rows.append(f)

# --- peer read-across: same subsector / sector names that already reported in the prior 45 days (same season)
bysub = defaultdict(list); bysec = defaultdict(list)
for f in rows:
    bysub[f['sub']].append(f); bysec[f['sector']].append(f)
for f in rows:
    d = D(f['d'])
    for key, grp, nm in (('peer_sub', bysub[f['sub']], 'sub'), ('peer_sec', bysec[f['sector']], 'sec')):
        xs = [(g['sur'] - (g['med8'] or 0)) for g in grp if g['tk'] != f['tk'] and d - timedelta(days=45) <= D(g['d']) < d and g['med8'] is not None]
        f[key] = st.mean(xs) if len(xs) >= 2 else None
        f[key + '_n'] = len(xs)
# target variants
for f in rows:
    f['sur_x'] = f['sur'] - f['med8'] if f['med8'] is not None else None   # beat vs own typical beat
json.dump(rows, open('panel_rb.json', 'w'), default=str)
print(len(rows), 'events', sum(1 for f in rows if f['med8'] is not None), 'with 6+ priors', sum(f['guided'] for f in rows), 'guided')
