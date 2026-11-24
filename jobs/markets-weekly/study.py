"""Predictive study + current scorecard.

Reads data/panel.csv (+ data/sector_tr_monthly.csv) and writes:
  data/study.json      per-signal backtest stats (market direction, cyclicals vs defensives)
  data/scorecard.json  latest reading of every indicator with status, percentile, changes and call-outs
Run with: python3 -I study.py
"""
import json, pathlib, math
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
D = pd.read_csv(ROOT / 'data' / 'panel.csv', parse_dates=['month'], index_col='month')
TR = pd.read_csv(ROOT / 'data' / 'sector_tr_monthly.csv', parse_dates=['month'], index_col='month') if (ROOT / 'data' / 'sector_tr_monthly.csv').exists() else pd.DataFrame()

def col(name):
    return D[name] if name in D else pd.Series(np.nan, index=D.index)

S = col('SPX')
# ---------------------------------------------------------------- derived signals (value, bullish-when rule)
sig = {}
def add(key, value, bull, label, group, desc, invert_for_ic=False):
    sig[key] = dict(v=value, bull=bull, label=label, group=group, desc=desc)

add('trend10', S / S.rolling(10).mean() - 1, lambda x: x > 0, 'S&P vs 10-month average', 'Trend & breadth',
    'Price above its 10-month moving average (the Faber trend rule).')
add('mom12', S.pct_change(12), lambda x: x > 0, 'S&P 12-month momentum', 'Trend & breadth', '12-month price change above zero.')
curve = (col('UST10Y') - col('UST3M')).combine_first(col('UST10Y') - col('FED_FUNDS'))
add('curve', curve, lambda x: x > 0, 'Yield curve (10y - 3m)', 'Rates & policy',
    '10-year minus 3-month Treasury (10y minus fed funds before 1982). Inverted = bearish with a long lead.')
uninv = (curve > 0) & (curve.rolling(12).min() < 0)
add('curve_resteep', (~uninv).astype(float).where(curve.notna()), lambda x: x > 0.5, 'Curve not re-steepening from inversion', 'Rates & policy',
    'Bearish when the curve has turned positive within 12 months of being inverted (the classic late-cycle sequence).')
ic3 = col('INIT_CLAIMS').rolling(3).mean()
add('claims', ic3 / ic3.rolling(12).min() - 1, lambda x: x < 0.10, 'Initial claims vs 12-month low', 'Labor',
    '3-month average claims less than 10% above their 12-month low.')
ur3 = col('UNEMP_RATE').rolling(3).mean()
add('sahm', ur3 - col('UNEMP_RATE').rolling(12).min(), lambda x: x < 0.5, 'Unemployment vs 12-month low (Sahm)', 'Labor',
    '3-month average unemployment rate less than 0.5pt above its 12-month low.')
add('nfp3', col('NFP_CHG').rolling(3).mean(), lambda x: x > 0, 'Payrolls, 3-month average change', 'Labor', 'Average monthly job gains above zero.')
ism = col('ISM_BLEND')
add('ism', ism, lambda x: x > 50, 'ISM manufacturing (level)', 'Growth', 'ISM above 50. After Jul-2018 a regional-Fed proxy until the Bloomberg series is refreshed.')
add('ism_chg', ism - ism.shift(6), lambda x: x > 0, 'ISM manufacturing, 6-month change', 'Growth', 'ISM higher than six months ago.')
emp = col('EMPIRE_GEN').rolling(3).mean()
add('empire_chg', emp - emp.shift(6), lambda x: x > 0, 'Empire State survey, 6-month change', 'Growth', '3-month average Empire State conditions higher than six months ago.')
add('capex', col('CORE_CAPEX_ORD_YOY'), lambda x: x > 0, 'Core capex orders y/y', 'Growth', 'Non-defense capital goods ex aircraft orders (3mma) up y/y.')
add('ipm', col('IP_MFG_YOY'), lambda x: x > 0, 'Manufacturing output y/y', 'Growth', 'Manufacturing industrial production up y/y.')
add('permits', col('BUILDING_PERMITS').rolling(3).mean().pct_change(12), lambda x: x > 0, 'Building permits y/y', 'Housing', 'Permits (3mma) up y/y; housing leads the cycle.')
add('nahb', col('NAHB'), lambda x: x > 50, 'NAHB builder sentiment', 'Housing', 'Builder sentiment above 50.')
add('ff12', col('FED_FUNDS') - col('FED_FUNDS').shift(12), lambda x: x <= 0, 'Fed funds, 12-month change', 'Rates & policy', 'Fed not tightening (funds rate flat or lower vs a year ago).')
add('realff', col('FED_FUNDS') - col('CORE_CPI_YOY'), lambda x: x < 1.5, 'Real fed funds (vs core CPI)', 'Rates & policy', 'Policy not restrictive: real funds rate below 1.5%.')
add('y10chg', col('UST10Y') - col('UST10Y').shift(6), lambda x: x < 0.75, '10-year yield, 6-month change', 'Rates & policy', 'No rate shock: 10y up less than 75bp in six months.')
add('cpi_chg', col('CORE_CPI_YOY') - col('CORE_CPI_YOY').shift(6), lambda x: x <= 0, 'Core CPI, 6-month change', 'Inflation', 'Core inflation flat or falling.')
add('cpi', col('CPI_YOY'), lambda x: x < 4, 'Headline CPI y/y', 'Inflation', 'Headline inflation below 4%.')
um = col('UMICH_SENT')
add('umich', (um - um.rolling(120, min_periods=60).mean()) / um.rolling(120, min_periods=60).std(), lambda x: x < -1, 'Consumer sentiment (contrarian)', 'Sentiment',
    'Michigan sentiment more than 1 s.d. below its 10-year average: historically a contrarian buy.')
erp = 100 / col('SPX_FWD_PE') - col('UST10Y')
add('erp', erp, lambda x: x > 2, 'Equity risk premium (fwd E/P - 10y)', 'Valuation', 'Forward earnings yield more than 2pt above the 10-year (1990-2018; needs Bloomberg refresh).')
add('fwdpe', col('SPX_FWD_PE'), lambda x: x < 17, 'S&P forward P/E', 'Valuation', 'Forward P/E below 17x.')
add('m2', col('M2_YOY'), lambda x: x > 3, 'M2 money supply y/y', 'Credit & liquidity', 'M2 growth above 3%.')
add('ci', col('CI_LOANS_YOY'), lambda x: x > 0, 'Bank C&I loans y/y', 'Credit & liquidity', 'Business lending growing.')
if 'PX_HYG' in D and 'PX_IEF' in D:
    r = D['PX_HYG'] / D['PX_IEF']
    add('credit', r / r.rolling(6).mean() - 1, lambda x: x > 0, 'High yield vs Treasuries (HYG/IEF trend)', 'Credit & liquidity', 'HYG/IEF above its 6-month average: credit confirming.')
if 'PX_RSP' in D and 'PX_SPY' in D:
    r = D['PX_RSP'] / D['PX_SPY']
    add('breadth', r / r.shift(6) - 1, lambda x: x > 0, 'Equal-weight vs cap-weight S&P (6m)', 'Trend & breadth', 'RSP outperforming SPY over six months: broad participation.')

# ---------------------------------------------------------------- forward targets
fwd6 = S.shift(-6) / S - 1
fwd12 = S.shift(-12) / S - 1
fmin = pd.concat([S.shift(-k) for k in range(1, 13)], axis=1).min(axis=1)
dd12 = (fmin / S - 1) < -0.15                      # a 15%+ fall at some month-end in the next 12 months
dd12 = dd12.where(S.shift(-12).notna())

CYC, DEF = ['XLY-US', 'XLI-US', 'XLB-US', 'XLF-US', 'XLE-US'], ['XLP-US', 'XLU-US', 'XLV-US']
rot_fwd6 = None
if not TR.empty and all(c in TR for c in CYC + DEF):
    cyc = (1 + TR[CYC].mean(axis=1)).cumprod(); dfn = (1 + TR[DEF].mean(axis=1)).cumprod()
    rel = (cyc / dfn).reindex(D.index)
    rot_fwd6 = rel.shift(-6) / rel - 1
    rot_fwd3 = rel.shift(-3) / rel - 1
    add('rotmom', rel / rel.shift(6) - 1, lambda x: x > 0, 'Cyclicals vs defensives, 6m momentum', 'Trend & breadth', 'Cyclicals outperforming defensives over six months.')
    D['CYC_DEF_REL'] = rel

def stats(v, bull, target, dd=None):
    ok = v.notna() & target.notna()
    if ok.sum() < 36: return None
    x, y = v[ok], target[ok]
    b = bull(x)
    ic = x.rank().corr(y.rank())
    o = dict(n=int(ok.sum()), start=str(x.index.min().date())[:7], ic=round(float(ic), 3),
             bull_share=round(float(b.mean()), 3),
             bull_avg=round(float(y[b].mean()) * 100, 2) if b.any() else None,
             bear_avg=round(float(y[~b].mean()) * 100, 2) if (~b).any() else None,
             bull_hit=round(float((y[b] > 0).mean()), 3) if b.any() else None,
             bear_hit=round(float((y[~b] > 0).mean()), 3) if (~b).any() else None)
    o['spread'] = round(o['bull_avg'] - o['bear_avg'], 2) if o['bull_avg'] is not None and o['bear_avg'] is not None else None
    # crude significance: difference in means over SE using effective n = n/horizon overlap
    if b.sum() > 12 and (~b).sum() > 12:
        h = 12 if target is fwd12 else 6
        se = math.sqrt(y[b].var() / max(1, b.sum() / h) + y[~b].var() / max(1, (~b).sum() / h))
        o['t'] = round(float((y[b].mean() - y[~b].mean()) / se), 2) if se > 0 else None
    if dd is not None:
        okd = ok & dd.notna(); bb = bull(v[okd]); dz = dd[okd].astype(bool)
        o['bull_dd'] = round(float(dz[bb].mean()), 3) if bb.any() else None
        o['bear_dd'] = round(float(dz[~bb].mean()), 3) if (~bb).any() else None
    return o

study = {'market': {}, 'rotation': {}}
for k, s in sig.items():
    m = stats(s['v'], s['bull'], fwd12, dd12)
    if m:
        m6 = stats(s['v'], s['bull'], fwd6); m['bull_avg6'] = m6['bull_avg'] if m6 else None; m['bear_avg6'] = m6['bear_avg'] if m6 else None
        study['market'][k] = m
    if rot_fwd6 is not None:
        r = stats(s['v'], s['bull'], rot_fwd6)
        if r: study['rotation'][k] = r

# ---------------------------------------------------------------- composites
# Evidence-based sets (see data/study.json). Market = drawdown-risk regime; rotation = (key, invert) pairs where
# invert=True means the signal's "bear" state is the cyclical-friendly one (contrarian: buy cyclicals out of weakness).
MARKET_SET = [('trend10', False), ('curve', False), ('claims', False), ('credit', False), ('permits', False), ('cpi_chg', False), ('fwdpe', False)]
ROT_SET = [('ism_chg', False), ('empire_chg', False), ('cpi_chg', False), ('claims', True), ('ism', True), ('umich', False)]
def composite(pairs):
    cols = {}
    for k, inv in pairs:
        if k not in sig: continue
        v = sig[k]['v']; b = sig[k]['bull'](v).astype(float).where(v.notna())
        # a signal whose data stopped more than 3 months ago does not vote
        last = v.last_valid_index()
        if last is not None and (D.index.max() - last).days > 100: b = b.where(b.index <= last)
        cols[k] = (1 - b) if inv else b
    votes = pd.concat(cols, axis=1).ffill(limit=3)   # monthly releases lag; carry a reading up to 3 months
    return (votes.mean(axis=1) * 2 - 1).where(votes.notna().sum(axis=1) >= 3), votes
mkt_score, mkt_votes = composite(MARKET_SET)
rot_score, rot_votes = composite(ROT_SET)
def bucket_table(score, target):
    out = []
    for lo, hi, nm in [(-1.01, -0.33, 'Bearish'), (-0.33, 0.34, 'Neutral'), (0.34, 1.01, 'Bullish')]:
        m = score.between(lo, hi, inclusive='right') & target.notna()
        if m.sum(): out.append(dict(bucket=nm, n=int(m.sum()), avg=round(float(target[m].mean()) * 100, 2), hit=round(float((target[m] > 0).mean()), 3)))
    return out
study['composite'] = {'market_keys': [k for k, _ in MARKET_SET], 'rotation_keys': [[k, inv] for k, inv in ROT_SET],
                      'market_buckets_fwd12': bucket_table(mkt_score, fwd12),
                      'market_buckets_dd': [dict(bucket=b['bucket']) for b in bucket_table(mkt_score, fwd12)],
                      'rotation_buckets_fwd6': bucket_table(rot_score, rot_fwd6) if rot_fwd6 is not None else []}
for b in study['composite']['market_buckets_dd']:
    lo, hi = {'Bearish': (-1.01, -0.33), 'Neutral': (-0.33, 0.34), 'Bullish': (0.34, 1.01)}[b['bucket']]
    m = mkt_score.between(lo, hi, inclusive='right') & dd12.notna()
    b['dd_freq'] = round(float(dd12[m].astype(bool).mean()), 3) if m.sum() else None
D['MKT_SCORE'] = mkt_score; D['ROT_SCORE'] = rot_score

# ---------------------------------------------------------------- scorecard (latest reading per signal)
def pct_rank(series, val):
    s = series.dropna(); return round(float((s < val).mean() * 100), 0) if len(s) and val is not None else None
card = []
for k, s in sig.items():
    v = s['v'].dropna()
    if v.empty: continue
    last_d, last = v.index[-1], float(v.iloc[-1])
    def ago(n):
        w = v[v.index <= last_d - pd.offsets.MonthEnd(n)]; return float(w.iloc[-1]) if len(w) else None
    bull_now = bool(s['bull'](pd.Series([last])).iloc[0])
    prev = ago(1); bull_prev = bool(s['bull'](pd.Series([prev])).iloc[0]) if prev is not None else None
    stale = (D.index.max() - last_d).days > 75
    card.append(dict(key=k, label=s['label'], group=s['group'], desc=s['desc'], date=str(last_d.date())[:7], value=round(last, 4),
                     m1=prev, m3=ago(3), m6=ago(6), m12=ago(12), pct=pct_rank(s['v'], last), state='bull' if bull_now else 'bear',
                     flipped=(bull_prev is not None and bull_prev != bull_now), stale=stale,
                     mkt=study['market'].get(k), rot=study['rotation'].get(k)))
json.dump(study, open(ROOT / 'data' / 'study.json', 'w'), indent=1, default=str)
json.dump({'asof': str(D.index.max().date()), 'signals': card,
           'mkt_score': None if mkt_score.dropna().empty else round(float(mkt_score.dropna().iloc[-1]), 3),
           'rot_score': None if rot_score.dropna().empty else round(float(rot_score.dropna().iloc[-1]), 3),
           'mkt_votes': {k: (None if pd.isna(x) else bool(x)) for k, x in mkt_votes.ffill(limit=3).iloc[-1].items()},
           'rot_votes': {k: (None if pd.isna(x) else bool(x)) for k, x in rot_votes.ffill(limit=3).iloc[-1].items()}},
          open(ROOT / 'data' / 'scorecard.json', 'w'), indent=1, default=str)
for k, x in sig.items(): D['SIG_' + k] = x['v']
D.to_csv(ROOT / 'data' / 'panel_scored.csv', index_label='month')
# print a readable summary
rows = sorted(study['market'].items(), key=lambda kv: -(kv[1].get('spread') or -99))
print('MARKET (fwd 12m S&P price return)')
print(f"{'signal':16s} {'n':>4s} {'from':>8s} {'IC':>6s} {'bull%':>6s} {'bullAvg':>8s} {'bearAvg':>8s} {'spread':>7s} {'t':>5s} {'ddBull':>6s} {'ddBear':>6s}")
for k, m in rows:
    print(f"{k:16s} {m['n']:4d} {m['start']:>8s} {m['ic']:6.2f} {m['bull_share']*100:6.0f} {m['bull_avg'] or 0:8.1f} {m['bear_avg'] or 0:8.1f} {m['spread'] or 0:7.1f} {m.get('t') or 0:5.1f} {(m.get('bull_dd') or 0)*100:6.0f} {(m.get('bear_dd') or 0)*100:6.0f}")
if study['rotation']:
    print('\nROTATION (fwd 6m cyclicals minus defensives, total return)')
    for k, m in sorted(study['rotation'].items(), key=lambda kv: -(kv[1].get('spread') or -99)):
        print(f"{k:16s} {m['n']:4d} {m['start']:>8s} {m['ic']:6.2f} {m['bull_share']*100:6.0f} {m['bull_avg'] or 0:8.1f} {m['bear_avg'] or 0:8.1f} {m['spread'] or 0:7.1f} {m.get('t') or 0:5.1f}")
print('\nCOMPOSITE', json.dumps(study['composite'], indent=0))
