#!/usr/bin/env python3
"""Tenet 3 (Bobby, 2026-11-23): closed frontier models dominate. Distillation blocking and China losing access to
Nvidia compute count as positives; Artificial Analysis scoreboard added as a table and datapoints.
Usage: build_tenet3_frontier.py <ai_tenets.json in> <patch.json out>  (tenets array with t2 changes already applied is fine)"""
import json, sys

TABLE = {
    'title': 'Frontier scoreboard: closed labs vs open / China models',
    'cols': ['Measure', 'Leader (closed)', 'Other closed', 'Best open / China', 'Gap', 'Source'],
    'rows': [
        ['AA Progress Index (Oct 29)', 'Gemini 4 Carbon 352', '–', 'Kimi K3.1 Pro 341 (weights not released); DeepSeek V4.1 Flash 324 (best released weights)', 'Kimi ~2 months; DeepSeek ~5 months (a closed model hit 324 in June)', 'Artificial Analysis (SB 64298, 64297)'],
        ['AA Intelligence Index v5', 'Gemini 4 Carbon 59', 'Opus 5.5 leads the coding-agent index (62 vs Carbon 59)', 'Kimi K3.1 55', '4 points', 'Artificial Analysis (SB 64076, 64330)'],
        ['HLE-Diamond', 'Gemini 4 Carbon 69%', 'Opus 5.5 68%', 'Kimi K3.1 Pro 37%', '>30 points', 'Artificial Analysis (SB 64293)'],
        ['Real World Engineering Bench (pass@5)', 'Opus 5.5 ~70%', 'GPT-6 Astra ~60%', 'Kimi K3.1 Pro ~5%', '~65 points', 'Xplore AI (SB 64067)'],
        ['Cost per AA task', 'GPT-6 Astra $6.25', 'Gemini 4 Carbon $7.76; Opus 5.5 $10.04', 'Kimi K3.1 ~$1.98', 'Open ~3-5x cheaper', 'Artificial Analysis (SB 64317, 64330)'],
    ],
    'note': 'Closed labs hold every top spot. On broad indices the best China model looks ~2 months behind, but it was reportedly distilled from GPT-6 Astra and falls far behind on hard, real-world engineering and reasoning tasks, which is where the revenue is. The open-model threat is price (3-5x cheaper per task) and enterprise token volume, not the frontier.',
}

DPS = [  # (id, score, ticker, date, text, src)  — new or rescored
    (69035, 1, 'ANTH', '2026-11-18', 'Anthropic: distillation by bad actors was 5-7% of revenue before it started blocking it in Aug 2026; cutting off distillation removes the cheapest route for open models to catch up.', 'Anthropic'),
    (61255, 1, 'ANTH', '2026-10-14', 'Anthropic: distillation fell from 5-7% of revenue to near zero by quarter-end after blocking.', 'Anthropic investor session (via SemiAnalysis)'),
    (69379, 1, 'NVDA', '2026-11-20', 'Barclays: recent token-demand slowdown partly a one-time distillation crackdown.', 'Barclays AI industry model'),
    (64108, 0, 'DEEPSEEK', '2026-10-29', 'DeepSeek V4.1 Flash reportedly trained extensively on GPT-6 Astra outputs (distillation).', 'The Information'),
    (69096, 2, 'NVDA', '2026-11-18', 'SemiAnalysis: Nvidia no longer shipping licensed H200 to China; all H200 removed from 4Q26 onward.', 'SemiAnalysis'),
    (68200, 1, 'NVDA', '2026-11-12', 'Nvidia AI shipments to China now de minimis: the US allows H200, but Beijing restricts its use.', 'Wolfe Research'),
    (69142, 2, '700 HK', '2026-11-18', "Tencent: the BIS remote-access rule 'sets everyone back' in China and delays its next-model training.", 'Tencent 3Q26 call (Martin Lau)'),
    (69235, 1, 'MOONSHOT', '2026-11-19', 'Moonshot reportedly cancelled a $150M B300 rental in Indonesia after the BIS remote-access rule.', 'The Information'),
    (68921, 1, 'NVDA', '2026-11-17', 'UBS: the BIS remote-access rule removes ~1-2 GW of current AI capacity, mostly serving China-domiciled firms.', 'UBS'),
    (69102, 1, 'NVDA', '2026-11-18', 'SemiAnalysis: ~1 GW freed by the remote-access rule would be absorbed by Anthropic, OpenAI and startups.', 'SemiAnalysis'),
    (69334, 1, 'TSM', '2026-11-19', 'TSMC halted ≤16nm orders from China designers without a US licence (BIS rule): limits Chinese AI chips too.', 'Reuters'),
    (64076, 1, 'GOOGL', '2026-10-28', 'Artificial Analysis: Gemini 4 Carbon 59 on the Intelligence Index v5, top model; Opus 5.5 leads the coding-agent index (62 vs 59).', 'Artificial Analysis'),
    (64297, 1, 'DEEPSEEK', '2026-10-29', 'Best released open-weight model (DeepSeek V4.1 Flash, 324 AA Progress) only matches where a closed model was in June: ~5 months behind.', 'Artificial Analysis'),
    (64330, -1, 'MOONSHOT', '2026-10-23', 'Kimi K3.1 scores 55 on the AA Intelligence Index (vs Carbon 59) at ~$1.98 per task, 3-5x cheaper than closed models.', 'Artificial Analysis'),
]

def build(src):
    d = json.load(open(src))
    for t in d['tenets']:
        if t['key'] != 't3': continue
        byid = {x['id']: x for x in t['dps']}
        for i, s, tk, dt, tx, sr in DPS:
            if i in byid: byid[i].update({'score': s, 'text': tx, 'src': sr, 't': byid[i].get('t') or tk})
            else: t['dps'].append({'id': i, 'score': s, 't': tk, 'date': dt, 'text': tx, 'src': sr})
        for x in t['dps']:
            if x['id'] == 64067:
                x['key'] = True; x['why_key'] = 'On hard real-world engineering work the best China model scores ~5% vs ~70% for Opus'
        t['tables'] = [TABLE] + [x for x in t.get('tables', []) if x.get('title') != TABLE['title']]
    return {'tenets': d['tenets']}

if __name__ == '__main__':
    json.dump(build(sys.argv[1]), open(sys.argv[2], 'w'), ensure_ascii=False); print('ok')
