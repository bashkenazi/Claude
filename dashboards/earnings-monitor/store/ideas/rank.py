#!/usr/bin/env python3
"""Weekly idea ranking: 50% Signal percentile, 25% fresh beat (latest revenue surprise minus median of prior 8), 25% expected next beat.
Run in the working folder after signal_score (stock_scores_latest.json, panel.json) and beat_model (bm/next_scores.json)."""
import json, statistics as st, sys
from collections import defaultdict
from datetime import date, timedelta
TODAY = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
LEDGER = sys.argv[2] if len(sys.argv) > 2 else 'ledger.json'
cos = {c['fs']: c for c in json.load(open('companies.json'))}
sig = {s['fs']: s for s in json.load(open('stock_scores_latest.json'))['scores']}
panel = {r['fs']: r for r in json.load(open('panel.json')) if r['date'] == TODAY}
nxt = {f['tk']: f for f in json.load(open('bm/next_scores.json'))}
ev = defaultdict(list)
for r in json.load(open('sales_surprise.json')):
    if r['surpriseBefore'] and r['surpriseAfter'] and r['surpriseBefore'] > 0:
        ev[r['requestId']].append((r['fiscalEndDate'], r['surpriseDate'], (r['surpriseAfter'] / r['surpriseBefore'] - 1) * 100))
for k in ev: ev[k].sort()
PT = json.load(open('pt.json')); PW = json.load(open('prices_w.json'))
rows = []
for fs, s in sig.items():
    c = cos[fs]; e = ev.get(fs, []); p = panel.get(fs, {})
    last = e[-1][2] if e else None
    fresh = last - st.median([x[2] for x in e[-9:-1]]) if len(e) >= 7 else None
    px = sorted(PW[fs].items()); p0 = px[-1][1][0]
    pt = list(PT.get(fs, {}).values())
    n = nxt.get(fs)
    rows.append({'fs': fs, 't': c['t'], 'name': c['name'], 'tier': c['tier'], 'sub': (c.get('subs') or [c.get('sub')])[0],
                 'sig': s['score'], 'pctl': s['pctl'], 'parts': s['parts'], 'inp': s['inputs'], 'n_prints': len(e),
                 'last_sur': last, 'fresh': fresh, 'last_date': e[-1][1] if e else None,
                 'med8': st.median([x[2] for x in e[-9:-1]]) if len(e) >= 7 else None,
                 'pred': n['pred'] if n else None, 'next': n['est_print'] if n else None,
                 'rev_q': n['rev_q'] if n else None, 'guide_vs_cons': n['guide_vs_cons'] if n else None,
                 'mom3': p['mom3'] * 100 if p.get('mom3') is not None else None,
                 'rev_eps12': p.get('rev_eps12'), 'rev_sales4': p.get('rev_sales4'), 'rev_sales12': p.get('rev_sales12'),
                 'pe_ntm': 1 / p['ey'] if p.get('ey') and p['ey'] > 0 else None,
                 'pt_up': (pt[0] / p0 - 1) * 100 if pt else None,
                 'ins_sellers': p.get('ins_sellers'), 'ins_buyers': p.get('ins_buyers'), 'ins_csuite_np': p.get('ins_csuite_np')})
def pr(key):
    v = sorted(r[key] for r in rows if r[key] is not None); n = len(v)
    for r in rows:
        x = r[key]
        r['p_' + key.replace('sig', 'sig')] = None if x is None else (sum(1 for y in v if y < x) + (sum(1 for y in v if y == x) - 1) / 2) / (n - 1)
for k in ('sig', 'fresh', 'pred'): pr(k)
for r in rows:
    r['combo'] = .5 * r['p_sig'] + .25 * (r['p_fresh'] if r['p_fresh'] is not None else .5) + .25 * (r['p_pred'] if r['p_pred'] is not None else .5)
rows.sort(key=lambda r: -r['combo'])
L = json.load(open(LEDGER)); cut = (date.fromisoformat(TODAY) - timedelta(weeks=8)).isoformat()
recent = {x for run in L['runs'] if run['date'] >= cut for x in run['longs'] + run['shorts']}
def pick(seq, k, extra=3):
    out, subs = [], set()
    for r in seq:
        if r['n_prints'] < 6 or r['fs'] in recent or r['sub'] in subs: continue
        out.append(r); subs.add(r['sub'])
        if len(out) == k + extra: break
    return out[:k], out[k:]
longs, ru_l = pick(rows, 3); shorts, ru_s = pick(rows[::-1], 5)
json.dump(rows, open(f'ranking_{TODAY}.json', 'w'), indent=1)
json.dump({'longs': longs, 'shorts': shorts, 'ru_l': ru_l, 'ru_s': ru_s}, open('picks.json', 'w'), indent=1)
f = lambda x, d=1: '—' if x is None else f'{x:+.{d}f}'
for nm, g in (('LONGS', longs), ('RU long', ru_l), ('SHORTS', shorts), ('RU short', ru_s)):
    print('==', nm)
    for r in g:
        print(f"{r['fs']:10s} {r['name'][:18]:18s} {r['sub'][:22]:22s} combo {r['combo']:.3f} sig {r['sig']:+.1f} parts {r['parts']} last {f(r['last_sur'])} med8 {f(r['med8'])} fresh {f(r['fresh'])} ({r['last_date']}) pred {f(r['pred'])} next {r['next']} revq {f(r['rev_q'])} g/c {f(r['guide_vs_cons'])} "
              f"rEPS12 {f((r['rev_eps12'] or 0)*100)} rSal12 {f((r['rev_sales12'] or 0)*100)} PE {f(r['pe_ntm'],0)} PT {f(r['pt_up'],0)} mom3 {f(r['mom3'],0)} ins_np {r['inp']['ins_sellers_np']} sellers {r['ins_sellers']} buyers {r['ins_buyers']} ev_sell {r['inp']['ev_sell']} ev_neg30 {r['inp']['ev_neg30']}")
