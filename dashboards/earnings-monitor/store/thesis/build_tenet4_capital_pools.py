#!/usr/bin/env python3
"""Tenet 4 (Bobby, 2026-11-23): size of each pool of capital (installed base and annual issuance) vs what AI needs,
with GPU-backed loans placed where they sit (private credit / ABS / project finance).
Usage: build_tenet4_capital_pools.py <ai_tenets.json in> <patch.json out>"""
import json, sys

TABLE = {
    'title': 'Pools of capital: installed base, annual issuance and AI\'s draw',
    'cols': ['Market', 'Installed base', 'Annual issuance', 'AI draw', 'What AI uses it for', 'Source'],
    'rows': [
        ['Hyperscaler operating cash flow', '–', 'Our model: $529bn applied to AI capex in 2026, $793bn in 2027', 'Largest single source; MS: >50% of ~$3.8T of 2026-28 hyperscaler AI spend still has to come from credit markets', 'AMZN, MSFT, GOOGL, META, ORCL capex', 'SRS AI Financings; Morgan Stanley'],
        ['US corporate bonds (all)', '$12.1T outstanding (2Q26)', '$2.34T 2026 through Oct (+19.5% y/y)', '–', '–', 'SIFMA, Nov 2'],
        ['Investment grade', '~$25T of debt above the IG line, globally', 'US IG $2.2T through Sep (+25% y/y, MS); our model counts $1.72T', 'Hyperscalers $277bn (16%) + other AI $44bn ≈ 19% of US IG; >$350bn global AI IG YTD (JPM)', 'Hyperscaler and Oracle/SpaceX parent bonds', 'SRS AI Financings; SemiAnalysis (SB 43950); JPM (SB 68573)'],
        ['High yield and leveraged loans', '~$4.5T below the IG line, globally; ~$1T US leveraged loans to private firms', '–', '~$60bn AI leveraged finance YTD; AI HY has had no new deals in a month vs ~$60bn expected', 'Neocloud, miner and developer corporate debt', 'SemiAnalysis; Fed (Aug 2026); JPM; Goldman (SB 68910)'],
        ['Private credit', '$4.1T global AUM end-2025 (+17% y/y, ~$600bn a year of growth); ~$1.4T US. Apollo frames the wider private lending origination market (mortgages, equipment, fleet, trade, corporate) at ~$40T', '–', '>$100bn AI private credit YTD; our model needs $100bn → $200bn → $300bn → $350bn (2026-29)', 'GPU-backed loans, delayed-draw facilities, GPU lease SPVs (e.g. SpaceX/Apollo $40bn)', 'AIMA (Oct 22); Fed; JPM; SRS AI Financings'],
        ['ABS and structured', '–', 'US ABS $440bn 2026 through Oct (SIFMA)', '~$20bn AI structured YTD (JPM); $28.6bn AI-related ABS (Nov 23)', 'Data-center ABS/CMBS refinancing; GPU ABS (largest: SpaceX $32bn secured notes, A3, 8.26%)', 'SIFMA; JPM; AI Build & Financing Sweep'],
        ['Project finance / infrastructure lending', 'Infrastructure funds raised ~$200bn in 2025, a record', '–', '$106bn AI project-finance bonds YTD, ~3x 2025; our model needs $127bn (2026) → $349bn (2027)', 'Data-center campuses (Hut 8, Cipher, TeraWulf; IG-wrapped at ~6-7%)', 'McKinsey; Bloomberg (SB 61318); SRS AI Financings'],
        {'c': ['GPU-backed loans (across the three above)', '–', '$48.4bn committed 2026 vs $6.6bn in 2025', '~47% of AI-infrastructure debt (8% a year ago)', 'Advance rates down from ~80% to 50-60% at mid-to-high-teens rates for mid-market borrowers', 'American Compute (SB 66417); Liquid Compute (SB 69386)'], 'b': 1},
        ['Vendor and customer financing', 'NVDA ~$530bn gross off-balance-sheet guarantees (Q2)', '–', 'Prepayments cover 25-100% of capex at Nebius/IREN; AVGO residual-value support', 'Labs and neoclouds; Nvidia pulling back (neocloud deals cut to $32bn, conditional)', 'Company filings (SB 69006)'],
        ['Equity, converts, preferred', '–', '–', 'Our model: $202bn in 2026; Anthropic IPO ~$64bn + $26bn supplier placement; Meta up to ~$95bn', 'Hyperscaler and lab balance sheets', 'SRS AI Financings'],
        {'c': ['AI need (SRS model)', 'AI debt outstanding >$7T by 2029 (SemiAnalysis)', 'JPM: ~$450bn of AI debt in 2027', 'Sources less uses: +$357bn (2026), +$227bn (2027), −$245bn (2028), −$555bn (2029)', 'JPM sees ~$595bn of funding gaps in 2027-28', 'SRS AI Financings; JPM (SB 69227); SemiAnalysis (SB 28491)'], 'b': 1},
    ],
    'note': 'The pools are big enough: AI is ~19% of US IG issuance off a ~$25T investment-grade base, and private credit grows ~$600bn a year. The strain is in the sub-IG, asset-backed slice, where GPU loans now sit: the HY window has shut, advance rates have dropped, and our model needs private credit and project finance to roughly double in 2027. "Choppy" means the cost and structure of the non-hyperscaler money, not whether capital exists.',
}

DPS = [
    (43950, 1, 'AI CAPEX', '2026-08-24', 'SemiAnalysis: ~$25T of debt above the IG line vs ~$4.5T below; the next AI-debt wave moves to 3-7 year project and equipment financing (secured facilities, private credit, 144A, ABS/CMBS takeout).', 'SemiAnalysis'),
    (68573, 1, 'AI CAPEX', '2026-10-16', 'JPM: AI issuance YTD >$350bn global IG, $60bn leveraged finance, $20bn structured, >$100bn private credit; HY closed to GPU deals; project equity checks must rise from ~10%.', 'JPMorgan credit research'),
    (61318, 1, 'AI CAPEX', '2026-10-19', '$106bn of AI project-finance bonds issued YTD, ~3x all of 2025.', 'Bloomberg'),
    (69227, -1, 'AI CAPEX', '2026-11-18', 'JPM: ~$450bn of AI debt in 2027 (half hyperscaler parents, half GPU/DC financing) and ~$595bn of funding gaps across 2027-28.', 'JPMorgan'),
    (28491, 0, 'AI CAPEX', '2026-07-06', 'SemiAnalysis: AI debt outstanding >$7T by 2029, the second-largest asset-backed market after ~$13T of US mortgages.', 'SemiAnalysis'),
    (42220, 1, 'NVDA', '2026-08-11', 'Apollo, BlackRock, Blackstone, Brookfield, Goldman and KKR to mobilize >$500bn of third-party capital for AI infrastructure with Nvidia (MOUs).', 'Nvidia announcement'),
]

def build(src):
    d = json.load(open(src))
    for t in d['tenets']:
        if t['key'] != 't4': continue
        have = {x['id'] for x in t['dps']}
        t['dps'] += [{'id': i, 'score': s, 't': tk, 'date': dt, 'text': tx, 'src': sr} for i, s, tk, dt, tx, sr in DPS if i not in have]
        t['tables'] = [TABLE] + [x for x in t.get('tables', []) if x.get('title') not in (TABLE['title'], 'Pools of capital the build can draw on')]
    return {'tenets': d['tenets']}

if __name__ == '__main__':
    json.dump(build(sys.argv[1]), open(sys.argv[2], 'w'), ensure_ascii=False); print('ok')
