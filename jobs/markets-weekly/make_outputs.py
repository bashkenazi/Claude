"""Turn the panel + study into (1) page-database docs for the Markets tab and (2) Supabase load SQL.

Inputs : data/panel_scored.csv, data/scorecard.json, data/study.json, data/factset_raw/px_d_*.json,
         data/pagedb/technicals/breadth.json (read from the page db before running), data/pagedb/markets/summary.json (previous run, optional)
Outputs: out/pagedb/*.json          one file per markets/<doc> (each < 256 KiB)
         out/sql/*.sql              idempotent upserts for macro_series, macro_observations, market_*_snapshots
Run with: python3 -I make_outputs.py [--asof YYYY-MM-DD]
"""
import json, glob, math, os, sys, pathlib, datetime as dt
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / 'out'; (OUT / 'pagedb').mkdir(parents=True, exist_ok=True); (OUT / 'sql').mkdir(parents=True, exist_ok=True)
ASOF = sys.argv[sys.argv.index('--asof') + 1] if '--asof' in sys.argv else dt.date.today().isoformat()

P = pd.read_csv(ROOT / 'data' / 'panel_scored.csv', parse_dates=['month'], index_col='month')
CARD = json.load(open(ROOT / 'data' / 'scorecard.json'))
STUDY = json.load(open(ROOT / 'data' / 'study.json'))
PREV = None
if (ROOT / 'data' / 'pagedb' / 'markets' / 'summary.json').exists():
    PREV = json.load(open(ROOT / 'data' / 'pagedb' / 'markets' / 'summary.json')); PREV = PREV.get('data', PREV)

# ------------------------------------------------------------------ series registry (Supabase macro_series + chart picker)
BBG, FS = 'Bloomberg Market historicals CSV', 'FactSet'
REG = {
 'SPX': ('S&P 500', 'Markets', 'index', f'{BBG} SPX Index to 2018-07; SPY (FactSet) rescaled to SPX after'),
 'MSCI_WORLD': ('MSCI World', 'Markets', 'index', f'{BBG} MXWO Index (history only)'),
 'UST10Y': ('10-year Treasury yield', 'Rates & policy', '%', f'{BBG} GT10 Govt to 2018-07; {FS} FRBRIFLGFCY10@US (monthly avg) after'),
 'UST2Y': ('2-year Treasury yield', 'Rates & policy', '%', f'{FS} FRBRIFLGFCY02@US'),
 'UST3M': ('3-month Treasury yield', 'Rates & policy', '%', f'{FS} FRBRIFLGFCM03@US'),
 'UST5Y': ('5-year Treasury yield', 'Rates & policy', '%', f'{BBG} USGG5YR; {FS} FRBRIFLGFCY05@US after'),
 'FED_FUNDS': ('Effective fed funds rate', 'Rates & policy', '%', f'{FS} FRBRIFSPFF@US'),
 'FED_FUNDS_UPPER': ('Fed funds target (upper)', 'Rates & policy', '%', f'{BBG} FDTR; {FS} ITONMAXD@US after'),
 'REAL10Y': ('10-year TIPS real yield', 'Rates & policy', '%', f'{FS} FRBRIFLGFCIIY10@US'),
 'BE10Y': ('10-year breakeven inflation', 'Inflation', '%', f'{FS} USIR6389706'),
 'FWD5Y5Y_BE': ('5y5y forward breakeven', 'Inflation', '%', f'{FS} USIR1578126'),
 'FED_ASSETS': ('Fed total assets', 'Credit & liquidity', '$mm', f'{BBG} FARBAST; {FS} US.CBASSET after'),
 'UNEMP_RATE': ('Unemployment rate', 'Labor', '%', f'{BBG} EHUPUS; {FS} US.LMUEMPR after'),
 'INIT_CLAIMS': ('Initial jobless claims (monthly avg)', 'Labor', 'k', f'{BBG} INJCJC to 2017-06; {FS} DOLICLAIMUI@US after'),
 'CONT_CLAIMS': ('Continuing claims (monthly avg)', 'Labor', 'k', f'{FS} US.LMCLAIMS'),
 'NFP_CHG': ('Payrolls, monthly change', 'Labor', 'k', f'{BBG} NFP TCH (total) to 2018-07; {FS} private payrolls USLM1012144 change after'),
 'AVG_WEEKLY_HOURS': ('Average weekly hours', 'Labor', 'hrs', f'{BBG} AWH TOTL; {FS} USLM2253126 after'),
 'AHE_YOY': ('Average hourly earnings y/y', 'Labor', '%', f'{BBG} AHE YOY%; {FS} US.LMWAGES after'),
 'JOLTS_OPENINGS': ('JOLTS job openings', 'Labor', 'k', f'{FS} US.LMVAC'),
 'CPI_YOY': ('CPI y/y', 'Inflation', '%', f'{FS} US.CPIALL'),
 'CORE_CPI_YOY': ('Core CPI y/y', 'Inflation', '%', f'{FS} US.CPICORE'),
 'CORE_PCE_YOY': ('Core PCE y/y', 'Inflation', '%', f'{FS} BEANIPABA03RG3@US'),
 'PPI_YOY': ('PPI y/y', 'Inflation', '%', f'{BBG} PPI YOY (history only)'),
 'PPI_CORE_YOY': ('Core PPI y/y', 'Inflation', '%', f'{BBG} PPI XYOY (history only)'),
 'ISM_MFG': ('ISM manufacturing PMI', 'Growth', 'index', f'{BBG} NAPMPMI (to 2018-07; refresh needed)'),
 'ISM_PROXY': ('ISM proxy from regional Fed surveys', 'Growth', 'index', f'Derived: OLS of ISM on Empire, Dallas, Kansas City surveys 2004-2018 ({FS})'),
 'ISM_BLEND': ('ISM manufacturing (actual to 2018-07, proxy after)', 'Growth', 'index', 'Derived'),
 'EMPIRE_GEN': ('Empire State manufacturing', 'Growth', 'diffusion', f'{FS} USSU0009518'),
 'EMPIRE_NEWORD': ('Empire State new orders', 'Growth', 'diffusion', f'{FS} USSU0009522'),
 'TX_MFG': ('Dallas Fed manufacturing', 'Growth', 'diffusion', f'{FS} USSU0587918'),
 'KC_MFG': ('Kansas City Fed manufacturing', 'Growth', 'diffusion', f'{FS} USSU1293726'),
 'GDP_YOY': ('Real GDP y/y', 'Growth', '%', f'{BBG} GDP CYOY (history only)'),
 'GDP_QOQ_SAAR': ('Real GDP q/q saar', 'Growth', '%', f'{BBG} GDP CQOQ (history only)'),
 'IP_MFG_YOY': ('Manufacturing production y/y', 'Growth', '%', f'{FS} US.INDPRODMG'),
 'CAP_UTIL': ('Capacity utilization', 'Growth', '%', f'{FS} FRBUTLB50001'),
 'CORE_CAPEX_ORD_YOY': ('Core capex orders y/y (3mma)', 'Growth', '%', f'{FS} CENANXANO'),
 'RETAIL_XAUTO_YOY': ('Retail sales ex autos y/y (3mma)', 'Growth', '%', f'{FS} CENRETAIL@MVP@US'),
 'INV_SALES': ('Business inventories/sales', 'Growth', 'ratio', f'{FS} US.INDINVR'),
 'UMICH_SENT': ('Michigan consumer sentiment', 'Sentiment', 'index', f'{BBG} CONSSENT; {FS} USSU0014446 after'),
 'HOUSING_STARTS': ('Housing starts', 'Housing', 'k saar', f'{BBG} NHSPSTOT; {FS} US.HCSTARTS after'),
 'BUILDING_PERMITS': ('Building permits', 'Housing', 'k saar', f'{FS} US.HCPERMIT'),
 'NEW_HOME_SALES': ('New home sales', 'Housing', 'k saar', f'{BBG} NHSLTOT; {FS} CENHSOLDTOT@US after'),
 'NAHB': ('NAHB builder sentiment', 'Housing', 'index', f'{FS} NAHBWFHMI'),
 'MORTGAGE30': ('30-year mortgage rate', 'Housing', '%', f'{BBG} ILM3NAVG (history only)'),
 'M2_YOY': ('M2 money supply y/y', 'Credit & liquidity', '%', f'{FS} US.MAM2'),
 'CI_LOANS_YOY': ('Bank C&I loans y/y', 'Credit & liquidity', '%', f'{FS} FRBBCABLCCBA@US'),
 'SLOOS_CI_TIGHTEN': ('SLOOS: % banks tightening C&I', 'Credit & liquidity', '%', f'{FS} USSU0486263 (quarterly)'),
 'SPX_FWD_PE': ('S&P 500 forward P/E', 'Valuation', 'x', f'{BBG} SPX BEST_PE_RATIO (to 2018-07; refresh needed)'),
 'NASDAQ_FWD_PE': ('Nasdaq forward P/E', 'Valuation', 'x', f'{BBG} CCMP BEST_PE_RATIO (to 2018-07)'),
 'CHINA_PMI': ('China PMI', 'Global', 'index', f'{BBG} CPMINDX (history only)'),
 'CHINA_FX_RESERVES': ('China FX reserves', 'Global', '$mm', f'{BBG} WIRACHIN (history only)'),
 'CHINA_TRADE_BAL': ('China trade balance', 'Global', '$bn', f'{BBG} CNFRCBAL (history only)'),
 'UK_CORE_CPI_YOY': ('UK core CPI y/y', 'Global', '%', f'{BBG} UKHCA9IQ (labelled US core CPI in the sheet; it is the UK series)'),
 'CYC_DEF_REL': ('Cyclicals / defensives (total return ratio)', 'Markets', 'ratio', f'Derived from {FS} total returns: XLY XLI XLB XLF XLE vs XLP XLU XLV, equal weight'),
 'MKT_SCORE': ('Market risk composite', 'Composite', '-1..+1', 'Derived (study.py)'),
 'ROT_SCORE': ('Rotation composite (cyclicals +)', 'Composite', '-1..+1', 'Derived (study.py)'),
}
ETF_NAMES = {'SPY': 'S&P 500 (SPY)', 'RSP': 'S&P 500 equal weight', 'QQQ': 'Nasdaq-100', 'IWM': 'Russell 2000', 'MDY': 'S&P 400 mid caps',
 'XLY': 'Consumer discretionary', 'XLI': 'Industrials', 'XLB': 'Materials', 'XLF': 'Financials', 'XLE': 'Energy', 'XLP': 'Consumer staples',
 'XLU': 'Utilities', 'XLV': 'Health care', 'XLK': 'Technology', 'SMH': 'Semiconductors', 'HYG': 'High yield bonds', 'LQD': 'IG corporate bonds',
 'IEF': '7-10y Treasuries', 'TLT': '20y+ Treasuries', 'GLD': 'Gold', 'UUP': 'US dollar', 'CPER': 'Copper', 'DBC': 'Commodities', 'EEM': 'Emerging markets',
 'EFA': 'Developed ex-US', 'SPHB': 'S&P high beta', 'SPLV': 'S&P low volatility', 'MTUM': 'Momentum factor', 'XHB': 'Homebuilders', 'KRE': 'Regional banks'}
for t, n in ETF_NAMES.items(): REG['PX_' + t] = (n + ' price', 'Markets', '$', f'{FS} {t}-US weekly close (month-end)')
CYC, DEF = ['XLY', 'XLI', 'XLB', 'XLF', 'XLE'], ['XLP', 'XLU', 'XLV']

def r4(x):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))): return None
    return float(f'{x:.4g}')

# ------------------------------------------------------------------ daily technicals (FactSet daily closes, last ~14 months)
def daily():
    fr = {}
    newd = sorted(glob.glob(str(ROOT / 'data' / 'factset_new' / 'px_d_*.json')))
    for p in newd or glob.glob(str(ROOT / 'data' / 'factset_raw' / 'px_d_*.json')):
        for r in json.load(open(p))['data']:
            if r.get('price') is not None: fr.setdefault(r['requestId'].replace('-US', ''), {})[r['date']] = r['price']
    return pd.DataFrame(fr).sort_index()
DLY = daily()
tech = {}
if not DLY.empty:
    last = DLY.ffill().iloc[-1]
    def ma(t, n): s = DLY[t].dropna(); return float(s.tail(n).mean()) if len(s) >= n else None
    rows = []
    for t in DLY.columns:
        s = DLY[t].dropna()
        if len(s) < 60: continue
        px = float(s.iloc[-1]); hi = float(s.tail(252).max())
        def ret(n): return r4((px / float(s.iloc[-n - 1]) - 1) * 100) if len(s) > n else None
        rows.append(dict(t=t, name=ETF_NAMES.get(t, t), px=r4(px), d50=r4((px / ma(t, 50) - 1) * 100) if ma(t, 50) else None,
                         d200=r4((px / ma(t, 200) - 1) * 100) if ma(t, 200) else None, off_hi=r4((px / hi - 1) * 100),
                         r1w=ret(5), r1m=ret(21), r3m=ret(63), r6m=ret(126), cyc=('cyc' if t in CYC else 'def' if t in DEF else '')))
    sect = [r for r in rows if r['t'] in CYC + DEF + ['XLK']]
    cyc_d = DLY[CYC].dropna().pipe(lambda x: x / x.iloc[0]).mean(axis=1); def_d = DLY[DEF].dropna().pipe(lambda x: x / x.iloc[0]).mean(axis=1)
    rel = (cyc_d / def_d).dropna()
    tech = dict(asof=str(DLY.dropna(how='all').index[-1]), etfs=rows,
                sectors_above_200=sum(1 for r in sect if (r['d200'] or 0) > 0), sectors_n=len(sect),
                rel_d=[[d[5:], r4(v)] for d, v in rel.items()][-260:],
                rel_vs50=r4((rel.iloc[-1] / rel.tail(50).mean() - 1) * 100), rel_vs200=r4((rel.iloc[-1] / rel.tail(200).mean() - 1) * 100) if len(rel) >= 200 else None,
                rel_3m=r4((rel.iloc[-1] / rel.iloc[-64] - 1) * 100) if len(rel) > 64 else None)

# ------------------------------------------------------------------ breadth from the Technicals tab's page doc
breadth = {}
bp = ROOT / 'data' / 'pagedb' / 'technicals' / 'breadth.json'
if bp.exists():
    b = json.load(open(bp)); b = b.get('data', b); d0 = dt.date.fromisoformat(b['d0'])
    for k, v in b['u'].items():
        off = v['o']; ds = [off]
        for ch in v['t']: off += int(ch, 36); ds.append(off)
        cum, best, bd, cums = 0, -1e18, 0, []
        for j, (a, c) in enumerate(zip(v['a'], v['c'])):
            cum += a - c; cums.append(cum)
            if cum >= best: best, bd = cum, j
        ix = v['i']; pk = max(range(len(ix)), key=lambda j: ix[j] or 0)
        f = lambda j: str(d0 + dt.timedelta(days=ds[j]))
        a10, c10 = sum(v['a'][-10:]), sum(v['c'][-10:])
        lead = (dt.date.fromisoformat(f(pk)) - dt.date.fromisoformat(f(bd))).days
        breadth[k] = dict(last=f(len(v['a']) - 1), ad_peak=f(bd), ix_peak=f(pk), lead=lead, ad_off=int(cums[-1] - best), g=v['g'],
                          ix_off=r4((ix[-1] / ix[pk] - 1) * 100) if ix[pk] else None, r10=r4(a10 / c10) if c10 else None,
                          div=bool(lead > 10 and (cums[-1] - best) / v['g'] < -0.03))
    breadth = {'built': b.get('built'), 'u': breadth}

# ------------------------------------------------------------------ call-outs
sig = {s['key']: s for s in CARD['signals']}
mb = {x['bucket']: x for x in STUDY['composite']['market_buckets_fwd12']}
dd = {x['bucket']: x['dd_freq'] for x in STUDY['composite']['market_buckets_dd']}
rb = {x['bucket']: x for x in STUDY['composite']['rotation_buckets_fwd6']}
def bucket(x): return None if x is None else 'Bearish' if x <= -0.33 else 'Bullish' if x > 0.33 else 'Neutral'
mkt, rot = CARD['mkt_score'], CARD['rot_score']
mvotes = {k: v for k, v in CARD['mkt_votes'].items() if v is not None}; rvotes = {k: v for k, v in CARD['rot_votes'].items() if v is not None}
rot_keys = {k: inv for k, inv in STUDY['composite']['rotation_keys']}
cyc_side = [k for k, v in rvotes.items() if v]; def_side = [k for k, v in rvotes.items() if not v]
lab = lambda k: sig[k]['label'] if k in sig else k
call = []
def C(kind, sev, title, body, keys=()): call.append(dict(kind=kind, sev=sev, title=title, body=body, keys=list(keys)))
mbk = bucket(mkt)
C('regime', 'pos' if mbk == 'Bullish' else 'neg' if mbk == 'Bearish' else 'warn',
  f"Macro risk regime: {mbk.lower()} ({sum(mvotes.values())} of {len(mvotes)} risk signals benign)",
  f"Since 1970, months in the {mbk.lower()} bucket were followed by a 15%+ S&P drawdown within 12 months {dd.get(mbk, 0)*100:.0f}% of the time "
  f"(bearish bucket: {dd.get('Bearish', 0)*100:.0f}%), with an average 12-month return of {mb[mbk]['avg']:.1f}%. "
  + (f"Not benign: {', '.join(lab(k) for k, v in mvotes.items() if not v)}." if not all(mvotes.values()) else "Every risk signal in the composite is benign."), list(mvotes))
rbk = bucket(rot)
lean = 'cyclicals' if rbk == 'Bullish' else 'defensives' if rbk == 'Bearish' else 'neither side decisively'
C('rotation', 'pos' if rbk == 'Bullish' else 'neg' if rbk == 'Bearish' else 'warn', f"Rotation: lean {lean} (score {rot:+.2f})",
  f"For cyclicals: {', '.join(lab(k) + (' (contrarian)' if rot_keys.get(k) else '') for k in cyc_side) or 'none'}. "
  f"For defensives: {', '.join(lab(k) + (' (contrarian)' if rot_keys.get(k) else '') for k in def_side) or 'none'}. "
  + (f"Since 2006 this bucket saw cyclicals beat defensives by {rb[rbk]['avg']:+.1f}% over the next 6 months on average ({rb[rbk]['hit']*100:.0f}% of the time)." if rbk in rb else ''),
  list(rvotes))
if tech and rbk in ('Bullish', 'Bearish') and tech.get('rel_3m') is not None:
    agree = (tech['rel_3m'] > 0) == (rbk == 'Bullish')
    call[-1]['body'] += (' Price action agrees: ' if agree else ' Price action does not confirm yet: ') + \
        f"cyclicals vs defensives {tech['rel_3m']:+.1f}% over 3 months and {tech['rel_vs50']:+.1f}% vs the 50-day."
    if not agree: call[-1]['sev'] = 'warn'
if tech:
    t = {r['t']: r for r in tech['etfs']}
    spy = t.get('SPY', {})
    sev = 'neg' if (spy.get('d200') or 0) < 0 else 'warn' if (spy.get('d50') or 0) < 0 else 'pos'
    C('technical', sev, f"S&P trend: {spy.get('d50', 0):+.1f}% vs 50-day, {spy.get('d200', 0):+.1f}% vs 200-day; {spy.get('off_hi', 0):.1f}% off its 52-week high",
      f"{tech['sectors_above_200']} of {tech['sectors_n']} sector SPDRs are above their 200-day average. Cyclicals vs defensives (daily, equal weight) is "
      f"{tech['rel_vs50']:+.1f}% vs its 50-day and {tech['rel_3m']:+.1f}% over 3 months.", ['trend10'])
if breadth.get('u'):
    u = breadth['u']; sp = u.get('S&P 500')
    divs = [k for k, v in u.items() if v['div']]
    if sp:
        C('breadth', 'neg' if sp['div'] else 'pos', f"Breadth: S&P 500 A/D line peaked {sp['ad_peak']}, index peaked {sp['ix_peak']}" + (f" ({sp['lead']} days later)" if sp['lead'] > 0 else ''),
          f"The A/D line has lost {abs(sp['ad_off']):,} net issues since its peak; 10-day A/D ratio {sp['r10']:.2f}x. "
          f"Small caps (S&P 600) {u.get('S&P 600 small', {}).get('r10', 0):.2f}x, mid caps {u.get('S&P 400 mid', {}).get('r10', 0):.2f}x. "
          f"{len(divs)} of {len(u)} markets show a lasting divergence: {', '.join(divs) or 'none'}. Breadth is tracked on the Technicals tab and is not in the backtested composite (history starts May 2025).", [])
for s in CARD['signals']:
    if s['stale']: continue
    if s['flipped']:
        C('flip', 'pos' if s['state'] == 'bull' else 'neg', f"Changed state: {s['label']} turned {'benign' if s['state'] == 'bull' else 'cautionary'}",
          s['desc'] + (f" Historically {s['mkt']['bull_avg']:.1f}% vs {s['mkt']['bear_avg']:.1f}% next-12m S&P return in the two states." if s.get('mkt') and s['mkt'].get('bull_avg') is not None else ''), [s['key']])
    elif s['pct'] is not None and (s['pct'] >= 92 or s['pct'] <= 8) and s['key'] not in ('curve_resteep',):
        C('extreme', 'warn', f"At an extreme: {s['label']} is at the {s['pct']:.0f}th percentile of its history", s['desc'], [s['key']])
stale = [s['label'] for s in CARD['signals'] if s['stale']]
if stale: C('gap', 'warn', 'Data gaps: ' + ', '.join(stale), 'These need the Bloomberg sheet refreshed (see Sources & gaps). They do not vote in the composites.', [])
if PREV:
    pm, pr = PREV.get('mkt_score'), PREV.get('rot_score')
    if pm is not None and pm != mkt: C('delta', 'warn', f"Market composite moved {pm:+.2f} → {mkt:+.2f} since {PREV.get('asof')}", '', [])
    if pr is not None and pr != rot: C('delta', 'warn', f"Rotation composite moved {pr:+.2f} → {rot:+.2f} since {PREV.get('asof')}", '', [])
sev_order = {'regime': 0, 'rotation': 1, 'breadth': 2, 'technical': 3, 'flip': 4, 'delta': 5, 'extreme': 6, 'gap': 7}
call.sort(key=lambda c: sev_order.get(c['kind'], 9))
headline = (f"Macro backdrop {mbk.lower()} for equities, rotation leans {lean}" +
            ("; breadth is diverging under the index" if breadth.get('u', {}).get('S&P 500', {}).get('div') else '') + '.')

# ------------------------------------------------------------------ page-db docs
def series_doc(cols):
    m0 = P.index.min(); out = {}
    for c in cols:
        if c not in P: continue
        s = P[c]; fv = s.first_valid_index()
        if fv is None: continue
        s = s.loc[fv:]; lv = s.last_valid_index(); s = s.loc[:lv]
        off = (fv.year - m0.year) * 12 + fv.month - m0.month
        nm, g, u, src = REG.get(c, (c, 'Other', '', ''))
        out[c] = dict(n=nm, g=g, u=u, o=off, v=[r4(x) for x in s.values])
    return dict(m0=str(m0.date())[:7], s=out)
sig_cols = {}
# derived signal series so every scorecard row can be charted
import importlib.util
macro_cols = [c for c in P.columns if not c.startswith(('PX_', 'SIG_'))]
sig_cols = [c for c in P.columns if c.startswith('SIG_')]
for s_ in CARD['signals']: REG.setdefault('SIG_' + s_['key'], (s_['label'], s_['group'], '', 'Derived signal (study.py)'))
px_cols = [c for c in P.columns if c.startswith('PX_')]
docs = {
 'summary': dict(asof=ASOF, data_through=CARD['asof'], headline=headline, mkt_score=mkt, rot_score=rot, mkt_bucket=mbk, rot_bucket=rbk,
                 mkt_votes=CARD['mkt_votes'], rot_votes=CARD['rot_votes'], callouts=call,
                 prev=dict(asof=PREV.get('asof'), mkt_score=PREV.get('mkt_score'), rot_score=PREV.get('rot_score')) if PREV else None,
                 signals=[{k: v for k, v in s.items()} for s in CARD['signals']],
                 composite=STUDY['composite'], technicals=tech, breadth=breadth,
                 registry={k: dict(n=v[0], g=v[1], u=v[2], src=v[3]) for k, v in REG.items() if k in P.columns},
                 ism_proxy=json.load(open(ROOT / 'data' / 'ism_proxy_fit.json')) if (ROOT / 'data' / 'ism_proxy_fit.json').exists() else None),
 'study': dict(asof=ASOF, market=STUDY['market'], rotation=STUDY['rotation'], composite=STUDY['composite']),
 'series_macro': series_doc(macro_cols),
 'series_px': series_doc(px_cols),
 'series_sig': series_doc(sig_cols),
}
for k, v in docs.items():
    s = json.dumps(v, separators=(',', ':'), default=str)
    (OUT / 'pagedb' / f'{k}.json').write_text(s)
    print(f'pagedb markets/{k}: {len(s)/1024:.0f} KiB')
    assert len(s) < 250 * 1024, f'{k} too large'

# ------------------------------------------------------------------ Supabase SQL
def q(x): return 'null' if x is None else "'" + str(x).replace("'", "''") + "'"
meta = []
for c in P.columns:
    if c not in REG or c.startswith('SIG_'): continue
    s = P[c].dropna()
    if s.empty: continue
    nm, g, u, src = REG[c]
    meta.append(f"({q(c)},{q(nm)},{q(g)},{q(u)},'M',{q(src)},{q(str(s.index.min().date()))},{q(str(s.index.max().date()))},now())")
(OUT / 'sql' / '01_series.sql').write_text(
    'insert into public.macro_series (series_id,name,category,units,frequency,sources,first_month,last_month,updated_at) values\n' + ',\n'.join(meta) +
    '\non conflict (series_id) do update set name=excluded.name, category=excluded.category, units=excluded.units, sources=excluded.sources, '
    'first_month=excluded.first_month, last_month=excluded.last_month, updated_at=now();\n')
since = '1900-01-01' if '--full' in sys.argv else (pd.Timestamp(ASOF) - pd.DateOffset(months=18)).strftime('%Y-%m-%d')
bbg = pd.read_csv(ROOT / 'data' / 'bbg_monthly.csv'); bbg_keys = set(zip(bbg.series_id, pd.to_datetime(bbg.month).dt.to_period('M').dt.to_timestamp('M')))
rows = []
for c in P.columns:
    if c not in REG: continue
    for d, v in P[c].dropna().items():
        if str(d.date()) < since: continue
        src = 'bloomberg_csv' if (c, d) in bbg_keys else 'derived' if REG[c][3].startswith('Derived') else 'factset'
        rows.append(f"({q(c)},'{d.date()}',{repr(float(v))},'{src}')")
for f in glob.glob(str(OUT / 'sql' / '02_obs_*.sql')): os.remove(f)
segs = []
for c in P.columns:
    if c not in REG or c.startswith('SIG_'): continue
    ser = P[c].dropna(); ser = ser[ser.index >= pd.Timestamp(since)]
    if ser.empty: continue
    cur = None
    for d, v in ser.items():
        src = 'bloomberg_csv' if (c, d) in bbg_keys else 'derived' if REG[c][3].startswith('Derived') else 'factset'
        mi = d.year * 12 + d.month - 1
        if cur and cur['src'] == src and mi == cur['m'] + len(cur['v']): cur['v'].append(float(f'{float(v):.6g}'))
        else:
            cur = dict(c=c, src=src, m=mi, v=[float(f'{float(v):.6g}')]); segs.append(cur)
chunks, buf, size = [], [], 0
for g in segs:
    t = f"({q(g['c'])},{g['m']},{q(g['src'])},'{json.dumps(g['v'], separators=(',', ':'))}'::jsonb)"
    if size + len(t) > 55000 and buf: chunks.append(buf); buf, size = [], 0
    buf.append(t); size += len(t)
if buf: chunks.append(buf)
for i, ch in enumerate(chunks):
    (OUT / 'sql' / f'02_obs_{i:03d}.sql').write_text(
        'insert into public.macro_observations (series_id,obs_month,value,source)\n'
        "select s.id, (make_date(s.m / 12, s.m % 12 + 1, 1) + ((e.i - 1) || ' month')::interval + interval '1 month' - interval '1 day')::date, e.x::text::float8, s.src\n"
        'from (values\n' + ',\n'.join(ch) + '\n) s(id, m, src, v), jsonb_array_elements(s.v) with ordinality e(x, i)\n'
        "where jsonb_typeof(e.x) = 'number'\n"
        'on conflict (series_id,obs_month) do update set value=excluded.value, source=excluded.source, loaded_at=now();\n')
snap = []
for s in CARD['signals']:
    snap.append(f"('{ASOF}',{q(s['key'])},'{s['date']}-01'::date + interval '1 month' - interval '1 day',{r4(s['value']) if s['value'] is not None else 'null'},"
                f"{q(s['state'])},{s['pct'] if s['pct'] is not None else 'null'},{'true' if s['stale'] else 'false'},{q(json.dumps({k: s[k] for k in ('m1','m3','m6','m12','flipped')}, default=str))}::jsonb)")
(OUT / 'sql' / '03_snapshots.sql').write_text(
    'insert into public.market_signal_snapshots (asof,signal_key,data_month,value,state,pct,stale,payload) values\n' + ',\n'.join(snap) +
    '\non conflict (asof,signal_key) do update set data_month=excluded.data_month, value=excluded.value, state=excluded.state, pct=excluded.pct, stale=excluded.stale, payload=excluded.payload;\n'
    f"insert into public.market_regime_snapshots (asof,mkt_score,rot_score,headline,callouts,run_notes) values ('{ASOF}',{mkt},{rot},{q(headline)},{q(json.dumps(call))}::jsonb,{q(json.dumps({'data_through': CARD['asof']}))}::jsonb)\n"
    'on conflict (asof) do update set mkt_score=excluded.mkt_score, rot_score=excluded.rot_score, headline=excluded.headline, callouts=excluded.callouts, run_notes=excluded.run_notes;\n')
print('sql files:', sorted(os.listdir(OUT / 'sql')), 'obs rows:', sum(len(g['v']) for g in segs))
print('HEADLINE:', headline)
for c in call: print('-', c['sev'], c['title'], '|', c['body'][:220])
