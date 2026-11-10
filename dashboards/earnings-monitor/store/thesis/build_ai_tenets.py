#!/usr/bin/env python3
"""Build the AI thesis 'By tenet' data: page-db doc thesis/ai_tenets and Supabase SQL
(thesis_tenets + thesis_tenet_evidence). Datapoint text is a short display form of the stored
research_evidence row; the row itself is the record."""
import json, pathlib

OUT = pathlib.Path(__file__).parent
TODAY = "2026-11-10"
S = "supports"; C = "challenges"; M = "mixed"

def dp(id, date, t, impact, stance, text, src):
    return dict(id=id, date=date, t=t, impact=impact, stance=stance, text=text, src=src)

TENETS = [
 dict(key="lab_arr", title="OpenAI + Anthropic revenue keeps compounding", status="weakening",
  claim="The two labs scale ARR fast enough to stay the incremental buyer of compute (deck: 7x in a year to ~$140bn by Sep-26).",
  srs_view="OpenAI is falling off.",
  checks=[
   dict(claim="OpenAI is falling off", verdict="partly", text="Losing share and raising less, not shrinking. SoftBank discloses OpenAI ARR of ~$50bn at Sep-26 vs Anthropic above $80bn in October. OpenAI's raise came in at ~$11bn on first close against $30bn+ first sought. But OpenAI ARR still grew 70%+ in Jul–Sep and enterprise doubled (CFO Friar).", sources=[["SoftBank 2Q FY3/27 results (SB #67052)", ""], ["24/7 Wall St., 2026-11-07", "https://247wallst.com/investing/2026/11/07/openai-just-raised-11-billion-at-a-1-25-trillion-valuation-below-the-1-4-trillion-it-first-sought/"]]),
  ],
  dps=[
   dp(67052, "2026-11-10", "9984 JP", "positive", M, "SoftBank: OpenAI ARR ~$50bn at Sep-26, up 70%+ in Jul–Sep; enterprise 50% of revenue; ads ARR $1bn.", "SoftBank 2Q FY3/27 results"),
   dp(66353, "2026-11-06", "ANTH", "positive", S, "Anthropic annualized revenue topped $80bn in October; ~$8bn net new vs September (TMTB calc), back to the Jun–Jul pace.", "WSJ"),
   dp(64181, "2026-10-29", "ANTH", "mixed", M, "Anthropic net new ARR ~$10bn/month in 2Q vs ~$4bn in 3Q; $8–10bn expected in 4Q after Opus 5.5.", "Anthropic S-1 via SemiAnalysis"),
   dp(65875, "2026-11-02", "ANTH", "positive", S, "Anthropic Q3 revenue nearly $17bn, ~12x y/y, +47% q/q (amended S-1).", "Anthropic amended S-1"),
   dp(65531, "2026-11-02", "OpenAI", "negative", C, "OpenAI cut its fundraising target to $20bn from $30bn after some investors reduced commitments.", "FT via The Bear Cave / TMTB"),
   dp(65838, "2026-11-02", "CBRS", "negative", C, "SemiAnalysis drops Cerebras' 1.25GW OpenAI tranche: OpenAI unlikely to upsize to 2GW; capacity plateaus ~750MW by end-2028.", "SemiAnalysis"),
   dp(67065, "2026-11-09", "OpenAI", "positive", S, "OpenAI ads reached a $1bn run rate by Aug-26, <200 days after launch; revenue now ~50/50 consumer/enterprise.", "OpenAI CFO Sarah Friar, CNBC"),
  ],
  staged=[dict(t="OpenAI", date="2026-11-06", impact="negative", field_key="risk", source_type="news", confidence="medium",
     text="OpenAI received ~$11B by 2026-11-06 as the first part of a round at a $1.25T pre-money valuation (confirmed by CFO Friar), vs ~$1.4T and $30B+ initially sought; the round may total up to ~$20B. SoftBank and MGX participated.",
     primary="OpenAI CFO Sarah Friar (TV interview); people familiar with the deal", secondary="24/7 Wall St., 2026-11-07, 'OpenAI Just Raised $11 Billion at a $1.25 Trillion Valuation'",
     why="Updates SB #65531 (target cut to $20bn) with the actual first close and valuation.")]),

 dict(key="roi", title="Lab ARR justifies the spend (15% ROIC)", status="weakening",
  claim="Deck ROIC model: oAI+ANTH need ~$195bn combined ARR exiting 2026, ~$452bn in 2027 and ~$737bn in 2028 at ~70% GM for the industry to earn 15% on capex.",
  srs_view="Anthropic's acceleration is not enough to get our combined new ARR to justify return on spend.",
  checks=[
   dict(claim="Anthropic's acceleration is not enough for combined ARR to justify the return on spend", verdict="supported", text="SRS calc on the deck's own model. Combined ARR is ~$130bn today: Anthropic above $80bn in October plus OpenAI ~$50bn in September. At ~$15bn/month of combined net new ARR (Anthropic ~$8bn in October, OpenAI ~+70% q/q in Q3), the labs exit 2026 at ~$165–175bn vs the model's $195bn. Reaching $452bn in 2027 needs ~$21bn/month all year. Anthropic is back at its Jun–Jul pace, but that alone does not close the gap.", sources=[["SRS AI Update, Oct 2026, slides 9–10", ""], ["SB #66353, #67052, #64181", ""]]),
  ],
  dps=[
   dp(64181, "2026-10-29", "ANTH", "mixed", M, "Anthropic 2Q gross margin ~88% excl. training and non-GAAP EBIT margin +11%, vs the deck's ~70% GM assumption (definitions may differ).", "Anthropic S-1 via SemiAnalysis"),
   dp(66353, "2026-11-06", "ANTH", "positive", M, "Anthropic ~$8bn net new ARR in October: back to the Jun–Jul pace, but below the ~$21bn/month combined pace the 2027 ROIC path needs.", "WSJ / TMTB"),
   dp(67052, "2026-11-10", "9984 JP", "positive", C, "OpenAI ~$50bn ARR at Sep-26 (SoftBank) vs deck assumptions; combined ~$130bn vs $195bn needed exiting 2026.", "SoftBank 2Q FY3/27 results"),
   dp(65687, "2026-10-28", "ORCL", "positive", S, "Oracle illustrative 1GW AI project: ~$37bn capex, ~$16bn revenue/yr fully ramped (vs ~$10bn/GW cited in 2025); cost-plus contracts at ~35% GM.", "Oracle Investor Day"),
   dp(66850, "2026-11-02", "MSFT", "negative", C, "Microsoft D&A 12.7% of revenue in 1Q27 vs 11.6% FY26; 75% of $45.2bn capex went to shorter-lived CPUs/GPUs.", "Microsoft 1Q27 results"),
  ], staged=[]),

 dict(key="compute_tight", title="Compute is constrained (GPU rental prices and IRR)", status="strengthening",
  claim="Rising GPU rental prices and ~30% rental IRRs show demand exceeds supply.",
  srs_view="", checks=[],
  dps=[
   dp(66397, "2026-11-09", "NVDA", "positive", S, "RBC GPU rental tracker (Oct-26, 65+ providers): median on-demand price +5.7% m/m; 2025-generation GPUs +9.5% m/m.", "RBC Capital Markets"),
   dp(66361, "2026-11-05", "IREN", "positive", S, "IREN contract pricing +11% (3-yr) and +12% (5-yr); H100s re-contracted at double prior pricing; short-term deal at $40m revenue per IT-MW.", "IREN Q1 FY27 results"),
   dp(66362, "2026-11-05", "IREN", "positive", S, "IREN 5-yr contract at ~$22m/IT-MW with the customer prepaying 90% of GPU capex (vs 45–55% in recent deals).", "IREN Q1 FY27 results"),
   dp(65673, "2026-11-02", "NVDA", "positive", S, "B300 median on-demand rental $9.15/GPU-hr, +14% over 90 days; reserved $5.99, spot $5.53.", "GetDeploying data"),
   dp(66250, "2026-11-05", "CRWV", "positive", S, "CoreWeave mostly sold out for 2027; offering mid-tier labs only small slots.", "SemiAnalysis"),
   dp(65967, "2026-11-02", "CRWV", "negative", M, "NVDA reportedly cutting neocloud Vera Rubin allocations by up to 50%, reallocating racks to SpaceX, which is selling >1GW into the rental market: rental-price pressure for neoclouds without IG offtakers.", "SemiAnalysis"),
  ], staged=[]),

 dict(key="capex", title="Hyperscalers are all-in", status="intact",
  claim="The best-informed executives at Amazon, Microsoft, Google and Meta keep putting massive capital behind AI.",
  srs_view="", checks=[],
  dps=[
   dp(66113, "2026-11-04", "NVDA", "positive", S, "Hyperscaler capex +87% y/y in 3Q to ~$217bn.", "Hyperscaler 3Q26 reported capex"),
   dp(63479, "2026-10-28", "GOOGL", "mixed", S, "Alphabet 3Q capex $51.4bn; FY26 $195–205bn vs $91bn in 2025; 2027 to 'increase significantly'; FCF −$9.1bn.", "Alphabet 3Q26 call"),
   dp(64142, "2026-10-29", "AMZN", "mixed", S, "Amazon 2026 cash capex ~$220bn after $75.9bn in 3Q; 'meaningfully more' in 2027.", "Amazon 3Q26 call"),
   dp(64059, "2026-10-29", "MSFT", "mixed", S, "Microsoft calendar-2026 capex ~$170bn; Q2 FY27 >$50bn; delayed third-party capacity shifts into fiscal H2.", "Microsoft FQ1 FY27 call"),
   dp(66216, "2026-11-05", "MSFT", "negative", C, "Microsoft spent ~$5bn less capex than planned in the Sep-Q because third-party data centers were late (IREN Childress a contributor).", "The Information"),
   dp(66389, "2026-11-05", "MSFT", "mixed", C, "Microsoft tightening oversight of some Nebius, IREN and Nscale projects and debating whether to sign new neocloud deals.", "Bloomberg"),
  ], staged=[]),

 dict(key="financing", title="Financing holds up", status="weakening",
  claim="Hyperscaler shortfalls are covered by credit and equity markets; neocloud gaps are backstopped by AVGO/NVDA guarantees.",
  srs_view="SoftBank didn't even want to invest: OpenAI's valuation went from $1.4 trillion to $1.2 trillion and it is only raising $11 billion. SoftBank is cancelling turbines.",
  checks=[
   dict(claim="SoftBank didn't even want to invest", verdict="not_supported", text="SoftBank and Abu Dhabi's MGX took part in the ~$11bn first close (people familiar with the deal). A separate headline says SoftBank weighed adding under $1bn to its $64.6bn position, but we could not verify it. Either way the participation is small next to its existing stake. SoftBank still carries OpenAI at a $730bn pre-money mark.", sources=[["24/7 Wall St., 2026-11-07", "https://247wallst.com/investing/2026/11/07/openai-just-raised-11-billion-at-a-1-25-trillion-valuation-below-the-1-4-trillion-it-first-sought/"], ["FourWeekMBA headline (unverified)", "https://fourweekmba.com/ai-softbank-said-to-weigh-adding-under-1b-to-64-6b-openai-bet/"], ["SB #67052", ""]]),
   dict(claim="Valuation cut from $1.4tn to $1.2tn and only raising $11bn", verdict="mostly", text="The round is at $1.25tn pre-money (CFO Friar confirmed on TV), vs ~$1.4tn first sought. ~$11bn had reached OpenAI by 2026-11-06 as the first part; the round could total up to ~$20bn, vs $30bn+ first sought and the cut $20bn target.", sources=[["24/7 Wall St., 2026-11-07", "https://247wallst.com/investing/2026/11/07/openai-just-raised-11-billion-at-a-1-25-trillion-valuation-below-the-1-4-trillion-it-first-sought/"], ["SB #65531", ""]]),
   dict(claim="SoftBank is cancelling turbines", verdict="partly", text="SoftBank took a ¥597.2bn (~$3.7bn) 2Q FY3/27 charge for realigning its power-generation equipment purchases: $2.9bn of non-refundable deposits on purchases dropped from the revised plan, plus ~$0.9bn of contract modifications and settlements. $6.6bn stays allocated (PORTS-Pike, Ohio, which the CFO says is not being downsized). The CFO called Musk's 'defaulting on turbine orders' claim incorrect ('There is no such default'). The supplier was not named.", sources=[["The Deep Dive, 2026-11-10", "https://thedeepdive.ca/softbank-denies-elon-musks-turbine-default-claim-amid-3-7-billion-loss/"], ["SB #67053", ""]]),
  ],
  dps=[
   dp(67053, "2026-11-10", "9984 JP", "negative", C, "SoftBank ¥597.2bn ($3.7bn) loss on realigning power-generation equipment for US AI data centers: ¥457.0bn non-refundable advances plus ¥140.2bn contract modifications/settlements.", "SoftBank 2Q FY3/27 results"),
   dp(66244, "2026-11-05", "NBIS", "negative", C, "Nebius CEO: asset-backed and debt markets 'temporarily closed' for some sources of capital.", "Nebius CEO, GTC Berlin"),
   dp(66295, "2026-11-06", "ORCL", "negative", C, "Oracle's five new tranches priced 35–41bp wide of its curve; the 2046s yield 8.67%, spread roughly level with the US HY index.", "SemiAnalysis (Bloomberg data)"),
   dp(66229, "2026-11-04", "ORCL", "negative", C, "Oracle closed 86.2m shares plus $10bn of notes (7.000–8.650% coupons, 2029–2046).", "Oracle 8-K"),
   dp(65566, "2026-11-02", "AVGO", "negative", C, "Blackstone now expects Anthropic to be rated junk after its IPO, affecting the $63bn TPU package (>$42bn senior debt Broadcom-guaranteed).", "Financial Times"),
   dp(66296, "2026-11-06", "META", "negative", C, "Meta's $15bn USD and debut €9bn bonds priced ~18–39bp wide of its curve, days after S&P moved its outlook to negative.", "SemiAnalysis (Bloomberg)"),
   dp(66221, "2026-11-05", "CRWV", "negative", C, "CoreWeave 2031 unsecured bonds traded as low as 79.5 after TX, GA and OH elected governors who campaigned on slowing construction.", "Bloomberg; WSJ; Evercore ISI"),
   dp(66417, "2026-11-07", "CRWV", "negative", C, "Lenders committed $48.4bn to GPU-backed loans in 2026 vs $6.6bn in 2025; now ~47% of AI-infra debt; collateral and repayment both hinge on GPU rental rates.", "American Compute data"),
   dp(66359, "2026-11-06", "9984 JP", "negative", C, "SoftBank 5-yr CDS ~466bp; debt +$40.4bn over 12 months.", "@DeItaone"),
   dp(67049, "2026-11-10", "9984 JP", "positive", S, "SoftBank raised a record $56.5bn in 2Q FY3/27 and repaid the $40bn bridge ~6 months early.", "SoftBank 2Q FY3/27 results"),
   dp(66594, "2026-11-06", "WULF", "positive", S, "Google IG credit support for project financing of a ~$19bn AI lab lease at TeraWulf.", "TeraWulf 3Q26"),
   dp(66298, "2026-11-06", "AMD", "negative", M, "AMD disclosed $7.7bn of data-center lease guarantees and $750m of partner debt guarantees; the TensorWave/Fermi lease missed its 31-Oct closing.", "SemiAnalysis"),
   dp(66291, "2026-11-06", "SPCX", "mixed", M, "Goldman and Apollo selling the $40bn SpaceX GPU SPV lease ($8.3bn senior loan plus bonds; with $7bn prepayment funds ~$47.3bn of GPUs).", "SemiAnalysis (Bloomberg)"),
   dp(66364, "2026-11-05", "IREN", "negative", C, "IREN: $15bn of FY27 capex remaining, $6bn still to be financed.", "IREN Q1 FY27 results"),
   dp(65684, "2026-10-28", "GOOGL", "negative", C, "Alphabet issued $12.4bn of ATM equity and $28.7bn of notes in 3Q as FCF was −$9.1bn.", "Alphabet 3Q26 10-Q"),
  ],
  staged=[]),

 dict(key="politics_gw", title="Political environment and GW deployed", status="new",
  claim="New tenet (Bobby, 2026-11-10). The Street models a 2028 GW ramp. Post-midterm permitting is pushing some of it into 2029, which would leave 2028 net adds flat and hit every bottleneck supplier priced for a 2028 ramp.",
  srs_view="The Street is assuming for '28, but some has clearly been pushed out. Morgan Stanley has 5GW pushed into 2029, making 2028 net adds flat. This could be a problem for all bottleneck companies.",
  checks=[
   dict(claim="Morgan Stanley has 5GW pushed into 2029, making 2028 net adds flat", verdict="confirmed", text="Morgan Stanley (2026-11-08/09) moved ~5GW of US data-center IT load from 2028 into 2029, about 20% of the 2028 slate. It now models 19.9GW of 2028 additions vs 27.6GW in 2029, which leaves 2028 flat vs 2027 (about −4% y/y). MS calls these postponements, not cancellations, with 2027 unchanged.", sources=[["SB #67062 (MS US Thematic Research)", ""], ["BigGo Finance on the MS note, 2026-11-08", "https://finance.biggo.com/news/7b7c2bee-7f97-4b76-aed2-f75ed42127ec"]]),
   dict(claim="This could be a problem for all bottleneck companies", verdict="supported", text="MS itself flags a possible temporary 2028 slowdown, with upstream suppliers facing slower orders, rising inventories and margin pressure. Offsets: Bernstein sees only a 2–4% realistic US capacity hit; SemiAnalysis says ~75% of 2027 capacity in the top 20 states is already under construction.", sources=[["BigGo Finance on the MS note", "https://finance.biggo.com/news/7b7c2bee-7f97-4b76-aed2-f75ed42127ec"], ["SB #66332, #65561", ""]]),
  ],
  dps=[
   dp(67062, "2026-11-09", "NVDA", "negative", S, "MS est.: ~5GW of US data-center capacity shifted from 2028 to 2029; 19.9GW incremental in 2028 vs 27.6GW in 2029, so 2028 additions are flat vs 2027 and down y/y.", "MS US Thematic Research"),
   dp(66331, "2026-11-06", "NVDA", "negative", S, "MS est. (McVeigh): ~12GW of the US pipeline at risk through 2030 from tighter TX/OH legislation (4.9GW 2028, 3.8GW 2029, 3.7GW 2030); no impact on 2027 capacity under construction.", "Morgan Stanley Research"),
   dp(66102, "2026-11-04", "VRT", "negative", S, "SemiAnalysis: 13 election states hold 43.5GW (70%) of 62.2GW of 2028 US net adds (Texas ~18GW); a 2028 delivery needs its power permit 12–15 months earlier.", "SemiAnalysis Datacenter Industry Model"),
   dp(67096, "2026-11-04", "CAT US", "negative", S, "Texas DC permits halted since the 9/21 TCEQ directive pending the ERCOT audit, incl. behind-the-meter generation; governor-elect pledges a hold until the legislature acts (session 1/12–5/31/27).", "Wells Fargo Securities"),
   dp(66101, "2026-11-04", "VST", "negative", S, "Texas pause could run 6–9 months into 2027 under Hinojosa vs Dec-26 under Abbott: ERCOT audit due 12/10, PUCT review 12/17.", "SemiAnalysis / WFS"),
   dp(66252, "2026-11-04", "NVDA", "negative", S, "SemiAnalysis est.: 5.8GW of US capacity could be delayed assuming a ~2Q permitting pause; only ~600MW is TPU, so the delay falls mostly on Nvidia GPU capacity.", "SemiAnalysis"),
   dp(66219, "2026-11-05", "META", "negative", S, "Meta president: new US data-center projects will be 'very challenging' after the midterms; considering building outside the US.", "WSJ Tech Conference"),
   dp(66265, "2026-11-04", "CRWV", "negative", S, "Gerstner (forecast, widely repeated): 10–15GW of the ~43GW of US capacity expected online in 2027 may not come online.", "Brad Gerstner, All-In"),
   dp(66332, "2026-11-06", "NVDA", "mixed", C, "Bernstein est.: midterms raise execution/cost risk, not cancellation risk; realistic US capacity hit 2–4% vs 9% worst case.", "Bernstein"),
   dp(65561, "2026-11-02", "VRT", "positive", C, "SemiAnalysis: ~75% of the 33.8GW due in 2027 across the top 20 states is already under construction; global +50GW year intact.", "SemiAnalysis DC model"),
   dp(66220, "2026-11-04", "CRWV", "positive", C, "CoreWeave CEO: no anticipated impact on existing commitments or backlog from the midterms.", "CoreWeave CEO"),
  ], staged=[]),

 dict(key="nvda", title="Nvidia: demand quality, export exposure and governance", status="watch",
  claim="Nvidia's demand is end-demand from labs and hyperscalers, not diverted or financed demand, and management is credible.",
  srs_view="Concern: a large share of revenue billed through Singapore/Malaysia, and the Huang/Megaspeed fact pattern (crisis PR engagement, questions over how much Megaspeed received) raises credibility and export-control risk that could lead to Nvidia order cuts. See fact checks; the board-misstatement point is not supported by reporting so far.",
  checks=[
   dict(claim="25% of Nvidia revenue went to Singapore and Malaysia", verdict="unverified", text="Not verifiable from current filings. Since FY27 Nvidia reports revenue by customer headquarters: Q2 FY27 US $60.1bn, Taiwan $27.0bn, China incl. HK $7.9bn, Other $1.3bn of $96.2bn, with no Singapore or Malaysia line. Under the old billing-location basis Singapore was ~18–28% (about 28% in CY24). But Nvidia said most Singapore-billed shipments went elsewhere, and Singapore's government said <1% of revenue was physically delivered there. Need the source for 25%.", sources=[["Nvidia 10-Q, quarter ended 2026-07-26", "https://www.sec.gov/Archives/edgar/data/0001045810/000104581026000075/nvda-20260726.htm"], ["Tom's Hardware (Bloomberg), 2025-02-18", "https://www.tomshardware.com/tech-industry/deepseek-gpu-smuggling-probe-shows-nvidias-singapore-gpu-sales-are-28-percent-of-its-revenue-but-only-1-percent-are-delivered-to-the-country-report"]]),
   dict(claim="Jensen Huang hired a crisis PR firm a year ago", verdict="reported", text="Wired (via TechCrunch, 2026-11-09): Heller Inc. was engaged around Oct-2025, after the NYT report; Nvidia's comms team was told to copy Heller on press inquiries about Huang. Nvidia had not commented.", sources=[["TechCrunch, 2026-11-09", "https://techcrunch.com/2026/11/09/jensen-huang-reportedly-engaged-a-pr-firm-with-a-history-of-handling-high-profile-sex-scandals-a-year-ago/"]]),
   dict(claim="He lied to the board about how much Megaspeed actually shipped", verdict="not_supported", text="No report says this. Reported so far: the board opened an independent investigation on 2026-11-08. The Business Times reports a ~50,000-unit gap between Nvidia's initial accounting to US officials of hardware supplied to Megaspeed and Bloomberg's customs data (~136k GPUs, ≥$4.6bn, 2023–Nov-25). Two of eight data-center operators Nvidia said it visited reportedly did not host Megaspeed hardware. The Information reports ≥$7.5bn / ~240k GPUs moved into China through a linked network, which Reuters could not verify. Fortune says the probe 'could look at' questionable public statements. The reported gap concerns statements to US officials, not the board.", sources=[["Fortune, 2026-11-09", "https://fortune.com/2026/11/09/nvidia-board-probe-jensen-huang-affair-suspected-china-spy-statements/"], ["Tech Times UK, 2026-11-10", "https://www.techtimes.co.uk/megaspeed-nvidia-hardware-imports-chip-scrutiny-1809823"], ["SB #67185 (The Information)", ""]]),
   dict(claim="Nvidia orders could be cut", verdict="inference", text="An SRS inference, not a datapoint. The nearest reported item runs the other way: Nvidia itself is reportedly cutting neocloud Vera Rubin allocations by up to 50% and reallocating to SpaceX (SB #65967).", sources=[]),
  ],
  dps=[
   dp(67185, "2026-11-10", "NVDA", "negative", C, "The Information (two people): a network tied to Alice Huang (Shanghai Century Litong, Megaspeed) moved ≥$7.5bn / ~240k H100/H200 GPUs into China. Unverified; Reuters could not confirm.", "The Information"),
   dp(66297, "2026-11-06", "NVDA", "negative", C, "Nvidia told cloud partners at least 51% of services on new contracts must go to non-Chinese customers; APAC banks avoiding GPU project finance with Chinese offtakers while the RASA bill is pending.", "SemiAnalysis"),
  ],
  staged=[dict(t="NVDA", date="2026-11-08", impact="negative", field_key="risk", source_type="news", confidence="medium",
     text="Nvidia's board opened an independent investigation (2026-11-08) after Huang disclosed an affair with a former Megaspeed executive reportedly targeted by a foreign intelligence effort. The Business Times reports a ~50k-unit gap between Nvidia's initial accounting to US officials of hardware supplied to Megaspeed and Bloomberg's customs-based ~136k GPUs (≥$4.6B, 2023–Nov 2025). Nvidia says it found the hardware in other warehouses; the board says it has no reason to believe national security or company secrets were compromised.",
     primary="Nvidia board statement; The Business Times; Bloomberg customs analysis", secondary="Tech Times UK, 2026-11-10; Fortune, 2026-11-09",
     why="Board probe plus a quantified shipment discrepancy; exposure (export-control penalties, customer actions) not yet established. Borderline under the filter.")]),

 dict(key="china_models", title="Chinese and open-weight models stay behind", status="watch",
  claim="Enterprises will not trust Chinese models, and the frontier gap holds.",
  srs_view="", checks=[], dps=[], staged=[],
  note="Datapoints for this tenet are on the AI thesis Signposts and Risks sections; nothing new this week."),
]

# ---------- page db doc ----------
doc = dict(thesis="ai", updated_at=TODAY + "T16:30:00Z", built_by="tenet build 2026-11-10",
           storage="Datapoints: Supabase research_evidence (one row per datapoint, via the Datapoint Filter). Tenets: Supabase thesis_tenets. Links: thesis_tenet_evidence (tenet, evidence id, stance). This document mirrors them for the page.",
           tenets=[{k: v for k, v in t.items()} for t in TENETS])
for i, t in enumerate(doc["tenets"]):
    t["sort"] = i + 1
(OUT / "ai_tenets.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

# ---------- SQL ----------
def q(s):
    tag = "$tq$"
    assert tag not in (s or "")
    return "null" if s is None or s == "" else f"{tag}{s}{tag}"
rows = []
for i, t in enumerate(TENETS):
    rows.append(f"('ai',{q(t['key'])},{i+1},{q(t['title'])},{q(t['claim'])},{q(t['status'])},{q(t['srs_view'])},{('date ' + repr(TODAY)) if t['srs_view'] else 'null'},{q(json.dumps(t['checks'], ensure_ascii=False))}::jsonb,now())")
sql1 = ("insert into public.thesis_tenets (thesis_key,tenet_key,sort,title,claim,status,srs_view,srs_view_date,fact_checks,updated_at) values\n" + ",\n".join(rows) +
        "\non conflict (thesis_key,tenet_key) do update set sort=excluded.sort,title=excluded.title,claim=excluded.claim,status=excluded.status,srs_view=excluded.srs_view,srs_view_date=excluded.srs_view_date,fact_checks=excluded.fact_checks,updated_at=now();")
links = [f"('ai',{q(t['key'])},{d['id']},{q(d['stance'])})" for t in TENETS for d in t["dps"]]
sql2 = ("insert into public.thesis_tenet_evidence (thesis_key,tenet_key,evidence_id,stance) values\n" + ",\n".join(links) +
        "\non conflict (thesis_key,tenet_key,evidence_id) do update set stance=excluded.stance returning id;")
(OUT / "tenets.sql").write_text(sql1)
(OUT / "links.sql").write_text(sql2)
print(len(TENETS), "tenets;", len(links), "links;", sum(len(t['staged']) for t in TENETS), "staged")
