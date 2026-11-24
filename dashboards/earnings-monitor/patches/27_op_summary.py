"""AI one page: section 0 summary table at the top (GW, chip GW, AI capex total/outside Big 4, AI revenue, ROI,
CFO of all capex spenders, financing needed). Marker "op-summary v1". Requires op-layout v1 (section toggles)."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-summary v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old)); s = s.replace(old, new)
rep("[['gw','1 GW'],", "[['sum','0 Summary'],['gw','1 GW'],")
rep("\n// 1. GW\nh += sec('gw',", r"""
/* op-summary v1 */
{
  const NC = d.neo_cfo || {}, ncK = ['CRWV', 'NBIS', 'IREN', 'APLD', 'CIFR', 'WULF', 'GLXY'];
  const strict = arrs => Y.map((_, i) => arrs.some(a => nv(a && a[i]) == null) ? null : arrs.reduce((t, a) => t + a[i], 0));
  const cfoHs = strict(cos.map(c => FU.cfo[c])), cfoNeo = add(...ncK.map(k => NC[k])), cfoSpx = NC.SPCX || Z();
  const cfoAll = Y.map((_, i) => nv(cfoHs[i]) == null ? null : cfoHs[i] + (nv(cfoNeo[i]) || 0) + (nv(cfoSpx[i]) || 0));
  const spxNon = (() => { const o = I.nonai_SPCX; const p = (o == null || o === '' || isNaN(o) ? 0 : +o) / 100; return (SC.SPCX || Z()).map(v => nv(v) == null ? null : v * p); })();
  const nonAI = Y.map((_, i) => { const hs = strict(cos.map(c => SC[c]))[i]; return nv(hs) == null ? null : hs * (1 - aiSh) + (nv(spxNon[i]) || 0); });
  const capAll = Y.map((_, i) => nv(S.capex_total[i]) == null || nv(nonAI[i]) == null ? null : S.capex_total[i] + nonAI[i]);
  const finNeed = Y.map((_, i) => nv(capAll[i]) == null || nv(cfoAll[i]) == null ? null : capAll[i] - cfoAll[i]);
  h += sec('sum', '0 · Summary', 'SRS models, FactSet consensus (24 Nov 2026); detail in the sections below', tbl('Summary', [
    { sep: 'Build' },
    { l: 'GW deployed, CITL (SRS)', v: S.gw_total, f: 'gw', ind: 1, note: 'Section 1' },
    { l: 'Chip GW sold (SRS accelerator model, chip power)', v: d.accel_tot && d.accel_tot.gw, f: 'gw', ind: 1, note: 'Section 2; before the GW-deployed haircut' },
    { sep: 'Spend' },
    { l: 'AI capex, total (SRS)', v: S.capex_total, b: 1, note: 'Section 3' },
    { l: 'AI capex outside the Big 4', v: outside, ind: 1, note: 'Oracle, neoclouds, SpaceX, labs, sovereigns, China, enterprise (section 9)' },
    { sep: 'Return' },
    { l: 'AI revenue reaching infrastructure', v: aiRev, b: 1, note: 'Section 8' },
    { l: 'ROI: revenue ÷ cumulative AI capex since 2023', v: roiCum, f: 'pct', ind: 1, note: 'Rentable capex base (section 8)' },
    { l: 'ROI, 1-year lagged: Δ revenue ÷ prior-year capex', v: roiLag, f: 'pct', ind: 1 },
    { sep: 'Funding' },
    { l: 'Cash flow from operations, all capex spenders', v: cfoAll, b: 1, note: 'Big 4 + Oracle, neoclouds and miners (CRWV, NBIS, IREN, APLD, CIFR, WULF, GLXY), SpaceX; FactSet' },
    { l: 'Big 4 + Oracle', v: cfoHs, ind: 1 }, { l: 'Neoclouds and miners', v: cfoNeo, ind: 1, note: 'CoreWeave and Nebius include customer prepayments' }, { l: 'SpaceX (whole company)', v: cfoSpx, ind: 1 },
    { l: 'Capex to fund: SRS AI capex + non-AI capex of Big 4, Oracle and SpaceX', v: capAll, ind: 1, note: `Non-AI = Street capex × ${100 - Math.round(aiSh * 100)}% for hyperscalers; SpaceX non-AI input` },
    { l: 'Total financing needed: capex less cash flow from operations', v: finNeed, b: 1, note: 'Before dividends and buybacks. AI capex by spenders outside this cash-flow set (labs, sovereigns, China, private) counts in full' },
    { l: 'Financing needed as % of AI capex', v: div(finNeed, S.capex_total), f: 'pct0', ind: 1 }]));
}
// 1. GW
h += sec('gw',""")
open(P, 'w', encoding='utf-8').write(s); print('applied')
