"""Parse the Bloomberg 'Market historicals' CSV exports (1970-2018) into one long monthly table.
Uses the ticker blocks (TICKER row, Date row, field row). Output: data/bbg_monthly.csv (series_id, month, value)."""
import csv, re, sys, json, pathlib
ROOT = pathlib.Path(__file__).parent
MON = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}
def mdate(s):
    m = re.fullmatch(r'([A-Z][a-z]{2})-(\d{2})', s.strip())
    if not m: return None
    y = int(m.group(2)); y += 2000 if y < 50 else 1900
    return f'{y}-{MON[m.group(1)]:02d}'
def num(s):
    s = s.strip().replace(',', '')
    if not s or s.startswith('#'): return None
    try: return float(s)
    except ValueError: return None
# Bloomberg ticker (+field) -> our series id
MAP = {('GT10 Govt','YLD_YTM_MID'):'UST10Y', ('SPX Index','LAST_PRICE'):'SPX', ('SPX Index','BEST_PE_RATIO'):'SPX_FWD_PE',
 ('CCMP Index','LAST_PRICE'):'NASDAQ', ('CCMP Index','BEST_PE_RATIO'):'NASDAQ_FWD_PE', ('NAPMPMI Index','PX_LAST'):'ISM_MFG',
 ('GDP CYOY Index','LAST_PRICE'):'GDP_YOY', ('GDP CURY Index','LAST_PRICE'):'GDP_YOY', ('GDP CQOQ Index','LAST_PRICE'):'GDP_QOQ_SAAR',
 ('UKHCA9IQ Index','LAST_PRICE'):'UK_CORE_CPI_YOY', ('CPI YOY Index','LAST_PRICE'):'CPI_YOY', ('FDTR Index','LAST_PRICE'):'FED_FUNDS_UPPER',
 ('PPI XYOY Index','LAST_PRICE'):'PPI_CORE_YOY', ('PPI YOY Index','LAST_PRICE'):'PPI_YOY', ('CONSSENT Index','LAST_PRICE'):'UMICH_SENT',
 ('NFP TCH Index','LAST_PRICE'):'NFP_CHG', ('INJCJC Index','LAST_PRICE'):'INIT_CLAIMS', ('AHE YOY% Index','LAST_PRICE'):'AHE_YOY',
 ('AWH TOTL Index','LAST_PRICE'):'AVG_WEEKLY_HOURS', ('RSTAXAG% Index','LAST_PRICE'):'RETAIL_XAUTO_GAS_MOM', ('FARBAST Index','LAST_PRICE'):'FED_ASSETS',
 ('USGG5YR Index','LAST_PRICE'):'UST5Y', ('USGGT05Y Index','LAST_PRICE'):'TIPS5Y', ('NHSPSTOT Index','LAST_PRICE'):'HOUSING_STARTS',
 ('NHSLTOT Index','LAST_PRICE'):'NEW_HOME_SALES', ('ILM3NAVG Index','LAST_PRICE'):'MORTGAGE30', ('WIRACHIN Index','LAST_PRICE'):'CHINA_FX_RESERVES',
 ('CNFRCBAL Index','LAST_PRICE'):'CHINA_TRADE_BAL', ('EHUPUS Index','LAST_PRICE'):'UNEMP_RATE', ('MXWO Index','LAST_PRICE'):'MSCI_WORLD',
 ('CPMINDX Index','PX_LAST'):'CHINA_PMI', ('MPMIEZMA Index','PX_LAST'):'EZ_PMI'}
out = {}  # (sid, month) -> (value, file)
for fn in ['bbg_1970_1985.csv','bbg_1986_2000.csv','bbg_1999_2018.csv']:
    rows = list(csv.reader(open(ROOT/'raw'/fn, encoding='utf-8-sig')))
    header = [mdate(c) for c in rows[0][1:]]
    for i, r in enumerate(rows):
        tk = r[0].strip()
        if not tk.endswith(('Index','Govt')) or i + 2 >= len(rows): continue
        if rows[i+1][0].strip() != 'Date': continue
        field = rows[i+2][0].strip().upper()
        sid = MAP.get((tk, field))
        if not sid: continue
        drow = [mdate(c) for c in rows[i+1][1:]]
        ok = sum(1 for d in drow if d) > 0.8 * len([c for c in rows[i+1][1:] if c.strip()])
        dates = drow if ok and all(a is None or b is None or a < b for a, b in zip(drow, drow[1:])) else header
        for d, v in zip(dates, rows[i+2][1:]):
            x = num(v)
            if d and x is not None: out[(sid, d)] = (x, fn)   # later files overwrite earlier (1999-2000 overlap)
# drop all-zero placeholder series values (sheet formulas that returned 0)
w = csv.writer(open(ROOT/'data'/'bbg_monthly.csv', 'w', newline=''))
w.writerow(['series_id','month','value','source_file'])
stats = {}
for (sid, d), (x, fn) in sorted(out.items()):
    w.writerow([sid, d, x, fn]); s = stats.setdefault(sid, [d, d, 0]); s[1] = d; s[2] += 1
for k, v in sorted(stats.items()): print(f'{k:24s} {v[0]} -> {v[1]}  n={v[2]}')
