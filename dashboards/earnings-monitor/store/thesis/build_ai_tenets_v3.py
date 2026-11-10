#!/usr/bin/env python3
"""v3 (Bobby, 2026-11-10): new tenet 'Use cases expanding' (cyber + knowledge work), placed third.
Reads live ai_tenets.json, writes ai_tenets_v3.json + links_v3.sql + tenet_v3.sql."""
import json, pathlib
OUT = pathlib.Path(__file__).parent
doc = json.load(open(OUT / "live/thesis/ai_tenets.json"))
def dp(id, date, t, score, text, src): return dict(id=id, date=date, t=t, score=score, text=text, src=src)
C, K = "Cyber: ", "Knowledge work: "
DPS = [
 # cyber
 dp(66401, "2026-11-09", "CSCO", 1, C + "Partners say enterprises are cutting network-gear useful lives to ~5 years from 6–7, citing Mythos-found vulnerabilities; one sees ~24 months of refresh.", "Cleveland Research channel checks"),
 dp(66092, "2026-11-03", "ANET", 1, C + "Arista guides campus +60% to ~$2bn in FY27, tied to AI-driven vulnerability discovery (87 EOS CVEs since 2019 vs 634–848 at two large peers).", "Arista 3Q26 call"),
 dp(64211, "2026-10-30", "ANET", 1, C + "A large bank pulled forward a 9-figure Arista switch refresh from 2H27 to address Mythos security concerns.", "Cleveland Research channel checks"),
 dp(64331, "2026-10-23", "MOONSHOT", -1, C + "Kimi K3.1 scores 64% on the AA Cyber Index at $2.81/task, near restricted GPT-6 Sol (69%): cyber capability reaching cheap open models.", "Artificial Analysis"),
 dp(64301, "2026-10-29", "2513 HK", 0, C + "Epoch: GLM-5.3 compromised 6 recent Firefox releases at ~$1,000 API cost each after >$100k setup; no provider refusals.", "Epoch AI"),
 dp(62411, "2026-10-28", "GOOGL", 1, C + "Gemini 4 Carbon launches first to selected cyber defenders (AA Index 59), at $2/$10 per m tokens intro pricing.", "Google DeepMind"),
 dp(65756, "2026-10-21", "FTNT", 1, C + "A global partner has 9 figures of Mythos-related business YTD plus a 9-figure pipeline, mostly firewall refresh of end-of-support gear.", "Cleveland Research channel checks"),
 dp(63198, "2026-10-16", "PANW", 1, C + "CIOs suggest 2027 security budgets could grow near double digits vs low-to-mid single digits; AI budgets carve out 3–5% for security.", "Deutsche Bank"),
 dp(63181, "2026-10-16", "RBRK", -1, C + "Rubrik sees no meaningful pipeline inflection since cyber-capable models launched, unlike CrowdStrike.", "Deutsche Bank"),
 dp(60554, "2026-10-06", "ANTH", 1, C + "Anthropic adds three Cyber Verification tiers (Defense, Red Team, Specialized), widening vetted access to Opus 5.5, Sonnet 5.5 and Mythos 5.1.", "Anthropic"),
 dp(56965, "2026-09-23", "ZS", -1, C + "Zscaler AI security has limited traction and is sometimes given away at renewal; little partner awareness of Agentic SOC.", "Cleveland Research partner checks"),
 dp(54756, "2026-09-17", "CSCO", 1, C + "Cisco partners tracking low-double-digit to 20%+ bookings growth; Mythos-driven refresh urgency is the highest they have seen.", "Cleveland Research channel checks"),
 dp(54411, "2026-09-16", "INDUSTRY_SOFTWARE", 2, C + "GSIs report $200–300m of Mythos-related business closed (patching, remediation); one GSI's Mythos pipeline reached $1bn.", "Cleveland Research IT services checks"),
 dp(53746, "2026-09-15", "INDUSTRY_AI_CAPEX", 1, C + "Barclays: lab monitoring of advanced cyber models adds ~18% to industry compute from CY27; inference cost +20% for GPT-5.6 Sol-class cyber models.", "Barclays"),
 dp(49025, "2026-08-26", "CRWD", 2, C + "CrowdStrike calls it a 'Mythos moment': AIDR ending ARR nearly tripled q/q; Kurtz says AIDR could be bigger than EDR.", "CrowdStrike Q2 FY27 call"),
 dp(43059, "2026-08-13", "PANW", 2, C + "Partners cite $200m+ of Mythos business closed against an $800m+ pipeline (4x); boards unlocking incremental security budget.", "Cleveland Research channel checks"),
 # knowledge work
 dp(65509, "2026-11-02", "ANTH", 1, K + "Opus 5.5 tops SemiAnalysis GDPx at 12.0% across 11 professional domains (Gemini 4 Carbon 10.9%, GPT-6 Astra 9.6%): capability, not revenue.", "SemiAnalysis GDPx"),
 dp(62414, "2026-10-28", "OpenAI", 1, K + "All ServiceNow employees slated for ChatGPT Work and Codex, beyond engineering.", "OpenAI / ServiceNow"),
 dp(64360, "2026-10-28", "MSFT", -1, K + "Hood: M365 Copilot consumption monetization 'will be a slower move' than GitHub's usage-billing shift.", "Microsoft FQ1 FY27 call"),
 dp(63735, "2026-10-26", "MSFT", 1, K + "Microsoft has >30m paid M365 Copilot seats.", "Morgan Stanley"),
 dp(63602, "2026-10-22", "MSFT", 1, K + "Copilot added ~5m and ~10m seats in the past two quarters; 57% of VARs see seat expansion at renewal.", "KeyBanc VAR survey"),
 dp(63030, "2026-10-14", "BOX", 0, K + "Typical Box AI deployments reach only ~15% of knowledge workers; NRR 106% on higher user penetration.", "BofA"),
 dp(62795, "2026-10-07", "MSFT", 1, K + "88% of CIOs expect to use M365 Copilot in the next 12 months vs 72% a year ago.", "Morgan Stanley CIO survey"),
 dp(62696, "2026-10-06", "MSFT", 0, K + "Almost half of Copilot power users already prompt Cowork, but default usage billing slipped to December on governance and cost-control concerns.", "J.P. Morgan partner call"),
 dp(64793, "2026-09-28", "REL LN", 1, K + "Law firms fund Harvey/Legora in 2026 budgets by cutting overlapping legacy modules.", "Third Bridge expert call"),
 dp(54760, "2026-09-17", "MSFT", -1, K + "MSFT Cowork can run 30–40% cheaper than Claude via model routing; an SI cut an $80m lab bill by moving off Opus to open-weight models.", "Cleveland Research"),
 dp(54759, "2026-09-17", "MSFT", 1, K + "Copilot/Cowork usage inflecting: customers burning through monthly Cowork credits; M365 ACV expansion ~15%.", "Cleveland Research"),
 dp(54412, "2026-09-16", "ANTH", 2, K + "Anthropic enterprise spend accelerating through 3Q: deal sizes up 5x on renewal, customers raising commits 3–5 months in.", "Cleveland Research SI checks"),
 dp(59860, "2026-09-15", "SNOW", 1, K + "Snowflake: >5,000 accounts on CoWork and ~9,100 on Cortex Code; AI adopters consume ~11% more.", "Snowflake (Piper Sandler conf.)"),
 dp(59603, "2026-09-10", "CRM", 1, K + "Slackbot, an Anthropic-based knowledge-worker agent, is bundled in Slack's top tier with Salesforce absorbing the token cost.", "Salesforce (GS conf.)"),
 dp(48993, "2026-08-26", "CRM", 0, K + "Only 5% of sales/service knowledge workers have upgraded to AI editions; agentic customers reach ~2x AOV.", "Salesforce Q2 FY27 call"),
]
T = dict(key="use_cases", title="Use cases expanding", status="strengthening",
  claim="Demand broadens beyond coding. Cyber (Mythos-class vulnerability discovery driving security budgets and a network-gear refresh) and knowledge work (Copilot/Cowork, ChatGPT Work, Claude in enterprise apps) add new token demand. The October deck's bear case was that knowledge work ramps slowly and cyber is not a needle-mover.",
  srs_view=None, checks=[], dps=DPS, staged=[])
doc["tenets"] = [t for t in doc["tenets"] if t["key"] != "use_cases"]
i = next(k for k, t in enumerate(doc["tenets"]) if t["key"] == "lab_arr") + 1
doc["tenets"].insert(i, T)
for n, t in enumerate(doc["tenets"]): t["sort"] = n + 1
doc["updated_at"] = "2026-11-10T21:00:00Z"
(OUT / "ai_tenets_v3.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1))
st = lambda s: "supports" if s > 0 else "challenges" if s < 0 else "mixed"
(OUT / "links_v3.sql").write_text("insert into public.thesis_tenet_evidence (thesis_key,tenet_key,evidence_id,stance,score) values " + ",".join(f"('ai','use_cases',{d['id']},'{st(d['score'])}',{d['score']})" for d in DPS) + " on conflict (thesis_key,tenet_key,evidence_id) do update set stance=excluded.stance, score=excluded.score;")
q = lambda s: "'" + s.replace("'", "''") + "'"
(OUT / "tenet_v3.sql").write_text(
  f"insert into public.thesis_tenets (thesis_key,tenet_key,sort,title,claim,status) values ('ai','use_cases',{T['sort']},{q(T['title'])},{q(T['claim'])},'strengthening') on conflict (thesis_key,tenet_key) do update set sort=excluded.sort,title=excluded.title,claim=excluded.claim,status=excluded.status;\n"
  + "".join(f"update public.thesis_tenets set sort={t['sort']} where thesis_key='ai' and tenet_key='{t['key']}';\n" for t in doc["tenets"]))
print([(t['key'], t['sort'], len(t['dps'])) for t in doc['tenets']])
ids = [d['id'] for d in DPS]; print(len(ids), len(set(ids)))
