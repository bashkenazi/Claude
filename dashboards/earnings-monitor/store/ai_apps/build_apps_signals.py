"""Build the Bobby Tech Daily page-database document ai/apps_signals from the AI dashboards on apps.srsinvest.com/ai.

Usage: python3 -I build_apps_signals.py <apps_dir> <out.json> [<previous apps_signals.json>]
<apps_dir> holds the files listed in README.md, saved at their key paths below ai/ (e.g. <apps_dir>/gpu_spot_rental/data.json).
With a previous document it writes callouts for what changed since that run; without one, 4-week changes.
"""
import json, collections, datetime as dt, sys, os
A = sys.argv[1]; OUT = sys.argv[2]
PREV = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else None
J = lambda p: json.load(open(os.path.join(A, p)))
D = lambda s: dt.date.fromisoformat(s[:10])
def wk(d):  # week ending Friday
    d = D(d); return d + dt.timedelta(days=(4 - d.weekday()) % 7)
def weekly(pts):  # pts [(date, v)] -> {friday: last v}
    out = {}
    for d, v in sorted(pts):
        if v is None: continue
        out[wk(d)] = float(v)
    return out
def chg(pts, days):
    pts = [(D(d), float(v)) for d, v in sorted(pts) if v is not None]
    if not pts: return None
    last_d, last_v = pts[-1]; tgt = last_d - dt.timedelta(days=days)
    prev = [v for d, v in pts if d <= tgt]
    return (last_v / prev[-1] - 1) if prev and prev[-1] else None
r3 = lambda x: None if x is None else round(x, 4)

# ---------- GPU rental ----------
g = J('gpu_spot_rental/data.json'); T = g['tiles']
series = {}  # key -> dict(n, src, gpu, pts)
for r in T['ornn_gpu_series']:
    if r['SOURCE'] not in ('public', 'bloomberg'): continue
    gpu = r['GPU'].replace(' SXM4', '').replace(' SXM', '').replace(' WS', '')
    s = series.setdefault('ornn_' + gpu, {'n': 'Ornn ' + gpu, 'src': 'Ornn index (Bloomberg ORNN backfill, then free daily feed)', 'gpu': gpu, 'pts': []})
    s['pts'].append((r['PRICE_DATE'], r['INDEX_VALUE']))
SDN = {'SDH100RT': 'H100', 'SDA100RT': 'A100', 'SDB200RT': 'B200'}
for r in T['gpu_rental_series']:
    if r['TICKER'] not in SDN: continue  # Compute Index series are stale-filled since Sep 8 (see page notes)
    gpu = SDN[r['TICKER']]
    s = series.setdefault('sd_' + gpu, {'n': 'Silicon Data ' + gpu, 'src': 'Silicon Data rental index (Bloomberg ' + r['TICKER'] + ')', 'gpu': gpu, 'pts': []})
    s['pts'].append((r['PRICE_DATE'], r['PX_LAST']))
nb = collections.defaultdict(lambda: collections.defaultdict(list))
for r in T['gpu_nbis_daily']: nb[r['GPU']][r['D']].append(r['PX'])
for gpu, by in nb.items():
    series['nbis_' + gpu] = {'n': 'Nebius spot ' + gpu, 'src': 'Nebius spot API, average across regions (floating spot from Oct 8; earlier = list price)', 'gpu': gpu,
                             'pts': [(d, sum(v) / len(v)) for d, v in by.items()]}
for s in series.values(): s['pts'] = sorted((d, v) for d, v in s['pts'] if v is not None)
gpu_latest = []
for k, s in series.items():
    d, v = s['pts'][-1]
    gpu_latest.append({'k': k, 'n': s['n'], 'gpu': s['gpu'], 'd': d, 'v': round(v, 3), 'c4': r3(chg(s['pts'], 28)), 'c12': None if k.startswith('nbis_') else r3(chg(s['pts'], 84)), 'src': s['src']})
order = ['H100', 'H200', 'B200', 'B300', 'A100', 'RTX PRO 6000']
gpu_latest.sort(key=lambda x: (order.index(x['gpu']) if x['gpu'] in order else 9, x['n']))
def chart(keys, start):
    W = {k: weekly(series[k]['pts']) for k in keys if k in series}
    weeks = sorted({w for m in W.values() for w in m if w >= start})
    return {'w': [w.isoformat() for w in weeks], 's': [{'k': k, 'n': series[k]['n'], 'v': [round(W[k][w], 3) if w in W[k] else None for w in weeks]} for k in W]}
st = dt.date(2025, 8, 15)
gpu = {'asof': g['freshness_as_of'], 'latest': gpu_latest,
       'charts': {'H100': chart(['ornn_H100', 'sd_H100', 'nbis_H100'], st), 'B200': chart(['ornn_B200', 'sd_B200', 'nbis_B200'], st),
                  'H200': chart(['ornn_H200', 'nbis_H200'], dt.date(2026, 8, 7)), 'B300': chart(['nbis_B300'], dt.date(2026, 9, 18))},
       'note': 'Ornn H100/B200 history before Aug 7, 2026 is the Bloomberg ORNN backfill of the same series. Silicon Data series end at the contractor file\'s last day and can carry forward. Compute Index (CIHOPUS, CIHOPEU, CIBLKWUS) is left out: flat stale fill since Sep 8. Nebius is floating spot only from Oct 8, 2026 (earlier points are its fixed list price) and swings day to day, so its 4-week change is noisy and its 12-week change is left blank.'}

# ---------- token prices (Silicon Data) ----------
sd = J('silicon_data/data.json')
tok = {'asof': sd['as_of'], 's': []}
wkset = set()
for key in ('broad', 'open', 'proprietary'):
    s = sd['daily'][key]; W = weekly(list(zip(s['dates'], s['values'])))
    tok['s'].append({'k': key, 'n': sd['series_meta'][key]['label'], 'code': sd['series_meta'][key]['code'], 'W': W,
                     'last': round(s['values'][-1], 3), 'd': s['dates'][-1], 'c4': r3(chg(list(zip(s['dates'], s['values'])), 28)),
                     'tier': s['source_tier'][-1]})
    wkset |= set(W)
weeks = sorted(wkset); tok['w'] = [w.isoformat() for w in weeks]
for s in tok['s']: W = s.pop('W'); s['v'] = [round(W[w], 3) if w in W else None for w in weeks]
tok['note'] = 'Open and proprietary series before the Bloomberg export are read off Silicon Data charts (source tier "chart_estimate"); the broad index is the Bloomberg export throughout.'

# ---------- OpenRouter weekly token share ----------
o = J('openrouter/data.json')
tk = collections.defaultdict(dict); sp = collections.defaultdict(dict)
for x in o['tiles']['enterprise_weekly_openrouter']['provider']:
    (tk if x['METRIC_NAME'] == 'Tokens' else sp)[x['PERIOD_START']][x['MODEL_PROVIDER']] = float(x['VALUE'])
wks = sorted(tk)[-26:]
last = wks[-1]; tot_last = sum(tk[last].values())
top = [p for p, _ in sorted(tk[last].items(), key=lambda z: -z[1]) if p != 'All Other'][:6]
for p in ('Anthropic', 'OpenAI', 'Google'):
    if p not in top: top.append(p)
orr = {'asof': o['freshness_as_of'], 'w': wks, 'tot': [round(sum(tk[w].values()) / 1e12, 2) for w in wks],
       's': [{'n': p, 'v': [round(100 * tk[w].get(p, 0) / sum(tk[w].values()), 2) for w in wks]} for p in top],
       'spend': [{'n': p, 'v': round(100 * sp[last].get(p, 0) / max(1, sum(sp[last].values())), 1)} for p in sorted(sp[last], key=lambda q: -sp[last][q])[:6]],
       'note': 'Yipit view of OpenRouter, all tokens (free and paid), week starting Monday. Spend share is token spend in the latest week. Yipit tokens reconcile to the public OpenRouter share series within 0.06%.'}

# ---------- ARR claims ----------
a = J('arr_estimates/data.json')['tiles']['arr_claims']
def cl(x): return {'e': x['ENTITY'], 'm': x['METRIC'], 'd': x['AS_OF_DATE'], 'lo': x['ANNUAL_LOW_USD_M'], 'hi': x['ANNUAL_HIGH_USD_M'],
                   'src': x['SOURCE_NAME'], 'st': x['SOURCE_TYPE'], 'u': x.get('SOURCE_URL') or '', 'conf': x.get('CONFIDENCE') or ''}
cur = [x for x in a if x['HORIZON'] == 'current' and x['METRIC'] in ('arr', 'run_rate') and x['ANNUAL_LOW_USD_M']]
arr_ = {'labs': {}, 'other': []}
for lab in ('Anthropic', 'OpenAI'):
    arr_['labs'][lab] = [cl(x) for x in sorted([x for x in cur if x['ENTITY'] == lab], key=lambda x: (x['AS_OF_DATE'], x['SOURCE_NAME']))][-10:][::-1]
seen = {}
for x in sorted(cur, key=lambda x: x['AS_OF_DATE']):
    if x['ENTITY'] not in ('Anthropic', 'OpenAI'): seen[x['ENTITY']] = x
arr_['other'] = sorted([cl(x) for x in seen.values()], key=lambda c: -(c['hi'] or 0))
fc = [x for x in a if x['HORIZON'] == 'forecast' and x['ENTITY'] in ('Anthropic', 'OpenAI')]
arr_['fc'] = [cl(x) | {'per': x.get('AS_OF_LABEL')} for x in sorted(fc, key=lambda x: x['PUBLISHED_AT'] or '')[-10:][::-1]]
vs = collections.defaultdict(dict)
for x in J('arr_estimates/data.json')['tiles']['arr_sig_vercel']: vs[(x['WEEK_END'], x['METRIC'])][x['LAB']] = x['SHARE_PCT']
arr_['vercel'] = [{'w': k[0], 'm': k[1], **v} for k, v in sorted(vs.items())[-4:]]
arr_['note'] = 'Each claim is one source\'s figure, annualized, never averaged. Yipit run-rate is a dataset estimate; SRS ARR model is the analysts\' workbook. Ledger is updated by hand after review.'

# ---------- dashboard headlines ----------
PAGES = [('dc_buildout', 'Data center build-out', 'Census C30 construction, Epoch large-site GW, hyperscaler capex'),
         ('nvda_alternatives', 'NVIDIA alternatives', 'ASIC/AMD share, hyperscaler capex, AWS spot, Taiwan ASIC houses'),
         ('silicon_data', 'LLM token prices', 'Silicon Data $ per million tokens'),
         ('ramp_ai', 'Ramp AI spend', 'Business adoption, model spend share, token spend and price'),
         ('ai_web_signals', 'AI web signals', 'DNS traffic share, enterprise hostnames'),
         ('korean_memory', 'Korean memory exports', 'DRAM / flash export value, volume and unit value'),
         ('incremental_research', 'Incremental research', 'Yipit and M Science sentiment reads on AI themes'),
         ('ai_server_trade', 'AI server trade', 'US computer imports vs NVIDIA data-center revenue')]
dash = []
for pid, title, what in PAGES:
    try: ins = J(pid + '/insights.json')
    except Exception: continue
    items = []
    for vk, vw in ins['views'].items():
        for it in vw['items']:
            href = it.get('href') or ''
            if href.startswith('#'): href = 'https://apps.srsinvest.com/ai/' + pid + '/index.html' + href
            items.append({'id': it.get('id') or '', 't': it['text'], 'imp': it.get('imp') or '', 'd': it.get('d') or '', 'q': it.get('q') or '', 'u': href, 'v': vw.get('label') or ''})
    dash.append({'id': pid, 'title': title, 'what': what, 'asof': ins.get('as_of'), 'gen': ins.get('generated_at', '')[:10], 'stale': ins.get('stale_after_days'),
                 'url': 'https://apps.srsinvest.com/ai/' + pid + '/index.html', 'items': items})
# pages without an insights file: computed headline from their data
tw = J('taiwan_monthly/data.json')['header']
gl = {x['k']: x for x in gpu_latest}
dash.append({'id': 'gpu_spot_rental', 'title': 'GPU rental prices', 'what': 'Nebius spot, Ornn and Silicon Data indices', 'asof': gpu['asof'], 'gen': g['generated_at'][:10], 'stale': 4,
             'url': 'https://apps.srsinvest.com/ai/gpu_spot_rental/index.html',
             'items': [{'t': f"Ornn index {x['gpu']} ${x['v']:.2f}/GPU-hr on {x['d']} ({x['c4']*100:+.0f}% over 4 weeks, {x['c12']*100:+.0f}% over 12)" if x['c12'] is not None else f"Ornn {x['gpu']} ${x['v']:.2f}/GPU-hr on {x['d']}", 'imp': '', 'd': x['d'], 'q': 'context', 'u': 'https://apps.srsinvest.com/ai/gpu_spot_rental/index.html', 'v': ''}
                       for x in gpu_latest if x['k'] in ('ornn_H100', 'ornn_H200', 'ornn_B200')]})
la, lo_ = arr_['labs']['Anthropic'][0], arr_['labs']['OpenAI'][0]
dash.append({'id': 'arr_estimates', 'title': 'Lab ARR estimates', 'what': 'Anthropic and OpenAI ARR by source, weekly lead signals', 'asof': max(x['AS_OF_DATE'] for x in cur if x['AS_OF_DATE'] <= dt.date.today().isoformat()), 'gen': J('arr_estimates/data.json')['generated_at'][:10], 'stale': 30,
             'url': 'https://apps.srsinvest.com/ai/arr_estimates/index.html',
             'items': [{'t': f"Latest Anthropic run-rate claim: ${la['hi']/1000:.1f}bn ({la['src']}, {la['d']})", 'imp': '', 'd': la['d'], 'q': 'context', 'u': 'https://apps.srsinvest.com/ai/arr_estimates/index.html', 'v': ''},
                       {'t': f"Latest OpenAI run-rate claim: ${lo_['hi']/1000:.1f}bn ({lo_['src']}, {lo_['d']})", 'imp': '', 'd': lo_['d'], 'q': 'context', 'u': 'https://apps.srsinvest.com/ai/arr_estimates/index.html', 'v': ''}]})
sh = {s['n']: s['v'][-1] for s in orr['s']}
dash.append({'id': 'openrouter', 'title': 'OpenRouter tokens', 'what': 'Weekly tokens and spend by model provider (Yipit)', 'asof': orr['asof'], 'gen': o['generated_at'][:10], 'stale': 14,
             'url': 'https://apps.srsinvest.com/ai/openrouter/index.html',
             'items': [{'t': f"Week of {last}: {orr['tot'][-1]:.0f}T tokens ({(orr['tot'][-1]/orr['tot'][-5]-1)*100:+.0f}% vs 4 weeks earlier); share " + ', '.join(f"{p} {sh[p]:.1f}%" for p in list(sh)[:5]), 'imp': '', 'd': last, 'q': 'context', 'u': 'https://apps.srsinvest.com/ai/openrouter/index.html', 'v': ''}]})
dash.append({'id': 'taiwan_monthly', 'title': 'Taiwan monthly revenue', 'what': 'TWSE/TPEx monthly sales across the tech supply chain', 'asof': tw['as_of'][:7], 'gen': '', 'stale': 40,
             'url': 'https://apps.srsinvest.com/ai/taiwan_monthly/index.html',
             'items': [{'t': f"Taiwan tech universe revenue {tw['as_of'][:7]}: +{float(tw['market_yoy_usd'])*100:.1f}% y/y in USD (+{float(tw['market_yoy_ntd'])*100:.1f}% in NT$); {tw['n_filed']} of {tw['n_universe']} companies filed", 'imp': '', 'd': tw['as_of'][:7], 'q': 'context', 'u': 'https://apps.srsinvest.com/ai/taiwan_monthly/index.html', 'v': ''}]})
LINKS = [('aggregate_ai_datapoints', 'Aggregate AI datapoints'), ('epoch', 'Epoch AI: US vs Chinese models'), ('vercel_gateway', 'Vercel AI Gateway'), ('crowding', 'AI crowding'),
         ('ai_stack_roic', 'AI stack ROIC'), ('github_coauthor_commits', 'GitHub co-author commits'), ('lab_sdk_downloads', 'Lab SDK downloads'), ('ai_community_tracker/reports', 'AI community tracker')]

# ---------- headline calls ----------
census = next((i for d in dash if d['id'] == 'dc_buildout' for i in d['items'] if 'C30' in i['t']), None)
def C(k, l, v, sub, n): return {'k': k, 'l': l, 'v': v, 's': sub, 'n': n}
calls = [
    C('arr_anth', 'Anthropic run-rate, latest claim', f"${la['hi']/1000:.1f}bn", f"{la['src']} · {la['d']}", la['hi']),
    C('arr_oai', 'OpenAI run-rate, latest claim', f"${lo_['hi']/1000:.1f}bn", f"{lo_['src']} · {lo_['d']}", lo_['hi']),
    C('gpu_h100', 'Ornn H100 rental', f"${gl['ornn_H100']['v']:.2f}/hr", f"{gl['ornn_H100']['c12']*100:+.0f}% over 12 weeks · {gl['ornn_H100']['d']}", gl['ornn_H100']['v']),
    C('gpu_b200', 'Ornn B200 rental', f"${gl['ornn_B200']['v']:.2f}/hr", f"{gl['ornn_B200']['c12']*100:+.0f}% over 12 weeks · {gl['ornn_B200']['d']}", gl['ornn_B200']['v']),
    C('tok', 'LLM token price (broad index)', f"${tok['s'][0]['last']:.2f}/M", f"{tok['s'][0]['c4']*100:+.0f}% over 4 weeks · {tok['s'][0]['d']}", tok['s'][0]['last']),
    C('or_tok', 'OpenRouter weekly tokens', f"{orr['tot'][-1]:.0f}T", f"{(orr['tot'][-1]/orr['tot'][-5]-1)*100:+.0f}% vs 4 weeks earlier · wk of {last}", orr['tot'][-1]),
]
for d0 in dash:
    for it in d0['items']:
        if d0['id'] == 'dc_buildout' and 'C30' in it['t']: calls.append(C('c30', 'US data-center construction (SAAR)', '$' + it['t'].split('$')[1].split(' bn')[0] + 'bn', it['d'] + ' · Census C30', None))
        if d0['id'] == 'dc_buildout' and it['t'].startswith('Epoch tracks'): calls.append(C('epoch', 'Epoch large AI sites online', it['t'].split(' with ')[1].split(' of ')[0], it['d'] + ' · Epoch', None))

# ---------- thesis signpost readings ----------
CN = {'DeepSeek', 'Z.ai', 'Tencent', 'Alibaba', 'Qwen', 'Moonshot AI', 'MiniMax', 'StepFun', 'Xiaomi', 'ByteDance', 'Baidu', 'Meituan', 'Kuaishou'}
ci = sum(v for n_, v in sh.items() if n_ in CN)
allsh = {}
tot_w = sum(tk[last].values())
for p_, v in tk[last].items(): allsh[p_] = 100 * v / tot_w
cn_share = sum(v for p_, v in allsh.items() if p_ in CN)
cn_prev = sum(100 * v / sum(tk[wks[-5]].values()) for p_, v in tk[wks[-5]].items() if p_ in CN)
ramp = next((i['t'] for d0 in dash if d0['id'] == 'ramp_ai' for i in d0['items'] if i['t'].startswith('Share of AI model spend')), '')
cap = next((i['t'] for d0 in dash if d0['id'] == 'dc_buildout' for i in d0['items'] if 'hyperscalers' in i['t'].lower()), '')
U = 'https://apps.srsinvest.com/ai/'
signposts = {
    'arr': {'value': f"Anthropic ${la['hi']/1000:.1f}bn run-rate ({la['src']}, {la['d']}); OpenAI ${lo_['hi']/1000:.1f}bn ({lo_['src']}, {lo_['d']})" + (f". Ramp: {ramp}" if ramp else ''), 'date': max(la['d'], lo_['d']), 'u': U + 'arr_estimates/index.html'},
    'gpu': {'value': '; '.join(f"{x['n']} ${x['v']:.2f}/hr ({x['c12']*100:+.0f}% 12w)" for x in gpu_latest if x['k'] in ('ornn_H100', 'ornn_H200', 'ornn_B200', 'sd_H100') and x['c12'] is not None), 'date': gpu['asof'], 'u': U + 'gpu_spot_rental/index.html'},
    'china': {'value': f"Chinese labs {cn_share:.0f}% of OpenRouter tokens, week of {last} ({cn_share-cn_prev:+.1f} pp vs 4 weeks earlier); DeepSeek {allsh.get('DeepSeek',0):.1f}% vs OpenAI {allsh.get('OpenAI',0):.1f}%, Anthropic {allsh.get('Anthropic',0):.1f}%", 'date': last, 'u': U + 'openrouter/index.html'},
}
if cap: signposts['capex'] = {'value': cap, 'date': next((d0['asof'] for d0 in dash if d0['id'] == 'dc_buildout'), ''), 'u': U + 'dc_buildout/index.html'}

# ---------- callouts: what changed since the previous run ----------
callouts = []
if PREV:
    pc = {c.get('k'): c for c in PREV.get('calls', []) if c.get('k')}
    for c in calls:
        q = pc.get(c['k'])
        if q and c['n'] is not None and q.get('n'):
            ch = c['n'] / q['n'] - 1
            if abs(ch) >= 0.02: callouts.append({'t': f"{c['l']} {c['v']}, {ch*100:+.1f}% since {PREV.get('asof')} ({q['v']})", 'tone': 'pos' if ch > 0 else 'neg', 'u': ''})
    seen_c = {(x['e'], x['d'], x['src']) for lab in PREV.get('arr', {}).get('labs', {}).values() for x in lab}
    for lab, xs in arr_['labs'].items():
        for x in xs:
            if (x['e'], x['d'], x['src']) not in seen_c: callouts.append({'t': f"New {lab} ARR claim: {('$%.1fbn' % (x['hi']/1000))} ({x['src']}, as of {x['d']})", 'tone': 'inf', 'u': x['u']})
    old_ids = {v for d0 in PREV.get('dash', []) for i in d0.get('items', []) for v in (i.get('id'), i.get('t')) if v}
    for d0 in dash:
        for it in d0['items']:
            if it.get('id') not in old_ids and it['t'] not in old_ids and it['q'] != 'thin data': callouts.append({'t': f"{d0['title']}: {it['t']}", 'tone': 'inf', 'u': it['u']})
if PREV and not callouts:
    callouts.append({'t': 'No change in the AI dashboards since the ' + str(PREV.get('asof')) + ' run.', 'tone': 'inf', 'u': ''})
if not PREV:
    for x in gpu_latest:
        if x['k'] in ('ornn_H100', 'ornn_H200', 'ornn_B200', 'sd_H100', 'sd_B200') and x['c4'] is not None and abs(x['c4']) >= 0.05: callouts.append({'t': f"{x['n']} ${x['v']:.2f}/GPU-hr, {x['c4']*100:+.0f}% over 4 weeks", 'tone': 'pos' if x['c4'] > 0 else 'neg', 'u': U + 'gpu_spot_rental/index.html'})
    callouts.append({'t': signposts['china']['value'], 'tone': 'inf', 'u': signposts['china']['u']})
    callouts.append({'t': f"LLM token prices: broad index ${tok['s'][0]['last']:.2f}/M tokens, {tok['s'][0]['c4']*100:+.0f}% over 4 weeks", 'tone': 'inf', 'u': U + 'silicon_data/index.html'})
callouts = callouts[:12]
for c in callouts: c.setdefault('ticker', 'AI'); c.setdefault('sentiment', {'pos': 'positive', 'neg': 'negative'}.get(c['tone'], 'neutral'))
runs = ([{'asof': PREV.get('asof'), 'built_at': PREV.get('built_at'), 'n_callouts': len(PREV.get('callouts', []))}] + PREV.get('runs', []))[:14] if PREV else []
doc = {'asof': dt.date.today().isoformat(), 'built_at': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M+00:00'),
       'source': 'apps.srsinvest.com/ai (srsinvest-apps S3, read through the SRS MCP s3 tool)',
       'calls': calls, 'callouts': callouts, 'signposts': signposts, 'runs': runs, 'prev_asof': PREV.get('asof') if PREV else None, 'gpu': gpu, 'tok': tok, 'or': orr, 'arr': arr_, 'dash': dash,
       'links': [{'t': t, 'u': 'https://apps.srsinvest.com/ai/' + p + '/index.html'} for p, t in LINKS]}
s = json.dumps(doc, separators=(',', ':'))
open(OUT, 'w').write(s); print('bytes', len(s))
print(json.dumps({'callouts': callouts, 'signposts': signposts}, indent=1))
