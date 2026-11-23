#!/usr/bin/env python3
"""Tenet 5 (Bobby, 2026-11-23): there will be enough land, power and shells to deploy the chips in our capex model.
Builds the tenet object for page-db doc thesis/ai_tenets: state-by-state direction table, the chips-vs-shells GW gap
table (SRS AI Master Model v14 vs data-center capacity forecasts) and scored Supabase datapoints.
Usage: build_tenet5_power.py <ai_tenets.json in> <patch.json out>   (writes {"tenets": [...]} with Risk 1 moved last)"""
import json, sys

T5 = {
    'key': 't5_power', 'num': '5', 'label': 'Tenet 5', 'sort': 4, 'status': 'watch', 'trend': 'up', 'conviction': 6,
    'title': 'There will be enough land, power and shells to deploy the chips in our capex model',
    'claim': 'Data-center capacity (sites, grid and onsite power, finished shells) keeps up with the GW of accelerators our AI Master Model ships, so chips are not stranded waiting for a home.',
    'srs_view': 'Covered for 2027 (most of it is under construction) but tight for 2028. Before the election, planned capacity ran well ahead of our chips (SemiAnalysis >90 GW of 2028 global adds vs 58.8 GW in our model); after the permit cuts it is ~66 GW, only ~7 GW of slack, and our own US base case (31 GW) needs ~28 GW outside the US. The state picture turned less bad in November: Texas reopened permit reviews, Hinojosa narrowed her pause to new permits and says she does not oppose data centers, and the Texas Senate bill sets conditions rather than a ban.',
    'view': '',
}
T5['view'] = T5['srs_view']

STATES = {
    'title': 'State by state: which way is it moving?',
    'cols': ['State', 'Direction (last 30 days)', 'What changed', 'GW at stake', 'Read for the build'],
    'dir_col': 1,
    'rows': [
        ['Texas', '▲ Better (from a low base)', 'TCEQ resumed permit reviews Nov 17 and issued 8 generating permits (~3.9 GW) Nov 16. Gov.-elect Hinojosa (sworn in Jan 19) on Nov 19–20: "I do not hate data centers"; pause applies to new permits only until laws pass, she cannot stop projects under construction, and she is open to working with Musk "on our terms". Sen. Perry\'s SB 338 (16 co-authors, mostly R) sets conditions (water-saving cooling, water reporting, PUC limits, ≤50% tax breaks) for new sites from Sep 1, 2027. Still open: ERCOT\'s 75 MW+ energization pause until the Dec 10 audit.', '~6.5 GW under construction waiting on ERCOT; 2028 adds cut 20.4 → 15.4 GW (SemiAnalysis)', 'Under-construction capacity grandfathered; new 2028+ sites wait for the 2027 session and cost more (tax, labor, water)'],
        ['Georgia', '▲ Better', 'Effingham County approved OpenAI\'s 3.2 GW Camellia site plan 5–0 (Nov 17) and tabled its moratorium to January; Army Corps wetlands permit pending. Gov.-elect Bottoms still wants a pause.', '3.2 GW Camellia; ~10 GW certified load', 'Certified load proceeds; new state approvals slower in 2027'],
        ['Ohio', '▼ Worse', '~125 local moratoria and 10 town bans (Nov 3); SoftBank booked $3.7bn to unwind turbine reservations tied to PORTS-Pike; governor-elect wants a conditional moratorium.', '~8–10 GW PORTS-Pike (OpenAI)', 'Largest single OpenAI site is the one most at risk'],
        ['Virginia', '▼ Worse', 'Loudoun adopted an up-to-12-month pause on data-center/substation applications (7-1-1, Nov 17; 33 applications); state consumption tax; Prince William cut its overlay to ~3,600 acres.', '11.4 GW active (Jefferies)', 'Still the largest market; growth limited to already-zoned land'],
        ['New Mexico', '▼ Worse', 'Jupiter air-permit hearing vacated; SemiAnalysis sees approval Aug–Oct 2027; HSBC sold its loan slice at ~85.', '2.45 GW Jupiter (Oracle/OpenAI)', 'Slips past its 2028 start'],
        ['Michigan', '▼ Worse', 'Bills would bar permits until Apr 2027; ~96 local moratoria; Saline first grid power moved to end-2027.', '974 MW Saline (Oracle)', 'About two quarters late'],
        ['Arizona', '■ Contested', 'AG Mayes asked Cochise County to postpone the Dec 9 vote on SpaceX\'s 6 GW campus; only 625 MW of named supply; new incentive applications paused to Jun 2029.', 'Up to 6 GW (SpaceX)', 'Watch Dec 9'],
        ['Wisconsin', '■ Credit-gated', 'Very-large-customer tariff needs an A-/A3 rating or cash collateral; Lighthouse 2027 cut to 310 MW from 650 MW on power approval (TrendForce).', '1.3 GW Lighthouse in 2028', 'Open to strong credits'],
        ['New York', '■ Paused', 'Executive-order pause on 50 MW+ (to Jul 2027).', '~0.8 GW', 'Small exposure'],
        ['Pennsylvania', '■ Conditions', 'Build, bring or buy your own power (Aug 18 EO).', '', 'Different terms, not a ban'],
        ['Louisiana / Kentucky / Wyoming', '▲ Better', 'Hut 8 River Bend under way (gas on site); Kentucky Power filed a 760 MW CCGT for TeraWulf; Google $17bn Laramie campus.', '', 'Capacity moving to friendly states'],
        ['Outside the US', '▲ Better', 'CoreWeave added 1.3 GW abroad; Cerebras puts ~75% of 2027 capacity outside the US; Malaysia has 15–20 GW of 2027–28 plans (now needs US export licences).', '', 'Has to absorb ~28 GW in 2028 in our base case'],
    ],
    'note': 'Direction = whether the last 30 days of news made it easier (▲) or harder (▼) to build. Sources: Supabase datapoints below, AI › Data centers & politics, Texas Tribune / KCBD / Longbridge on Hinojosa (Nov 19–20).',
}

GAP = {
    'title': 'Chips vs shells: GW our capex model needs vs GW that can be built',
    'cols': ['GW added in the year (critical IT)', '2026', '2027', '2028', '2029', 'Source'],
    'rows': [
        {'c': ['Chips (demand)', '', '', '', '', ''], 'h': 1},
        {'c': ['Accelerator power shipped (units × chip power), global', '24.3', '44.0', '73.5', '97.5', 'AI Master Model v14, XPU Model']},
        {'c': ['GW our capex model deploys (×0.8; ×0.7 in 2029), global', '19.5', '35.2', '58.8', '68.2', 'AI Master Model v14, Overview row 65'], 'b': 1},
        {'c': ['Wolfe, chip-level GW shipped', '–', '41', '64', '–', 'Wolfe, Nov 13 (SB 69550)']},
        {'c': ['Shells (supply)', '', '', '', '', ''], 'h': 1},
        {'c': ['SemiAnalysis Datacenter Model, global, before the cut', '–', '–', '>90', '–', 'SB 68416']},
        {'c': ['SemiAnalysis Datacenter Model, global, after the Nov 13 cut', '–', '–', '~66', '+~21 slips in', '>90 less 24.1 GW cut (SB 68416)'], 'b': 1},
        {'c': ['SemiAnalysis, US, before the election', '<19', '~38–40', '62.2', '–', 'SB 66102']},
        {'c': ['SRS base case, US (bear / bull)', '16 (14 / 17)', '26 (19 / 33)', '31 (18 / 42)', '33 (22 / 45)', 'AI › Data centers & politics'], 'b': 1},
        {'c': ['Morgan Stanley, US', '–', 'unchanged', '19.9', '27.6', 'SB 68026']},
        {'c': ['Jefferies deployments', '16–18', '~27', '~40', '–', 'SB 68956']},
        {'c': ['Wolfe, data-center level (facility power)', '–', '60', '87', '–', 'SB 69550']},
        {'c': ['Gap', '', '', '', '', ''], 'h': 1},
        {'c': ['Chips shipped but not deployed in our model (haircut)', '4.9', '8.8', '14.7', '29.3', 'Model line 1 less line 2']},
        {'c': ['Shell slack vs our model, global (SemiAnalysis after cut less our GW)', '–', '–', '+~7', '–', '~66 less 58.8'], 'b': 1},
        {'c': ['GW our model needs outside the US if the US hits our base case', '3.5', '9.2', '27.8', '35.2', 'Model GW less SRS US base'], 'b': 1},
        {'c': ['US share of our model GW implied by our US base case', '82%', '74%', '53%', '48%', 'US base ÷ model GW (US has been ~70%)']},
    ],
    'note': 'Before the election planned capacity ran well ahead of our chips (SemiAnalysis >90 GW of 2028 global adds vs 58.8 GW in our model), so land and power were not the constraint. After the permit cuts the slack is ~7 GW, and our own US base case leaves ~28 GW to be built abroad in 2028, about double the ex-US share so far. 2027 is covered: ~75% of it is already under construction. Mixed bases: chip GW are global and calendar-year; SRS, Morgan Stanley and pre-vote SemiAnalysis shell figures are US only; Wolfe data-center GW are facility power, not critical IT.',
}

DPS = [  # (id, score, ticker, date, text, src)
    (69536, 2, 'VRT', '2026-11-20', 'Cleanview: 58 GW of US data-center capacity under construction, ~2x y/y, vs 65 GW built in the last ~30 years.', 'Cleanview tracker'),
    (68416, -2, 'NVDA', '2026-11-13', 'SemiAnalysis cut 24.1 GW from global 2028 additions (from >90 GW); ~21 GW pushed into 2029–32, 385 buildings delayed a median 3 quarters. Hyperscaler self-builds mostly untouched.', 'SemiAnalysis Datacenter Model'),
    (68977, -2, 'VRT', '2026-11-17', 'Citi reviewed ~50 projects under construction (TX, VA, PA, OH, GA) and sees a possible 30–35% GW reduction; applies a 30% haircut to its >150 GW 2026–30 model.', 'Citi'),
    (69550, 1, 'NVDA', '2026-11-13', 'Wolfe: chip-level shipments ~41 GW (2027) and ~64 GW (2028), data-center level ~60/87 GW; >80 GW of US power online in 2027, no large shortfall.', 'Wolfe Research'),
    (69391, 1, 'TX', '2026-11-17', 'Texas TCEQ resumed data-center permit reviews, ending the Sep 21 halt; ERCOT findings go to the PUCT Dec 10.', 'TCEQ statement'),
    (68920, 1, 'TX', '2026-11-16', 'TCEQ issued 8 generating-unit permits (~3.9 GW) in one day vs 0–1 a day before; 1.6 GW of data-center capacity approved, possibly 1.6 GW more.', 'SemiAnalysis'),
    (68607, 1, 'TX', '2026-11-05', 'Hinojosa: the moratorium covers new permits, not projects under construction.', 'Texas Gov.-elect Hinojosa'),
    (68733, -1, 'TX', '2026-11-16', 'ERCOT paused energization of 75 MW+ loads until its Dec 10 audit; ~6.5 GW under construction in Texas is exposed.', 'BofA'),
    (68417, -1, 'TX', '2026-11-13', 'SemiAnalysis cut Texas 2028 additions to 15.4 GW from 20.4 GW, dropping ERCOT studied-load sites.', 'SemiAnalysis'),
    (68904, -1, 'TX', '2026-11-16', 'ERCOT kept ~200 projects (66.4 GW) in line and shut out >350 (>300 GW); ~170 GW still waiting.', 'Latitude analysis'),
    (68488, 1, 'HUT', '2026-11-11', 'Hut 8 filed Beacon Point (1 GW) as one energization application; Texas policy risk is mainly for projects beyond 2028.', 'Hut 8 CEO'),
    (68601, 1, 'FRMI', '2026-11-04', 'Fermi Matador has its 6 GW air permit and needs no local permits; behind-the-meter in SPP, outside the ERCOT queue.', 'Fermi IR'),
    (69215, 1, 'OpenAI', '2026-11-17', 'Effingham County (GA) approved OpenAI\'s 3.2 GW Camellia site plan 5–0 and tabled its moratorium to January.', 'Effingham County vote'),
    (69147, -1, 'VA', '2026-11-17', 'Loudoun County adopted an up-to-12-month pause on data-center/substation applications; 33 applications affected.', 'Loudoun County board'),
    (68914, -1, 'OpenAI', '2026-11-16', 'All of OpenAI\'s ~14 GW of planned US capacity is in states whose governors back a pause (MSFT ~45%, AMZN ~42%, ANTH/GOOGL ~20s%).', 'WSJ (Cleanview)'),
    (69369, -1, 'SPCX', '2026-11-19', 'Arizona AG asked Cochise County to postpone the Dec 9 vote on SpaceX\'s 6 GW campus; only 625 MW of named supply.', 'Arizona AG'),
    (66334, -1, 'ORCL', '2026-11-06', 'Lighthouse (WI) 2027 capacity cut to 310 MW from 650 MW on power approval; 1.3 GW kept for 2028.', 'TrendForce'),
    (66433, -1, 'ORCL', '2026-11-09', 'Saline (MI) first grid power moved to end-2027; 974 MW ramp runs through 2028.', 'SemiAnalysis'),
    (68158, -1, 'CBRS', '2026-11-12', 'Cerebras: OpenAI\'s first capacity tranches are behind on land, power and shells; back on schedule 2H27.', 'Cerebras mgmt'),
    (66059, -1, 'SMCI', '2026-11-03', 'Supermicro: 2H FY27 moderation reflects customer data-center readiness (land, power, shells), not demand.', 'Supermicro mgmt'),
    (69056, -1, 'NVDA', '2026-11-17', 'Dylan Patel: water, wastewater and air permits, not labor or equipment, are pushing GW of US capacity from 2027 into 2028; Cerebras puts ~75% of 2027 capacity outside the US.', 'SemiAnalysis / Cerebras'),
    (66388, -1, 'nscale', '2026-11-05', 'Microsoft cancelled a ~$3bn Nscale UK deal over multiyear grid-power delays.', 'Press reports'),
    (68128, -1, 'FRMI', '2026-11-12', 'Fermi first power slipped to late 2Q/early 3Q27 from ~1Q27; 640 MW by 4Q27 not reiterated.', 'Fermi mgmt'),
    (69331, 1, 'DLR', '2026-11-19', 'Digital Realty: ~1.5 GW under development is mostly permitted; pauses unlikely to hit approved projects.', 'Digital Realty mgmt'),
    (69277, 1, 'EQIX', '2026-11-19', 'Equinix: 700 MW pipeline substantially approved, permitted and powered.', 'Equinix mgmt'),
    (69465, 1, 'MOD', '2026-11-18', 'Modine: customer projects largely approved and permitted through 2029; no change from moratoriums.', 'Modine mgmt'),
    (68718, 1, 'STRL', '2026-11-16', 'Sterling: backlog projects already have master permits; pauses would not affect them.', 'Sterling CEO'),
    (69388, 1, 'CRUSOE', '2026-11-19', 'Crusoe: >6 GW under contract or in development vs ~2 GW at end-2025.', 'Crusoe CEO'),
    (68372, 1, 'NBIS', '2026-11-12', 'Nebius: >4 GW of contracted power, 5 GW year-end target; >1 GW added a year from 2027.', 'Nebius mgmt'),
    (67801, 1, 'CRWV', '2026-11-10', 'CoreWeave added 1.3 GW outside the US (Indonesia, India, Spain, Denmark, Canada).', 'CoreWeave 3Q26 call'),
    (69232, 1, 'SPCX', '2026-11-18', 'SpaceX adding ~0.5 GW of compute a month, >1 GW a month by end-2027 (targets).', 'Elon Musk'),
    (66416, 1, 'ANTH', '2026-11-08', 'Anthropic bought 1.7 GW of Caterpillar gas gensets ($3.4bn): behind-the-meter power outside the grid queue.', 'FT'),
    (67196, 1, 'CAT', '2026-11-10', 'SemiAnalysis: behind-the-meter power is $690bn (53%) of ~$1.3T of 2026–30 data-center US energy capex.', 'SemiAnalysis Energy Model'),
    (68233, 1, 'ENR GR', '2026-11-12', 'Siemens Energy adding ~8 GW a year of gas-turbine capacity from FY27; grid transformer and switchgear capacity +50% by 2030.', 'Siemens Energy'),
    (67918, 1, 'ENR GR', '2026-11-11', 'Gas-turbine market additions ~145 GW in FY26 and 130–150 GW a year FY27–30.', 'Siemens Energy'),
    (68727, 1, 'BE', '2026-11-16', 'Bloom capacity >2 GW at YE26, +200–300 MW a quarter.', 'Bloom mgmt'),
    (68441, 1, 'ORCL', '2026-11-12', 'Oracle: OCI 2027–28 capacity fully committed; long turbine lead times pushed it to VoltaGrid engines plus batteries.', 'Oracle OCI President'),
    (69170, -1, 'SPCX', '2026-11-17', 'Turbine blade/vane lead times now 18–24 months vs 12–18 months a quarter ago.', 'SpaceX CFO'),
    (68705, -1, 'ENR GR', '2026-11-16', 'Large power transformers ~10% undersupplied through 2030.', 'Siemens Energy'),
    (67903, -1, 'NRG', '2026-11-11', 'ERCOT North forwards fell after the midterms on data-center delay fears: 2027 ~$39/MWh vs ~$58 a year ago.', 'NRG'),
    (68956, 0, 'NVDA', '2026-11-16', 'Jefferies channel checks: 16–18 GW of data-center deployments in 2026, ~27 GW in 2027, ~40 GW in 2028 (wide cone).', 'Jefferies'),
    (68707, 0, 'VST', '2026-11-16', 'Vistra: 4–6% ERCOT load growth through 2030, but near-term Texas load slower; interconnection queues overstated.', 'Vistra mgmt'),
]
STAGED = [  # not yet in Supabase
    {'t': 'TX', 'date': '2026-11-20', 'text': 'Hinojosa: "I do not hate data centers. I just hate the way they are currently exploiting the people of Texas"; wants a pause on new permits until laws pass and is open to working with Musk.', 'primary': 'Gov.-elect Gina Hinojosa interview', 'secondary': 'Longbridge, 2026-11-20'},
    {'t': 'TX', 'date': '2026-11-19', 'text': 'Hinojosa: ban on new data-center permits until laws protect Texans; concedes she cannot stop projects already under construction; says industry contacts find that reasonable.', 'primary': 'Hinojosa on Fox News, 2026-11-19', 'secondary': 'KCBD, 2026-11-20'},
    {'t': 'TX', 'date': '2026-11-19', 'text': 'Sen. Perry filed SB 338 (16 co-authors): new data centers from Sep 1, 2027 must use water-saving cooling, report water use; PUC sets water/noise/setback limits; tax breaks capped at 50%. Conditions, not a ban.', 'primary': 'Texas SB 338', 'secondary': 'KCBD, 2026-11-20'},
]

def build(src):
    d = json.load(open(src))
    ten = [t for t in d['tenets'] if t['key'] != 't5_power']
    t5 = dict(T5)
    t5['tables'] = [GAP, STATES]
    t5['dps'] = [{'id': i, 'score': s, 't': tk, 'date': dt, 'text': tx, 'src': sr} for i, s, tk, dt, tx, sr in DPS]
    t5['staged'] = STAGED
    for t in ten:
        if t.get('kind') == 'risk': t['sort'] = 5
    ten.append(t5)
    ten.sort(key=lambda t: t.get('sort', 0))
    return {'tenets': ten}

if __name__ == '__main__':
    out = build(sys.argv[1]); json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False)
    print([(t['key'], t.get('label'), t.get('sort')) for t in out['tenets']], len(DPS), 'datapoints')
