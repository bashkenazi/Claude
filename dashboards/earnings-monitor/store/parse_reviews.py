import json, re, glob, os, sys, html
S = sys.argv[1]
H = open(S + '/earnings-monitor.html').read()
D = json.loads(re.search(r'<script id="data"[^>]*>(.*?)</script>', H, re.S).group(1).replace('<\\/', '</'))
keep = {str(r.get('url')).split('?')[0]: r for r in D['bobby'] if r.get('report_date', '') >= '2026-07-01'}
files = {}
for f in glob.glob(S + '/data/review_md/*.md'):
    l = open(f).read().splitlines()
    if len(l) > 1: files[l[1].strip().split('?')[0]] = f
TAG = re.compile(r'<[^>]+>')
def clean(s): return html.unescape(TAG.sub('', s)).replace('\\$', '$').replace('\\', '').strip()
PCT = re.compile(r'([+\-−–]?\d+(?:\.\d+)?)\s*%')
BP = re.compile(r'([+\-−–]?\d+(?:\.\d+)?)\s*bp')
def pct(s):
    if not s: return None
    m = PCT.search(s)
    if m: return float(m.group(1).replace('−', '-').replace('–', '-'))
    m = BP.search(s)
    if m: return float(m.group(1).replace('−', '-').replace('–', '-')) / 100
    return None
DOTS = '🟢🔴🟠🟡⚪'
def sections(md):
    out, cur, buf = [], None, []
    for line in md.splitlines():
        m = re.match(r'^#{2,4}\s+(\d+)\.\s*(.*)$', line)
        if m or line.startswith('# '):
            if cur: out.append((cur, '\n'.join(buf)))
            cur, buf = ((int(m.group(1)), m.group(2)) if m else None), []
            continue
        buf.append(line)
    if cur: out.append((cur, '\n'.join(buf)))
    return out
def tables(txt):
    for t in re.findall(r'<table.*?</table>', txt, re.S):
        rows = [[clean(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.S)] for r in re.findall(r'<tr>(.*?)</tr>', t, re.S)]
        if rows: yield rows
prints, metrics = [], []
for url, r in keep.items():
    f = files.get(url)
    md = open(f).read() if f else ''
    key = os.path.basename(f)[:-3] if f else None
    cq = '2026Q2' if '_CQ2_' in url or r['report_date'] < '2026-10-01' else '2026Q3'
    title = r.get('title') or ''
    marker = ''.join(ch for ch in title.split(' ')[0] if ch in DOTS) if title[:1] in DOTS else ''
    prints.append(dict(ticker=r['ticker'], company_name=r.get('company'), sector=r.get('sector'), fiscal_quarter=r.get('quarter'),
        calendar_quarter=cq, report_date=r['report_date'], verdict=r.get('sentiment'), verdict_marker=marker,
        headline=(r.get('headline') or '')[:600], summary=r.get('summary') or [], stock_reaction=r.get('reaction'),
        title=title, local_key=key or url))
    for (num, name), body in sections(md):
        if num not in (2, 3, 4): continue
        sec = {2: 'quarter', 3: 'next_q_guide', 4: 'fy_guide'}[num]
        for rows in tables(body):
            hdr = rows[0]
            def col(pred):
                for i, h in enumerate(hdr):
                    if i and pred(h): return i
            ia = 1
            ist = col(lambda h: '📊' in h and 'Δ' not in h)
            ivs = col(lambda h: '📊' in h and 'Δ' in h)
            ib = col(lambda h: '🎯' in h and 'Δ' not in h)
            ivb = col(lambda h: '🎯' in h and 'Δ' in h)
            for row in rows[1:]:
                if not row or not row[0]: continue
                g = lambda i: row[i] if i is not None and i < len(row) and row[i] not in ('—', '-', '') else None
                lab = row[0]; mk = ''.join(ch for ch in lab if ch in DOTS); lab = lab.lstrip(DOTS + ' ️').strip()
                metrics.append(dict(local_key=key or url, section=sec, metric=lab[:120], actual=g(ia), street=g(ist), bogey=g(ib),
                    vs_street_pct=pct(g(ivs)), vs_bogey_pct=pct(g(ivb)), marker=mk or None,
                    raw_row=dict(header=hdr, row=row, section_title=name[:120])))
json.dump(dict(prints=prints, metrics=metrics), open(S + '/load_earn/parsed.json', 'w'), ensure_ascii=False)
from collections import Counter
print(len(prints), Counter(p['calendar_quarter'] for p in prints), len(metrics), Counter(m['section'] for m in metrics))
print(sum(1 for p in prints if not p['local_key'].startswith('http')), 'with local file')
