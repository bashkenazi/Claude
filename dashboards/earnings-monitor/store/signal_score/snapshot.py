import json, statistics as st, math
from ic import by, dates, ics, summ
from combo import z, comp_ic
from final import W, spread
d = max(dates); rows = by[d]
Z = {s: z(rows, s) for s in W}
GROUP = {'sur_sales': 'earn', 'sur_eps': 'earn', 'ins_sellers_np': 'ins', 'ey': 'val', 'ev_sell': 'crowd', 'ev_neg30': 'crowd', 'rev_eps4': 'crowd', 'ev_r': 'crowd', 'vol12': 'risk'}
out = []
raw = [sum(W[s] * Z[s][i] for s in W) for i in range(len(rows))]
srt = sorted(raw)
for i, r in enumerate(rows):
    g = {}
    for s in W: g[GROUP[s]] = g.get(GROUP[s], 0) + W[s] * Z[s][i]
    pctl = round(100 * sum(1 for x in srt if x < raw[i]) / (len(srt) - 1))
    out.append({'t': r['t'], 'fs': r['fs'], 'score': round(max(-100, min(100, raw[i] * 45)), 1), 'pctl': pctl,
                'parts': {k: round(v * 45, 1) for k, v in g.items()},
                'inputs': {k: (None if r.get(k) is None else round(r[k], 4)) for k in W}, 'ev_comp': round(r['ev_comp'], 1)})
ds4 = [x for x in dates if any(rr['f4b'] is not None for rr in by[x])]; ds12 = [x for x in dates if any(rr['f12b'] is not None for rr in by[x])]
bt = {}
for h, ov, ds in (('4 weeks', 4, ds4), ('12 weeks', 12, ds12)):
    k = 'f4b' if ov == 4 else 'f12b'
    a = summ(comp_ic(W, k, 'universe', ds), ov); c = summ(comp_ic({'ev_comp': 1}, k, 'universe', ds), ov); sp, hit = spread(W, k, ds)
    bt[h] = {'ic': round(a['ic'], 3), 't': round(a['t'], 1), 'hit': round(a['hit'], 2), 'spread_pct': round(sp * 100, 1), 'spread_hit': round(hit, 2), 'old_ic': round(c['ic'], 3), 'dates': f"{ds[0]} to {ds[-1]}"}
ICS = json.load(open('ic_results.json'))
sig = {s: {'ic4': round(ICS['f4b_universe'][s]['ic'], 3), 't4': round(ICS['f4b_universe'][s]['t'], 1), 'ic12': round(ICS['f12b_universe'][s]['ic'], 3), 't12': round(ICS['f12b_universe'][s]['t'], 1)} for s in ICS['f4b_universe'] if ICS['f4b_universe'][s] and ICS['f12b_universe'].get(s)}
doc = {'as_of': d, 'version': 'signal-score v1 (2026-11-13)', 'weights': W, 'groups': GROUP, 'scores': out, 'backtest': bt, 'signals': sig,
       'oos_note': 'Walk-forward test (weights refit each week from returns already known): out-of-sample IC about 0.00 over 2026-07-24 to 2026-10-16. Treat as a starting point and re-test monthly.',
       'universe': f"{len(rows)} Tier 1-2 names with prices"}
json.dump(doc, open('stock_scores_latest.json', 'w'))
top = sorted(out, key=lambda x: -x['score'])
print(d, len(out)); print('top', [(x['t'], x['score']) for x in top[:10]]); print('bottom', [(x['t'], x['score']) for x in top[-10:]]); print(bt)
