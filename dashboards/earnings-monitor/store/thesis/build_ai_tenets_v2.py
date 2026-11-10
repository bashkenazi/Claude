#!/usr/bin/env python3
"""v2 of the AI thesis tenet data (Bobby, 2026-11-10): a score per datapoint relative to the AI bull thesis
(+2 strongly supports, +1 supports, 0 neutral, -1 weakens, -2 strongly weakens), more datapoints from Supabase,
the political tenet renamed 'getting more difficult' and moved first with a GW-deployed table, and the two
staged rows loaded (#67190, #67191). Reads v1 ai_tenets.json, writes ai_tenets.json + links_v2.sql + tenets_v2.sql."""
import json, pathlib
OUT = pathlib.Path(__file__).parent
doc = json.load(open(OUT / "ai_tenets.json"))
T = {t["key"]: t for t in doc["tenets"]}

# scores for existing links, relative to the bull thesis
SC = {
 "lab_arr": {67052: 0, 66353: 2, 64181: 0, 65875: 2, 65531: -1, 65838: -1, 67065: 1},
 "roi": {64181: 1, 66353: 0, 67052: -1, 65687: 1, 66850: -1},
 "compute_tight": {66397: 2, 66361: 2, 66362: 1, 65673: 1, 66250: 1, 65967: 0},
 "capex": {66113: 2, 63479: 1, 64142: 1, 64059: 1, 66216: -1, 66389: -1},
 "financing": {67053: -1, 66244: -2, 66295: -2, 66229: -1, 65566: -2, 66296: -1, 66221: -2, 66417: -1, 66359: -1, 67049: 1, 66594: 1, 66298: 0, 66291: 0, 66364: -1, 65684: -1},
 "politics_gw": {67062: -2, 66331: -1, 66102: -1, 67096: -2, 66101: -1, 66252: -1, 66219: -1, 66265: -1, 66332: 1, 65561: 1, 66220: 1},
 "nvda": {67185: -2, 66297: -1},
}
def dp(id, date, t, score, text, src):
    return dict(id=id, date=date, t=t, score=score, text=text, src=src)
ADD = {
 "lab_arr": [
  dp(67190, "2026-11-06", "OpenAI", -1, "OpenAI received ~$11bn as the first part of a round at a $1.25tn pre-money valuation (CFO Friar), vs ~$1.4tn and $30bn+ first sought; may total up to ~$20bn; SoftBank and MGX participated.", "OpenAI CFO Sarah Friar; 24/7 Wall St."),
  dp(66108, "2026-11-03", "GOOGL", 1, "OpenAI: ChatGPT search volume ~1/5 of Google's; ChatGPT at 1.2bn WAUs, +200m in two months.", "OpenAI internal data (Big Technology)"),
  dp(62414, "2026-10-28", "OpenAI", 1, "All ServiceNow employees slated for ChatGPT Work and Codex; OpenAI models picked for more ServiceNow app-dev and security workflows.", "OpenAI / ServiceNow"),
  dp(65692, "2026-11-02", "ANTH", 1, "Anthropic compute/infra expense 57% of revenue in 9M26 vs 172% in 9M25: revenue +1,206% y/y vs compute +329%.", "Anthropic amended S-1"),
  dp(66266, "2026-11-02", "ANTH", -1, "Anthropic 3Q compute & infrastructure $9.86bn = 58% of revenue vs 48% in 2Q, incl. $5.0bn of short-term commitments that cost significantly more.", "Anthropic S-1/A"),
  dp(66267, "2026-11-02", "ANTH", -1, "Anthropic estimates 5–7% of 9M26 revenue came from customers violating usage policies or commercial terms.", "Anthropic S-1/A"),
  dp(65893, "2026-11-03", "ANTH", -1, "Investors urging a $1.5–1.6tn Anthropic IPO valuation vs earlier hopes near $2tn: a ~20–25% reset in expected IPO value.", "New York Times"),
 ],
 "roi": [
  dp(65691, "2026-11-02", "ANTH", -1, "Anthropic $895.4bn of purchase/lease commitments, substantially all compute: $69.8bn due in the next 12 months, $447.5bn before end-2030.", "Anthropic amended S-1"),
  dp(66887, "2026-11-02", "MSFT", -1, "Microsoft future lease commitments $364bn (>$133bn added in 4Q26), 54% of $677bn commercial RPO.", "Microsoft 1Q27 results"),
  dp(65541, "2026-10-30", "META", -1, "S&P: Meta capex $140bn (2026), >$225bn (2027), $252bn (2028) with free operating cash flow deficits of $22bn/$71bn/$39bn; outlook cut to negative.", "S&P Global Ratings"),
  dp(66691, "2026-11-09", "ORCL", -1, "DB est.: OpenAI still 40%+ of Oracle's backlog.", "Deutsche Bank"),
 ],
 "compute_tight": [
  dp(66394, "2026-11-05", "CRWV", 2, "Very short-term GPU contracts reportedly pricing at ~4x CoreWeave's existing contract base; near-term capacity sold out.", "BofA HY credit (Ana Goshko)"),
  dp(66724, "2026-11-09", "NVDA", 1, "GPU rental prices rose ~6% m/m in October; A100, H100 and H200 all up.", "RBC Capital Markets"),
  dp(66363, "2026-11-05", "IREN", 1, "IREN backlog $20.3bn (+22% q/q), ~2/3 with investment-grade counterparties.", "IREN Q1 FY27 results"),
  dp(65836, "2026-11-02", "NVDA", 1, "4–5k Vera Rubin racks (~1GW) ordered across SpaceX, xAI and Tesla, up to 11–12k racks (~2.8GW) on demand.", "SemiAnalysis Accelerator Model"),
  dp(66218, "2026-11-05", "MSFT", -1, "Microsoft declined an option worth tens of billions to more than double its Texas business with Nscale (~500MW).", "Financial Times"),
  dp(66386, "2026-11-06", "ORCL", -1, "Microsoft declined to renew its 2023 OCI AI-capacity rental (older Nvidia GPUs) and has been turning it off.", "Bloomberg (via Reuters)"),
 ],
 "capex": [
  dp(65891, "2026-10-30", "AMZN", 0, "Amazon 10-Q: secured supplier-financing facility of up to ~$80bn for infrastructure, drawable 1Q27–3Q28.", "Amazon 10-Q"),
  dp(65793, "2026-11-02", "META", 0, "Meta seeking ≥$20bn of bonds a week after announcing stock sales to fund capex; FCF −$2.1bn last quarter.", "Press reports"),
 ],
 "financing": [
  dp(67187, "2026-11-10", "ANTH", 2, "Anthropic S-1/A2: $26.0bn concurrent placement at the IPO price from suppliers: NVDA $10bn, GOOGL $10bn, AMD $2.5bn, AVGO/MU/MSFT $1bn each, TSMC $0.5bn.", "Anthropic S-1/A2"),
  dp(66300, "2026-11-06", "ANTH", 1, "Anthropic amended S-1: $15bn secured revolver and $77bn of undrawn note-purchase lines from Google, Amazon and Broadcom.", "Anthropic amended S-1"),
  dp(65719, "2026-11-02", "ORCL", 1, "Oracle priced $20bn: $10bn of stock at $116 plus $10bn of notes at 7.000–8.650% (2029–2046).", "Oracle pricing release"),
  dp(66239, "2026-11-04", "WULF", 1, "Google credit support backstops Anthropic on $19bn of leases at TeraWulf's Justified (KY) campus.", "TeraWulf 8-K"),
  dp(67051, "2026-11-10", "9984 JP", 1, "Nvidia committed $3.0bn to SB Energy and gave credit support for 4.25GW at PORTS-Pike (Ohio), leased to OpenAI for 20 years.", "SoftBank 2Q FY3/27 results"),
  dp(66472, "2026-11-09", "CRWV", -2, "Some CoreWeave 2031 bonds yield >16%; 5-yr CDS >1,240bp, up ~50% in a month.", "CNBC"),
  dp(65568, "2026-11-02", "NBIS", -2, "WSJ: neocloud high-yield issuance has effectively stalled; Nebius dropped a HY bond and is using customer prepayments.", "WSJ"),
  dp(65850, "2026-11-02", "APLD US", -1, "Goldman paused premarketing of a $3.5bn HY bond for Applied Digital's Delta Forge 1; DC capital markets 'gummed up' without offtake.", "SemiAnalysis"),
  dp(65848, "2026-11-02", "NBIS", -1, "Nebius took a $3.5bn 364-day secured bridge from Citi at S+275, stepping up to S+350, secured on substantially all assets.", "SemiAnalysis"),
  dp(65801, "2026-10-30", "INDUSTRY_DATACENTER", -1, "Banks shelved the bond takeout of a $15bn bridge for the Google-backed Nexus (Anthropic) campus in Hubbard, TX, amid the Texas permit freeze.", "SemiAnalysis"),
  dp(65845, "2026-11-02", "ANTH", -1, "Unwrapped $18bn North Star TPU second lien (Anthropic credit) priced ~10% (~12% at 95 OID).", "SemiAnalysis"),
  dp(65422, "2026-10-31", "ANTH", -1, "Developers say they cannot currently finance projects directly on Anthropic credit; direct contracting post-IPO hinges on IG ratings.", "SemiAnalysis interviews"),
  dp(65868, "2026-11-03", "ORCL", -1, "MS credit: Oracle's ~$5bn/$4.75bn/$6.25bn FY27–29 refinancing and possible tens of $bn of vendor financing sit outside the '$20bn and done' framing.", "Morgan Stanley credit"),
 ],
 "politics_gw": [
  dp(66099, "2026-11-04", "NVDA", -2, "Democratic wins in TX/GA/OH/PA put ~50% of proposed US AI DC additions at risk of pushback (Bloomberg); MS: 24GW of Texas builds at risk through 2030 (~20% of US GW).", "Bloomberg; Morgan Stanley"),
  dp(66615, "2026-11-06", "VST", -1, "Texas governor-elect ran on a moratorium on new data centers until guardrails are set; ERCOT Batch Zero report 12/10, PUCT 12/17.", "Wolfe Research"),
  dp(65921, "2026-11-03", "TLN", -1, "Talen: \"'29 is becoming the new '28\" for data-center site development (~1-year slip); new CCGT all-in cost >$120/MWh and rising.", "Talen Energy management"),
  dp(66334, "2026-11-06", "ORCL", -1, "TrendForce cuts 2027 capacity at Vantage's Lighthouse campus (Oracle/OpenAI, WI) to 310MW from 650MW on power approval; 2028 kept at 1.3GW.", "TrendForce"),
  dp(66438, "2026-11-09", "ORCL", -1, "SemiAnalysis: Lighthouse (~900MW IT) first AI ops slip to 3Q28, ~3–4 quarters behind Oracle's 2H27 guide.", "SemiAnalysis"),
  dp(66251, "2026-11-04", "OpenAI", -1, "SemiAnalysis: Vantage Stargate Texas may have 700MW delayed from 4Q27; SB Energy Ohio phase 2 (800MW, 3Q28) at risk depending on pause length.", "SemiAnalysis"),
  dp(66249, "2026-11-04", "MSFT", -1, "SemiAnalysis: Crusoe Stargate Abilene Buildings 9/10 (672MW, Microsoft) likely delayed from 3Q27; onsite-generation permit pending under the TCEQ pause.", "SemiAnalysis"),
  dp(66246, "2026-11-04", "GOOGL", -1, "SemiAnalysis: Nexus Hubbard (800MW TPU for Anthropic) permitted for only ~470MW IT; Goodnight may see ~275MW delayed from 4Q27.", "SemiAnalysis"),
  dp(66377, "2026-11-06", "VST", 0, "Vistra: Texas permit hold could lift ~mid-December when audits finish; PUCT drafting a stricter large-load tariff; a moratorium needs legislation and is 'a bridge too far'.", "Vistra 3Q26 call"),
  dp(66100, "2026-11-04", "AMZN", 0, "BofA: moratoria and the end of tax breaks raise build cost and permitting risk, but incumbent permitted capacity (e.g. AMZN) gains scarcity value.", "BofA research"),
  dp(66103, "2026-11-03", "SPCX", 1, "SemiAnalysis: SpaceX can deploy ~13GW of DC capacity in 2027 vs a 10GW plan (3.6GW under construction).", "SemiAnalysis"),
 ],
 "nvda": [
  dp(67191, "2026-11-08", "NVDA", -2, "Nvidia's board opened an independent investigation after Huang disclosed an affair with a former Megaspeed executive; ~50k-unit gap between Nvidia's initial accounting to US officials and Bloomberg customs data (~136k GPUs, ≥$4.6bn).", "Nvidia board statement; Business Times; Bloomberg"),
  dp(66104, "2026-11-04", "ORCL", -1, "Oracle reportedly scrapped a ~$7bn five-year deal to lease ~100k AI chips to Tencent under US administration pressure.", "Financial Times"),
  dp(65425, "2026-10-31", "NVDA", -1, "MI355X reportedly delivers up to 2x B200 performance per dollar on Kimi K3 agentic inference (memory per server).", "SemiAnalysis InferenceX"),
  dp(65690, "2026-11-02", "NVDA", 0, "RMB16m for an eight-GPU Blackwell server in China, prices reportedly tripled in four months (secondary-market scarcity, not Nvidia ASP).", "@jukan05 (unsourced)"),
 ],
 "china_models": [
  dp(64067, "2026-10-29", "MOONSHOT", 2, "Kimi K3.1 Pro ~5% pass@5 vs ~70% Opus 5.5 and ~60% GPT-6 Astra on Real World Engineering Bench.", "Xplore AI benchmark"),
  dp(64293, "2026-10-29", "MOONSHOT", 1, "Kimi K3.1 Pro 37% on HLE-Diamond vs 69% Gemini 4 Carbon and 68% Opus 5.5.", "Artificial Analysis"),
  dp(65515, "2026-11-02", "2513 HK", 1, "GLM 5.3 2.7% GDPx vs DeepSeek 4.1 Flash 5.4% and Opus 5.5 12.0%.", "SemiAnalysis GDPx"),
  dp(64298, "2026-10-29", "MOONSHOT", -1, "Kimi K3.1 Pro 341 on the AA Progress Index vs frontier leader Gemini 4 Carbon 352: roughly two months behind.", "Artificial Analysis"),
  dp(64297, "2026-10-29", "DEEPSEEK", -1, "DeepSeek V4.1 Flash 324 on the AA Progress Index, the top released-weights model, above the leading US open-weight model (307).", "Artificial Analysis"),
  dp(64096, "2026-10-29", "MSFT", -1, "Microsoft Foundry revenue from open-source models up 10x; multi-model agent customers up 5x.", "Microsoft FQ1 FY27 call"),
  dp(64109, "2026-10-29", "MOONSHOT", 0, "Kimi K3.1 Pro reportedly trained extensively on GPT-6 Astra outputs (distillation), per The Information.", "The Information"),
  dp(64340, "2026-10-31", "BABA", 0, "Qwen integrated into Apple Intelligence in China (Siri, Writing Tools, Visual Intelligence); commercial terms undisclosed.", "Apple China Newsroom"),
 ],
}
for k, t in T.items():
    for d in t["dps"]:
        d["score"] = SC.get(k, {}).get(d["id"], 0); d.pop("stance", None); d.pop("impact", None)
    have = {d["id"] for d in t["dps"]}
    t["dps"] += [d for d in ADD.get(k, []) if d["id"] not in have]
    t["staged"] = []

P = T["politics_gw"]
P["title"] = "Political environment: getting more difficult"
P["status"] = "weakening"
P["claim"] = "Post-midterm politics is getting more difficult for US data centers (TX/OH/GA/PA governors, the Texas permit freeze, stricter large-load tariffs). The Street models a 2028 GW ramp; some of it is already moving into 2029, which would leave 2028 net adds flat and hit every bottleneck supplier priced for that ramp."
P["gw"] = dict(title="GW deployed: who says what", cols=["Source", "Date", "2027", "2028", "2029", "Read"], rows=[
  ["Morgan Stanley US Thematic", "2026-11-09", "unchanged", "19.9GW incremental (~5GW moved out); flat vs 2027", "27.6GW", "Postponement, not cancellation"],
  ["Morgan Stanley (McVeigh)", "2026-11-06", "no impact", "4.9GW at risk", "3.8GW at risk", "~12GW at risk through 2030 from TX/OH rules"],
  ["SemiAnalysis DC model", "2026-11-04", "33.8GW due, ~75% under construction", "62.2GW US net adds; 43.5GW in 13 election states", "–", "30.3GW exposed in a pro-pause case vs 5.7GW otherwise"],
  ["SemiAnalysis", "2026-11-04", "5.8GW could be delayed (mostly Nvidia, mostly TX)", "–", "–", "Assumes a ~2-quarter permitting pause"],
  ["Bernstein", "2026-11-06", "–", "–", "–", "Realistic US capacity hit 2–4% vs 9% worst case"],
  ["Talen Energy mgmt", "2026-11-03", "–", "'29 is becoming the new '28", "–", "~1-year slip in site development"],
 ], note="Forecasts, not actuals. SB = Supabase research_evidence id.")
order = ["politics_gw", "lab_arr", "roi", "financing", "compute_tight", "capex", "nvda", "china_models"]
doc["tenets"] = [T[k] for k in order]
for i, t in enumerate(doc["tenets"]): t["sort"] = i + 1
T["china_models"].pop("note", None)
doc["updated_at"] = "2026-11-10T20:00:00Z"
doc["scale"] = "Dots score each datapoint against the AI bull thesis: two green = strongly supports, one green = supports, blue = neutral or mixed, one red = weakens, two red = strongly weakens."
(OUT / "ai_tenets.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))

st = lambda s: "supports" if s > 0 else "challenges" if s < 0 else "mixed"
rows = [f"('ai','{t['key']}',{d['id']},'{st(d['score'])}',{d['score']})" for t in doc["tenets"] for d in t["dps"]]
(OUT / "links_v2.sql").write_text("insert into public.thesis_tenet_evidence (thesis_key,tenet_key,evidence_id,stance,score) values " + ",".join(rows) + " on conflict (thesis_key,tenet_key,evidence_id) do update set stance=excluded.stance, score=excluded.score;")
print(sum(len(t["dps"]) for t in doc["tenets"]), "links;", [(t["key"], len(t["dps"])) for t in doc["tenets"]])
