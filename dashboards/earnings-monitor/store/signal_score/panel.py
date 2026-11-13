#!/usr/bin/env python3
"""Point-in-time weekly signal panel + forward returns for the Stocks universe (6-month backtest)."""
import json, math, re, statistics as st
from collections import defaultdict
from datetime import date, timedelta

cs = [c for c in json.load(open('companies.json')) if c.get('fs')]
P = json.load(open('prices_w.json'))            # fs -> {date: [price, turnover]}
E = json.load(open('est_w.json'))               # metric -> fs -> {date: [mean, up, down, n]}
PT = json.load(open('pt.json'))                 # fs -> {month date: mean target}
SUR = json.load(open('surprise.json'))
INS = json.load(open('insiders.json'))
EV = json.load(open('evidence.json'))           # [id, rid, event_date, key, impact, conf, stype, psrc, created]

D = lambda s: date.fromisoformat(s[:10])
def ser(m):  # sorted list of (date, value)
    return sorted((D(k), v) for k, v in m.items())
def asof(sr, t):
    v = None
    for d, x in sr:
        if d > t: break
        v = x
    return v
def asof_d(sr, t):
    v = None
    for d, x in sr:
        if d > t: break
        v = (d, x)
    return v

px = {c['fs']: ser({k: v[0] for k, v in P.get(c['fs'], {}).items()}) for c in cs}
to = {c['fs']: ser({k: v[1] for k, v in P.get(c['fs'], {}).items() if v[1]}) for c in cs}
eps = {c['fs']: ser({k: v[0] for k, v in E['EPS'].get(c['fs'], {}).items()}) for c in cs}
sal = {c['fs']: ser({k: v[0] for k, v in E['SALES'].get(c['fs'], {}).items()}) for c in cs}
ptg = {c['fs']: ser(PT.get(c['fs'], {})) for c in cs}
sur = defaultdict(list)
for s in SUR: sur[(s['requestId'], s['metric'])].append((D(s['surpriseDate']), s['surprisePercent']))
for k in sur: sur[k].sort()
ins = defaultdict(list)
for r in INS:
    try: v = float(r['value'] or 0)
    except: v = 0
    ins[r['ticker']].append((D(r['datefiled']), r['code'], r['insider'], r['has_10b5'] == 'True', abs(v), r['pos_type']))

# evidence (pillar, signal, reliability) per research id
CONF = {"high": 1.0, "medium": 0.75, "low": 0.5}
REL = {"company": 1.0, "independent_research": 1.0, "sell_side": 0.6, "news": 0.5, "substack": 0.5, "email": 0.5, "evernote": 0.6, "fintool": 0.5, "twitter": 0.3, "reddit": 0.2}
CHANNEL = re.compile(r"semianalysis|cleveland|\bbwg\b|trendforce|\bidc\b|counterpoint|gartner|expert call|third bridge|guidepoint|tegus|digitimes|sensor tower|yipit|channel check|supply chain check|distributor|bluefin|edgewater", re.I)
GUIDE = re.compile(r"management|earnings call|transcript|\bir\b|investor day|analyst day|\bcfo\b|\bceo\b|10-k|10-q|8-k|press release|filing|guidance", re.I)
INFER = re.compile(r"inferred|extrapolat|triangulat|speculat", re.I)
def pillar(k):
    k = (k or '').lower()
    for p, pre in (('g', 'growth'), ('g', 'tam'), ('m', 'margin'), ('k', 'competition'), ('r', 'risk'), ('s', 'shareholder')):
        if k.startswith(pre): return p
    return None
def bucket(st_, p):
    if INFER.search(p): return 'infer', 0.3
    if CHANNEL.search(p): return 'channel', 1.0
    if GUIDE.search(p) or st_ == 'company': return 'mgmt', 1.0
    if st_ == 'sell_side': return 'sell', 0.6
    if st_ in ('twitter', 'reddit'): return 'social', REL.get(st_, 0.3)
    return 'other', REL.get(st_, 0.5)
evr = defaultdict(list)
for i, rid, ed, k, imp, conf, stp, ps, cr in EV:
    p = pillar(k)
    sgn = {'positive': 1, 'negative': -1}.get(imp, 0)
    b, rel = bucket(stp, ps)
    evr[int(rid)].append((D(ed), D(cr), p, sgn, CONF.get(conf, 0.75), b, rel))
for k in evr: evr[k].sort()

PW = {'g': .40, 'm': .25, 'k': .20, 'r': .15}
def ev_feats(rids, t, avail='event'):
    xs = [x for r in rids for x in evr.get(r, []) if (x[0] if avail == 'event' else max(x[0], x[1])) <= t]
    acc = {p: [0.0, 0.0] for p in PW}
    f = {}
    n90 = n30 = 0; flow30 = 0.0; neg30 = 0; bsum = defaultdict(lambda: [0.0, 0.0])
    for d, cr, p, s, c, b, rel in xs:
        age = (t - d).days
        w = rel * 0.5 ** (age / 90)
        if p in PW: acc[p][0] += s * c * w; acc[p][1] += w
        if age <= 90:
            n90 += 1
            bsum[b][0] += s * c; bsum[b][1] += 1
        if age <= 30:
            n30 += 1; flow30 += s * c * rel; neg30 += s < 0
    comp = 0
    for p, (sw, w) in acc.items():
        v = (sw / w if w else 0) * w / (w + 5)
        f['ev_' + p] = v * 100; comp += PW[p] * v
    f['ev_comp'] = comp * 100
    f['ev_n90'] = math.log1p(n90)
    f['ev_flow30'] = flow30 / math.sqrt(n30) if n30 else 0.0
    f['ev_neg30'] = neg30 / n30 if n30 >= 3 else None
    for b in ('sell', 'channel', 'mgmt', 'social'):
        sw, n = bsum[b]
        f['ev_' + b] = (sw / n) * n / (n + 3) if n else 0.0
    return f

def pct(a, b):
    return None if a is None or b is None or b == 0 else a / b - 1

def feats(c, t):
    fs = c['fs']; tk = c['fs'][:-3] if c['fs'].endswith('-US') else None
    p0 = asof(px[fs], t)
    if not p0: return None
    f = {}
    p4, p12, p26, p52 = (asof(px[fs], t - timedelta(weeks=w)) for w in (4, 12, 26, 52))
    f['mom1'] = pct(p0, p4); f['mom3'] = pct(p0, p12)
    f['mom6x1'] = pct(p4, p26)
    hi = max([x for d, x in px[fs] if t - timedelta(weeks=52) < d <= t] or [p0])
    f['dist_hi'] = p0 / hi - 1
    rets = [math.log(b / a) for (da, a), (db, b) in zip(px[fs], px[fs][1:]) if t - timedelta(weeks=12) < db <= t and a and b]
    f['vol12'] = st.pstdev(rets) if len(rets) > 5 else None
    tv = [x for d, x in to[fs] if t - timedelta(weeks=8) < d <= t]
    f['size'] = math.log(sum(tv) / len(tv)) if tv else None
    e0, e4, e12 = asof(eps[fs], t), asof(eps[fs], t - timedelta(weeks=4)), asof(eps[fs], t - timedelta(weeks=12))
    s0, s4, s12 = asof(sal[fs], t), asof(sal[fs], t - timedelta(weeks=4)), asof(sal[fs], t - timedelta(weeks=12))
    f['rev_eps4'] = (e0 - e4) / abs(e4) if e0 is not None and e4 not in (None, 0) else None
    f['rev_eps12'] = (e0 - e12) / abs(e12) if e0 is not None and e12 not in (None, 0) else None
    f['rev_sales4'] = pct(s0, s4); f['rev_sales12'] = pct(s0, s12)
    f['ey'] = e0 / p0 if e0 is not None else None          # earnings yield (value)
    sh = None
    f['pt_up'] = pct(asof(ptg[fs], t), p0)
    for m, k in (('SALES', 'sur_sales'), ('EPS', 'sur_eps')):
        v = asof_d(sur.get((fs, m), []), t)
        f[k] = max(-50, min(50, v[1])) if v and (t - v[0]).days <= 95 else None
    if tk:
        xs = [x for x in ins.get(tk, []) if t - timedelta(days=90) < x[0] <= t]
        f['ins_sellers_np'] = len({x[2] for x in xs if x[1] == 'Sale' and not x[3]})
        f['ins_sellers'] = len({x[2] for x in xs if x[1] == 'Sale'})
        f['ins_buyers'] = len({x[2] for x in xs if x[1] == 'Buy'})
        f['ins_csuite_np'] = len({x[2] for x in xs if x[1] == 'Sale' and not x[3] and x[5] in ('CEO', 'CFO')})
    f.update(ev_feats(c.get('rids') or [], t))
    return f

def fwd(c, t, w):
    a, b = asof(px[c['fs']], t), asof(px[c['fs']], t + timedelta(weeks=w))
    return pct(b, a)

dates = []
d = date(2026, 5, 8)
while d <= date(2026, 11, 13):
    dates.append(d); d += timedelta(weeks=1)
rows = []
for t in dates:
    for c in cs:
        f = feats(c, t)
        if not f: continue
        f.update({'t': c['t'], 'fs': c['fs'], 'date': t.isoformat(), 'sector': c['sector'], 'sub': (c.get('subs') or [c.get('sub')])[0], 'tier': c['tier'],
                  'f4': fwd(c, t, 4) if t + timedelta(weeks=4) <= date(2026, 11, 13) else None,
                  'f12': fwd(c, t, 12) if t + timedelta(weeks=12) <= date(2026, 11, 13) else None})
        # robustness: evidence only once it was in Supabase
        g = ev_feats(c.get('rids') or [], t, avail='created')
        f['evc_comp'] = g['ev_comp']; f['evc_flow30'] = g['ev_flow30']
        rows.append(f)
json.dump(rows, open('panel.json', 'w'))
print(len(rows), 'rows', len(dates), 'dates', dates[0], dates[-1])

# ---- beta-adjusted forward returns (beta to the equal-weight universe, trailing 26 weeks)
import statistics as st2
allw = sorted({d for c in cs for d, _ in px[c['fs']]})
wk = {}
for c in cs:
    s = dict(px[c['fs']])
    wk[c['fs']] = {b: s[b] / s[a] - 1 for a, b in zip(allw, allw[1:]) if a in s and b in s and s[a]}
mkt = {}
for d in allw[1:]:
    v = [wk[f][d] for f in wk if d in wk[f]]
    if len(v) > 30: mkt[d] = st2.median(v)
def beta(fs, t):
    xs = [(mkt[d], wk[fs][d]) for d in allw if t - timedelta(weeks=26) < d <= t and d in mkt and d in wk[fs]]
    if len(xs) < 12: return None
    mx = st2.mean(x for x, _ in xs); my = st2.mean(y for _, y in xs)
    vx = sum((x - mx) ** 2 for x, _ in xs)
    return sum((x - mx) * (y - my) for x, y in xs) / vx if vx else None
def mfwd(t, w):
    r = 1.0
    for d in allw:
        if t < d <= t + timedelta(weeks=w) and d in mkt: r *= 1 + mkt[d]
    return r - 1
for f in rows:
    t = date.fromisoformat(f['date']); b = beta(f['fs'], t)
    f['beta'] = b
    for h, w in (('f4', 4), ('f12', 12)):
        f[h + 'b'] = None if f[h] is None or b is None else f[h] - b * mfwd(t, w)
json.dump(rows, open('panel.json', 'w'))
print('beta added', sum(1 for f in rows if f['beta'] is not None))
