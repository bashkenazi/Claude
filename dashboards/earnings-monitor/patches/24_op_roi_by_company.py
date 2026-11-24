"""AI one page: section 5b, ROI by company (hyperscalers, Oracle, neoclouds, SpaceX). Requires op-internal-use v1.
Reads page db ai/one_page: rev.hs_ai_rev, rev.spacex_gross, co_rev {ORCL, CRWV, NBIS, META_total}. Marker "op-roi-co v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-roi-co v1' in s: print('already'); sys.exit(0)
assert 'op-internal-use v1' in s
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old)); s = s.replace(old, new)
rep("['who','5 Who installs'],", "['who','5 Who installs'],['roico','5b ROI by company'],")
JS = r"""
  /* op-roi-co v1: AI revenue, AI capex, installed base and ROI company by company */
  {
    const CR = d.co_rev || {}, RVH = R.hs_ai_rev || {};
    const ry = Y.includes(+I.roico_y) ? +I.roico_y : 2027, ri = Y.indexOf(ry);
    const metaUp = CR.META_total ? Y.map((_, i) => !i || nv(CR.META_total[i]) == null || nv(CR.META_total[0]) == null ? null : CR.META_total[i] - CR.META_total[0]) : Z();
    const revOf = { MSFT: RVH.Microsoft, AMZN: RVH.Amazon, GOOGL: RVH.Google, META: metaUp, ORCL: CR.ORCL, CRWV: CR.CRWV, NBIS: CR.NBIS, SPCX: R.spacex_gross };
    const revNote = { MSFT: 'AI Economics: Azure AI rental (incl. OpenAI) + Foundry + first-party (Copilot)', AMZN: 'AI Economics: AWS AI rental (incl. Anthropic) + Bedrock + first-party', GOOGL: 'AI Economics: GCP AI rental (incl. Anthropic) + Gemini platform + first-party', META: 'No disclosed AI revenue. Shown: growth in total revenue since 2023 (FactSet), an upper bound', ORCL: 'OCI revenue (all IaaS, not only AI); FactSet segment consensus, calendarized from May FY', CRWV: 'Total revenue, FactSet consensus', NBIS: 'Total revenue, FactSet consensus', SPCX: 'GPU rental revenue, gross (model build); excludes Grok subscriptions' };
    const cumS = a => { let c = 0, any = false; return Y.map((_, i) => { const v = nv(a && a[i]); if (v != null) { c += v; any = true; } return any ? c : null; }); };
    const avg2 = a => Y.map((_, i) => nv(a[i]) == null ? null : nv(a[i - 1]) == null ? a[i] : (a[i] + a[i - 1]) / 2);
    const dvG = (a, b, min) => Y.map((_, i) => nv(a[i]) == null || nv(b[i]) == null || b[i] < (min || 0.1) ? null : a[i] / b[i]);
    const rentFrac = k => { const it = IU.find(x => x[0] === k); return it ? 1 - iuOn(k) * iuPct(k, it[2]) / 100 : 1; };
    const mk = x => { const k = x.c.k, rev = revOf[k] || Z(), cap = cumS(x.ai), gw = x.cum || Z(), rf = rentFrac(k), gwA = avg2(gw);
      return { k, l: x.c.l + (k === 'META' ? ' (upper bound)' : ''), note: revNote[k] || '', rev, ai: x.ai, cap, gw, rf,
        rpg: dvG(rev, gwA), rprg: rf > 0.05 ? dvG(rev, gwA.map(v => nv(v) == null ? null : v * rf)) : Z(),
        roi: dvG(rev, cap, 0.5), capGw: dvG(cap, gw),
        inc: Y.map((_, i) => !i || nv(rev[i]) == null || nv(rev[i - 1]) == null || !(nv(x.ai[i - 1]) > 0.5) ? null : (rev[i] - rev[i - 1]) / x.ai[i - 1]) }; };
    const MH = H.map(mk), MN = N.map(mk);
    const sumS = arrs => Y.map((_, i) => arrs.some(a => nv(a && a[i]) == null) ? null : arrs.reduce((t, a) => t + a[i], 0));
    const agg = (X, label) => { const rev = sumS(X.map(m => m.rev)), ai = sumS(X.map(m => m.ai)), cap = sumS(X.map(m => m.cap)), gw = sumS(X.map(m => m.gw)), gwA = avg2(gw);
      return { k: '', l: label, rev, ai, cap, gw, rpg: dvG(rev, gwA), rprg: Z(), roi: dvG(rev, cap, 0.5), capGw: dvG(cap, gw),
        inc: Y.map((_, i) => !i || nv(rev[i]) == null || nv(rev[i - 1]) == null || !(nv(ai[i - 1]) > 0.5) ? null : (rev[i] - rev[i - 1]) / ai[i - 1]), b: 1 }; };
    const hsT = agg(MH.filter(m => m.k !== 'META'), 'Hyperscalers + Oracle, ex-Meta'), neoT = agg(MN, 'Neoclouds + SpaceX'), allT = agg(MH.filter(m => m.k !== 'META').concat(MN), 'All named, ex-Meta');
    const LIST = [{ sep: 'Hyperscalers and Oracle' }].concat(MH, [hsT, { sep: 'Neoclouds and SpaceX / xAI' }], MN, [neoT, allT]);
    const snapCols = [['rev', 'AI revenue, $bn', 'bn'], ['ai', 'AI capex, $bn', 'bn'], ['cap', 'Cum. AI capex since 2023, $bn', 'bn'], ['gw', 'AI GW installed', 'gw'], ['capGw', 'Cum. capex per installed GW', 'bn1'], ['rpg', 'Revenue per installed GW', 'bn1'], ['rprg', 'Revenue per rentable GW', 'bn1'], ['roi', 'ROI: revenue ÷ cum. capex', 'pct'], ['inc', 'Incremental: Δ revenue ÷ prior-year capex', 'pct']];
    const snap = `<div class="tbl-wrap"><table class="op-t op-roico"><thead><tr><th>${ry}E</th>${snapCols.map(c => `<th class="n">${c[1]}</th>`).join('')}</tr></thead><tbody>${LIST.map(m => m.sep ? `<tr><td colspan="${snapCols.length + 1}" class="op-sep">${m.sep}</td></tr>` : `<tr${m.b ? ' class="th-b"' : ''}><td${m.b ? '' : ' style="padding-left:20px"'} title="${esc(m.note || '')}">${m.b ? '<b>' + esc(m.l) + '</b>' : esc(m.l)}</td>${snapCols.map(([key, , f]) => { const v = m[key] ? m[key][ri] : null; return `<td class="n${nv(v) != null && v < 0 ? ' dn' : ''}">${cell(v, f)}</td>`; }).join('')}</tr>`).join('')}</tbody></table></div>`;
    const series = (key, f, lab, noteFn) => tbl(lab, LIST.map(m => m.sep ? m : { l: m.l, v: m[key], f, ind: m.b ? 0 : 1, b: m.b, note: noteFn ? noteFn(m) : '' }));
    const ySel = `<label class="op-l" style="max-width:none">Snapshot year<span><select class="op-sel" data-op="roico_y">${Y.filter(y => y >= 2024).map(y => `<option value="${y}"${y === ry ? ' selected' : ''}>${y}${y >= 2026 ? 'E' : ''}</option>`).join('')}</select></span></label>`;
    h += sec('roico', '5b · ROI by company', 'AI revenue: AI Economics v14, FactSet consensus, model build · AI capex and GW: section 5',
    `<div class="op-bar" role="group" aria-label="Snapshot year">${ySel}</div>
<p class="sub">ROI = AI revenue ÷ cumulative AI capex since 2023, the section 8 definition applied to each company. AI capex and GW come from section 5 (Street capex × AI share; AI Master GW by host), so the non-AI inputs there flow through. Revenue per rentable GW uses the internal-use inputs in section 6. Hover a company for its revenue source.</p>` +
    snap +
    series('roi', 'pct', 'ROI: AI revenue ÷ cumulative AI capex since 2023') +
    series('rev', 'bn', 'AI revenue, $bn', m => esc(m.note || '')) +
    `<details><summary>AI capex, installed base and revenue per GW by year</summary>` +
    series('ai', 'bn', 'AI capex, $bn') + series('cap', 'bn', 'Cumulative AI capex since 2023 (installed base), $bn') + series('gw', 'gw', 'AI GW installed, CITL') +
    series('capGw', 'bn1', 'Cumulative AI capex per installed GW, $bn') + series('rpg', 'bn1', 'AI revenue per installed GW (average of start and end of year), $bn') +
    series('rprg', 'bn1', 'AI revenue per rentable GW, $bn') + series('inc', 'pct', 'Incremental ROI: Δ AI revenue ÷ prior-year AI capex') + `</details>` +
    `<p class="sub">Read with care: hyperscaler AI revenue includes what OpenAI and Anthropic pay to rent capacity, so Microsoft, Amazon and Google partly earn the labs' revenue. Meta has no AI revenue line; its row assumes all revenue growth since 2023 came from AI. Oracle's OCI includes non-AI IaaS. Cumulative capex starts in 2023, while installed GW includes capacity built before 2023. Rows need at least $0.5bn of cumulative capex or 0.1 GW to show a ratio.</p>`);
  }
"""
rep("\n}\n// 6. GPU rental waterfall", "\n" + JS + "}\n// 6. GPU rental waterfall")
css = """
/* op-roi-co v1 */
table.op-roico th.n { white-space: normal; min-width: 92px; vertical-align: bottom; text-transform: none; letter-spacing: 0; font-size: 11.5px; }
"""
i = s.find('/* op-internal-use v1 */'); assert i > 0; s = s[:i] + css + s[i:]
open(P, 'w', encoding='utf-8').write(s); print('applied')
