#!/usr/bin/env python3
"""Tenet 2 (Bobby, 2026-11-23): flag AWS CEO Garman's sold-out comment as a key datapoint, add what every
hyperscaler says about compute supply vs demand (table + Supabase datapoints).
Usage: build_tenet2_hyperscalers.py <ai_tenets.json in> <patch.json out>"""
import json, sys

TABLE = {
    'title': 'What the hyperscalers say about compute supply vs demand',
    'cols': ['Company', 'Supply vs demand', 'Latest statements', 'Date', 'Source'],
    'dir_col': 1,
    'rows': [
        ['Amazon / AWS', '▲ Short through 2028', 'Garman: could sell out every accelerator landing in 2027 today, capacity-short for "a couple of years", already rationing. Jassy: 2026 fully committed, 2027 largely sold out, a good chunk of 2028 pre-sold; most large 2027 capacity booked; backlog ~$580bn; power doubling end-2025 to end-2027.', 'Nov 10 / Nov 20', 'Garman (Sources podcast), Jassy interviews, 3Q26 call'],
        ['Microsoft', '▲ Short, but choosier', 'Demand continues to exceed supply; third-party capacity slipped into 2H so Sep-Q capex was $45.2bn vs ~$50bn guided. Keeping capacity for first-party apps, Foundry and enterprise rather than long GPU-as-a-service deals; walked from some neocloud projects, which the CFO ties to suppliers missing SLAs, not weaker demand.', 'Oct 28 – Nov 18', 'FQ1 FY27 call, CFO meetings at Ignite'],
        ['Alphabet / Google', '▲ Short; power now a limiter', 'Still supply-constrained and renting third-party capacity as a bridge (4Q Cloud margin hit); Argon ramp limited by capacity; Cloud +103% y/y, backlog $561bn. Kuo: 2027 TPU 8i cut by ~1M units on supply and data-center power limits.', 'Oct 28 / Nov 20', '3Q26 call; Ming-Chi Kuo'],
        ['Meta', '▲ Short', 'Compute supply-constrained "for the foreseeable future"; getting offers to buy its compute at multiples of what it paid. (3Q26 call commentary not yet in Supabase.)', 'Jul 29', '2Q26 call (CFO Susan Li)'],
        ['Oracle', '▲ Short', 'OCI capacity for 2027 and 2028 fully committed; demand exceeds supply and component cost increases are passed through; capacity ~3 GW to ~10 GW by FY28.', 'Nov 12 / Sep 10', 'OCI President; F1Q27 call; Investor Day'],
        ['Counterpoints', '■ Watch', 'Rothschild: Amazon has ~8 GW (~4mn GPUs) of 2028 capacity not yet contracted. Microsoft let its 2023 OCI rental of older Nvidia GPUs lapse and passed on doubling its Nscale Texas lease.', 'Nov 5 – 19', 'Rothschild call; FT; press'],
    ],
    'note': 'Every hyperscaler that has spoken since the 3Q prints still says demand exceeds supply. The pushback is on who gets capacity (Microsoft favouring its own workloads) and on older GPUs and uncontracted 2028 capacity, not on demand.',
}

DPS = [
    (62035, 2, 'AMZN', '2026-10-27', "Jassy: AWS 2026 capacity fully committed, 2027 'largely' sold out, a good chunk of 2028 pre-sold; memory and component shortages to last beyond 2027.", 'Andy Jassy, a16z podcast'),
    (69377, 1, 'AMZN', '2026-11-20', 'Jassy: most large 2027 data-center capacity already booked, a substantial share of 2028–29 locked in; AWS backlog ~$580bn.', 'Andy Jassy interview'),
    (64152, 1, 'AMZN', '2026-10-29', 'AWS customers reserve blocks of hundreds of MW up to 1 GW, giving visibility into 2027–28 and some of 2029; AWS power to double from end-2025 to end-2027.', 'Amazon 3Q26 call'),
    (64151, 1, 'AMZN', '2026-10-29', 'Short-term prior-generation Trainium capacity sells at a premium to 1H; Trainium and Graviton commitments each >20x y/y.', 'Amazon 3Q26 call'),
    (62053, 1, 'AMZN', '2026-10-27', 'AI-native CIO: AWS G7e capacity sold out through next year; the alternative instance costs 2–3x, so it signed CoreWeave instead.', 'Cleveland Research'),
    (66553, 1, 'MSFT', '2026-10-30', 'Microsoft: customer demand continues to exceed available supply; still allocating power to first-party models, Copilot and R&D.', 'Microsoft FQ1 FY27 call (via Barclays)'),
    (62456, 1, 'MSFT', '2026-10-28', 'Microsoft Sep-Q capex $45.2bn vs ~$50bn guided because third-party capacity slipped into 2H; CY26 ~$170bn.', 'Microsoft CFO, FQ1 FY27 call'),
    (40487, 1, 'MSFT', '2026-08-06', 'Azure +43% cc, guided 45%; management said customer demand still exceeds supply.', 'Microsoft F4Q26 call (via Mizuho)'),
    (62405, 1, 'GOOGL', '2026-10-28', 'Pichai: 32B API tokens a minute (>4x y/y); more capacity needed to meet demand; Argon ramped 3.5x faster than Gemini 3 despite capacity constraints.', 'Alphabet 3Q26 call'),
    (63472, 1, 'GOOGL', '2026-10-28', 'Google Cloud +103% y/y to $30.7bn, backlog $561bn (from $514bn); 4Q margin pressure from renting third-party capacity.', 'Alphabet 3Q26 call'),
    (38626, 1, 'GOOGL', '2026-07-22', 'Alphabet still supply-constrained; renting third-party capacity as a bridge; 2026 capex raised to $195–205bn.', 'Alphabet 2Q26 call'),
    (38827, 2, 'META', '2026-07-29', "Meta CFO: compute supply-constrained 'for the foreseeable future'; receiving offers to buy its compute at multiples of what Meta paid.", 'Meta 2Q26 call'),
    (68447, 1, 'ORCL', '2026-11-12', 'Oracle OCI President: capacity for 2027 and 2028 is fully committed.', 'Cloud Wars Live'),
    (58557, 1, 'ORCL', '2026-09-10', 'Oracle: demand exceeds supply; component cost increases passed through to customers.', 'Oracle F1Q27 call'),
]

def build(src):
    d = json.load(open(src))
    for t in d['tenets']:
        if t['key'] != 't2': continue
        have = {x['id'] for x in t['dps']}
        for x in t['dps']:
            if x['id'] == 67818:
                x['key'] = True; x['t'] = 'AMZN'
                x['why_key'] = 'The largest cloud saying it is sold out for 2027 and rationing today'
        t['dps'] += [{'id': i, 'score': s, 't': tk, 'date': dt, 'text': tx, 'src': sr} for i, s, tk, dt, tx, sr in DPS if i not in have]
        t['tables'] = [TABLE] + [x for x in t.get('tables', []) if x.get('title') != TABLE['title']]
    return {'tenets': d['tenets']}

if __name__ == '__main__':
    json.dump(build(sys.argv[1]), open(sys.argv[2], 'w'), ensure_ascii=False); print('ok')
