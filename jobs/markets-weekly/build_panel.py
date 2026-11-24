"""Build the monthly markets panel: Bloomberg history (1970-2018) spliced with FactSet (macro + ETF prices).

Inputs:  data/bbg_monthly.csv (parse_bbg.py), data/factset_raw/*.json (FactSet MCP pulls)
Outputs: data/obs_long.csv   one row per series x month (what goes to Supabase macro_observations)
         data/panel.csv      wide monthly panel used by study.py
Run with: python3 -I build_panel.py
"""
import json, glob, os, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).parent
RAW = ROOT / 'data' / 'factset_raw'

NEW = ROOT / 'data' / 'factset_new'   # weekly pulls (recent window) that overlay the committed history in factset_raw

def fs_items(name):
    """Macro items for a series: committed history, then this week's pull (same periodDate -> newer value wins)."""
    by = {}
    for base in (RAW, NEW):
        p = base / f'{name}.json'
        if not p.exists(): continue
        d = json.load(open(p))
        for it in (d['data'][0]['items'] if d.get('data') else []): by[it['periodDate']] = it
    return list(by.values())

def fs_series(name, how='last'):
    """FactSet as_reported_economics items -> monthly Series indexed by month-end Timestamp."""
    items = fs_items(name)
    if not items: return None
    s = pd.Series({pd.Timestamp(i['periodDate']): i['value'] for i in items if i.get('value') is not None}, dtype=float).sort_index()
    s.index = s.index.to_period('M').to_timestamp('M')
    return getattr(s.groupby(level=0), how)()

def fs_prices(kind='W'):
    """All px_*.json price files -> DataFrame of closes (columns = ticker), index = date."""
    frames = {}
    for p in sorted(glob.glob(str(RAW / 'px_*.json'))) + sorted(glob.glob(str(NEW / 'px_*.json'))):   # new pulls last: they win
        nm = os.path.basename(p)
        if nm.startswith('px_tr') or (kind == 'W') == nm.startswith('px_d_'): continue
        d = json.load(open(p))
        rows = d.get('data', d) if isinstance(d, dict) else d
        for r in rows:
            if r.get('price') is None: continue
            tk = r.get('requestId') or r.get('fsymId')
            frames.setdefault(tk, {})[pd.Timestamp(r['date'])] = r['price']
    return pd.DataFrame({k: pd.Series(v) for k, v in frames.items()}).sort_index() if frames else pd.DataFrame()

def fs_tr():
    """Monthly total returns (decimal) per ticker from px_tr*.json."""
    out = {}
    for p in sorted(glob.glob(str(RAW / 'px_tr*.json'))) + sorted(glob.glob(str(NEW / 'px_tr*.json'))):
        d = json.load(open(p))
        rows = d.get('data', d) if isinstance(d, dict) else d
        for r in rows:
            if r.get('totalReturn') is None: continue
            tk = r.get('requestId') or r.get('fsymId')
            out.setdefault(tk, {})[pd.Timestamp(r['date']).to_period('M').to_timestamp('M')] = r['totalReturn'] / 100.0
    return pd.DataFrame({k: pd.Series(v) for k, v in out.items()}).sort_index() if out else pd.DataFrame()

def bbg():
    b = pd.read_csv(ROOT / 'data' / 'bbg_monthly.csv')
    b['month'] = pd.to_datetime(b['month']).dt.to_period('M').dt.to_timestamp('M')
    return b.pivot(index='month', columns='series_id', values='value')

def splice(old, new, mode='level'):
    """Old history, then new source after old ends. mode='ratio' rescales new to old at the overlap."""
    if old is None or old.dropna().empty: return new
    if new is None or new.dropna().empty: return old
    old = old.dropna(); new = new.dropna()
    if mode == 'ratio':
        ov = old.index.intersection(new.index)
        if len(ov) >= 6: new = new * float((old[ov] / new[ov]).tail(36).median())
    return pd.concat([old, new[new.index > old.index.max()]]).sort_index()

def build():
    B = bbg()
    P = {}
    # ---- markets
    W = fs_prices('W')
    M_px = W.resample('ME').last() if not W.empty else pd.DataFrame()
    spy = M_px.get('SPY-US')
    P['SPX'] = splice(B.get('SPX'), spy, 'ratio')            # SPX level after Jul-2018 = SPY scaled to SPX at the overlap
    P['MSCI_WORLD'] = B.get('MSCI_WORLD')
    for c in M_px.columns: P['PX_' + c.replace('-US', '')] = M_px[c]
    # ---- rates & policy (FactSet monthly averages; Bloomberg month-end before)
    P['UST10Y'] = splice(B.get('UST10Y'), fs_series('FRBRIFLGFCY10_US'))
    P['UST2Y'] = fs_series('FRBRIFLGFCY02_US')
    P['UST3M'] = fs_series('FRBRIFLGFCM03_US')
    P['UST5Y'] = splice(B.get('UST5Y'), fs_series('FRBRIFLGFCY05_US'))
    P['FED_FUNDS'] = fs_series('FRBRIFSPFF_US')
    P['FED_FUNDS_UPPER'] = splice(B.get('FED_FUNDS_UPPER'), fs_series('ITONMAXD_US'))
    P['REAL10Y'] = fs_series('FRBRIFLGFCIIY10_US')
    P['BE10Y'] = fs_series('USIR6389706')
    P['FWD5Y5Y_BE'] = fs_series('USIR1578126')
    P['FED_ASSETS'] = splice(B.get('FED_ASSETS'), fs_series('US_CBASSET'))
    # ---- labor
    P['UNEMP_RATE'] = splice(B.get('UNEMP_RATE'), fs_series('US_LMUEMPR'))
    ic = fs_series('DOLICLAIMUI_US', 'mean'); P['INIT_CLAIMS'] = splice(B.get('INIT_CLAIMS'), ic / 1000.0 if ic is not None and ic.median() > 5000 else ic)
    cc = fs_series('US_LMCLAIMS', 'mean'); P['CONT_CLAIMS'] = cc / 1000.0 if cc is not None and cc.median() > 50000 else cc
    priv = fs_series('USLM1012144')
    P['NFP_CHG'] = splice(B.get('NFP_CHG'), priv.diff() if priv is not None else None)
    P['AVG_WEEKLY_HOURS'] = splice(B.get('AVG_WEEKLY_HOURS'), fs_series('USLM2253126'))
    ahe = fs_series('US_LMWAGES')
    P['AHE_YOY'] = splice(B.get('AHE_YOY'), (ahe.pct_change(12) * 100) if ahe is not None else None)
    P['JOLTS_OPENINGS'] = fs_series('US_LMVAC')
    # ---- inflation
    cpi, core = fs_series('US_CPIALL'), fs_series('US_CPICORE')
    P['CPI_YOY'] = (cpi.pct_change(12) * 100) if cpi is not None else B.get('CPI_YOY')
    P['CORE_CPI_YOY'] = (core.pct_change(12) * 100) if core is not None else None
    pce = fs_series('BEANIPABA03RG3_US'); P['CORE_PCE_YOY'] = (pce.pct_change(12) * 100) if pce is not None else None
    P['PPI_YOY'] = B.get('PPI_YOY'); P['PPI_CORE_YOY'] = B.get('PPI_CORE_YOY')
    # ---- growth & surveys
    P['ISM_MFG'] = B.get('ISM_MFG')
    P['EMPIRE_GEN'] = fs_series('USSU0009518'); P['EMPIRE_NEWORD'] = fs_series('USSU0009522')
    P['TX_MFG'] = fs_series('USSU0587918'); P['KC_MFG'] = fs_series('USSU1293726')
    P['GDP_YOY'] = B.get('GDP_YOY'); P['GDP_QOQ_SAAR'] = B.get('GDP_QOQ_SAAR')
    ip = fs_series('US_INDPRODMG'); P['IP_MFG_YOY'] = (ip.pct_change(12) * 100) if ip is not None else None
    P['CAP_UTIL'] = fs_series('FRBUTLB50001')
    cg = fs_series('CENANXANO'); P['CORE_CAPEX_ORD_YOY'] = (cg.rolling(3).mean().pct_change(12) * 100) if cg is not None else None
    rs = fs_series('CENRETAIL_MVP_US'); P['RETAIL_XAUTO_YOY'] = (rs.rolling(3).mean().pct_change(12) * 100) if rs is not None else None
    P['INV_SALES'] = fs_series('US_INDINVR')
    P['UMICH_SENT'] = splice(B.get('UMICH_SENT'), fs_series('USSU0014446'))
    # ---- housing
    P['HOUSING_STARTS'] = splice(B.get('HOUSING_STARTS'), fs_series('US_HCSTARTS'))
    P['BUILDING_PERMITS'] = fs_series('US_HCPERMIT')
    P['NEW_HOME_SALES'] = splice(B.get('NEW_HOME_SALES'), fs_series('CENHSOLDTOT_US'))
    P['NAHB'] = fs_series('NAHBWFHMI')
    P['MORTGAGE30'] = B.get('MORTGAGE30')
    # ---- credit & liquidity
    m2 = fs_series('US_MAM2'); P['M2_YOY'] = (m2.pct_change(12) * 100) if m2 is not None else None
    ci = fs_series('FRBBCABLCCBA_US'); P['CI_LOANS_YOY'] = (ci.pct_change(12) * 100) if ci is not None else None
    P['SLOOS_CI_TIGHTEN'] = fs_series('USSU0486263')
    # ---- valuation
    P['SPX_FWD_PE'] = B.get('SPX_FWD_PE'); P['NASDAQ_FWD_PE'] = B.get('NASDAQ_FWD_PE')
    # ---- international (history only)
    for k in ['CHINA_PMI', 'CHINA_FX_RESERVES', 'CHINA_TRADE_BAL', 'UK_CORE_CPI_YOY']: P[k] = B.get(k)
    df = pd.DataFrame({k: v for k, v in P.items() if v is not None}).sort_index()
    df = df[df.index >= '1970-01-31']
    # ISM proxy after Jul-2018: regional Fed manufacturing surveys mapped to ISM over 2001-2018 (OLS). Flagged as proxy.
    need = ['ISM_MFG', 'EMPIRE_GEN', 'TX_MFG', 'KC_MFG']
    reg = df[need].dropna() if all(c in df for c in need) else pd.DataFrame()
    if len(reg) > 60:
        X = np.column_stack([np.ones(len(reg)), reg[['EMPIRE_GEN', 'TX_MFG', 'KC_MFG']].values])
        beta, *_ = np.linalg.lstsq(X, reg['ISM_MFG'].values, rcond=None)
        fit = X @ beta; r2 = 1 - ((reg['ISM_MFG'] - fit) ** 2).sum() / ((reg['ISM_MFG'] - reg['ISM_MFG'].mean()) ** 2).sum()
        Z = df[['EMPIRE_GEN', 'TX_MFG', 'KC_MFG']]
        prox = pd.Series(np.column_stack([np.ones(len(Z)), Z.values]) @ beta, index=df.index)
        df['ISM_PROXY'] = prox.where(Z.notna().all(axis=1))
        df['ISM_BLEND'] = df['ISM_MFG'].combine_first(df['ISM_PROXY'].where(df.index > df['ISM_MFG'].dropna().index.max()))
        json.dump({'beta': beta.tolist(), 'r2': float(r2), 'n': len(reg)}, open(ROOT / 'data' / 'ism_proxy_fit.json', 'w'))
    else:
        df['ISM_BLEND'] = df.get('ISM_MFG')
    return df, fs_tr()

if __name__ == '__main__':
    df, tr = build()
    df.to_csv(ROOT / 'data' / 'panel.csv', index_label='month')
    if not tr.empty: tr.to_csv(ROOT / 'data' / 'sector_tr_monthly.csv', index_label='month')
    long = df.stack().rename('value').reset_index().rename(columns={'level_1': 'series_id'})
    long.to_csv(ROOT / 'data' / 'obs_long.csv', index=False)
    cov = df.apply(lambda s: pd.Series({'first': s.first_valid_index(), 'last': s.last_valid_index(), 'n': s.notna().sum()})).T
    print(cov.to_string())
