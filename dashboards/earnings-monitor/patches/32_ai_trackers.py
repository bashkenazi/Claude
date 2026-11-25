"""AI tab: two new views. 'DC tracker' (data-center delays, cancellations, approvals, denials, permits; aggregate vs SRS US base)
and 'Token demand' (every quantification of token volume or growth). Data: page db ai/dc_tracker, ai/token_demand.
The One page section 12 reads ai/dc_tracker too, so there is one source. Marker "ai-trk v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'ai-trk v1' in s: print('already'); sys.exit(0)
def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (old[:80], s.count(old)); s = s.replace(old, new)
# modes
rep("return ['onepage', 'cheat', 'overview', 'tenets', 'data', 'compute', 'returns', 'consensus', 'financing'].includes(m)",
    "return ['onepage', 'cheat', 'overview', 'tenets', 'data', 'dctrack', 'tokens', 'compute', 'returns', 'consensus', 'financing'].includes(m)")
rep("['data', 'Models &amp; data'], ['compute', 'AI compute']", "['data', 'Models &amp; data'], ['dctrack', 'Data center tracker'], ['tokens', 'Token demand'], ['compute', 'AI compute']")
rep("const O = document.getElementById('v-aione'); if (O) O.hidden = m !== 'onepage';",
    "const O = document.getElementById('v-aione'); if (O) O.hidden = m !== 'onepage';\nconst K = document.getElementById('v-aitrk'); if (K) K.hidden = !(m === 'dctrack' || m === 'tokens'); /* ai-trk v1 */")
rep("if (m === 'onepage') { opLoad(); return; }", "if (m === 'onepage') { opLoad(); return; }\nif (m === 'dctrack' || m === 'tokens') { trkLoad(m); return; }")
rep('<div class="view" data-view="ai" id="v-aiframe" hidden></div>', '<div class="view" data-view="ai" id="v-aiframe" hidden></div>\n<div class="view" data-view="ai" id="v-aitrk" hidden></div>')
# one page reads the tracker doc
rep(".then(sn => { OP.loading = false; if (!sn || !sn.exists) {",
    ".then(async sn => { try { const db2 = await window.claude.use('db'); const t = db2 ? await db2.collection('ai').doc('dc_tracker').get() : null; if (t && t.exists && sn && sn.exists) { const dd = sn.data(); dd.dc_pushback = t.data(); sn = { exists: true, data: () => dd }; } } catch (e) {} return sn; })\n.then(sn => { OP.loading = false; if (!sn || !sn.exists) {")
JS = r"""
/* ai-trk v1: AI › Data center tracker and AI › Token demand */
const TRK = { docs: {}, loading: {}, f: (() => { try { return JSON.parse(localStorage.getItem('trk-f') || '{}') || {}; } catch (e) { return {}; } })() };
const trkSaveF = () => { try { localStorage.setItem('trk-f', JSON.stringify(TRK.f)); } catch (e) {} };
function trkLoad(m) {
  const C = document.getElementById('v-aitrk'); if (!C) return;
  const id = m === 'dctrack' ? 'dc_tracker' : 'token_demand';
  if (TRK.docs[id]) { (m === 'dctrack' ? trkDC : trkTok)(C, TRK.docs[id]); return; }
  if (TRK.loading[id]) return; TRK.loading[id] = 1;
  C.innerHTML = `<section class="panel"><p class="sub">Loading…</p></section>`;
  (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null))
    .then(db => db ? db.collection('ai').doc(id).get() : null)
    .then(sn => { TRK.loading[id] = 0; if (!sn || !sn.exists) { C.innerHTML = `<section class="panel"><p class="sub">Not loaded yet. Ask Claude to refresh this tracker.</p></section>`; return; } TRK.docs[id] = sn.data(); if (aiMode() === m) (m === 'dctrack' ? trkDC : trkTok)(C, TRK.docs[id]); })
    .catch(e => { TRK.loading[id] = 0; C.innerHTML = `<section class="panel"><p class="sub">Could not read the page database: ${esc(e && e.message || e)}</p></section>`; });
}
const trkOpt = (xs, v, all) => `<option value="">${all}</option>` + xs.map(x => `<option value="${esc(x)}"${x === v ? ' selected' : ''}>${esc(x)}</option>`).join('');
const trkBind = (C, rerender) => C.querySelectorAll('[data-trkf]').forEach(el => el.addEventListener(el.tagName === 'INPUT' ? 'input' : 'change', () => { TRK.f[el.dataset.trkf] = el.value; trkSaveF(); rerender(); }));
function trkDC(C, PB) {
  const cls = st => ({ cancelled: 'lost', denied: 'lost', relocated: 'lost', delayed: 'delayed', at_risk: 'risk', cleared: 'ok', approved: 'ok' })[st] || null;
  const yrs = Object.keys(PB.us_base).map(Number).sort(), T = PB.thresholds;
  const agg = {}; yrs.forEach(y => { agg[y] = { lost: 0, delayed: 0, risk: 0, ok: 0 }; });
  const P = PB.projects || [];
  P.forEach(p => { const k = cls(p.status); if (k && agg[p.year] && p.mw) agg[p.year][k] += p.mw / 1000; });
  const pc = v => (v * 100).toFixed(1) + '%', f1 = v => v ? v.toFixed(1) : '–';
  const flag = sh => sh >= T.red ? '🔴 Red' : sh >= T.amber ? '🟠 Amber' : '🟢 Green';
  const today = new Date(PB.as_of || Date.now()), ago = n => { const d = new Date(today); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
  const win = (a, b) => P.filter(p => p.date > ago(a) && p.date <= ago(b));
  const bad = xs => xs.filter(p => ['lost', 'delayed'].includes(cls(p.status))), mwOf = xs => xs.reduce((t, p) => t + (p.mw || 0), 0) / 1000;
  const w = [[30, 0], [60, 30], [90, 0], [180, 90]].map(([a, b]) => { const xs = win(a, b); return { n: bad(xs).length, mw: mwOf(bad(xs)), ok: mwOf(xs.filter(p => cls(p.status) === 'ok')) }; });
  const ST = { cancelled: '🔴🔴 Cancelled', denied: '🔴🔴 Denied', relocated: '🔴 Withdrawn / relocating', delayed: '🔴 Delayed', paused: '🟠 Paused (short)', at_risk: '🟠 At risk', cleared: '🟢 Approved / cleared', approved: '🟢 Approved / cleared' };
  const f = TRK.f, states = [...new Set(P.map(p => p.state))].sort(), stats = Object.keys(ST).filter(k => P.some(p => p.status === k));
  const q = (f.dq || '').toLowerCase();
  const rows = P.filter(p => (!f.dst || p.status === f.dst) && (!f.dstate || p.state === f.dstate) && (!f.dyr || String(p.year) === f.dyr) && (!q || JSON.stringify(p).toLowerCase().includes(q)))
    .sort((a, b) => b.date.localeCompare(a.date));
  C.innerHTML = `<section class="panel"><span class="eyebrow">AI · data center tracker</span><h1>Data center delays, cancellations, approvals and permits</h1>
<p class="op-call">${esc(PB.view)}</p>
<h3>Aggregate vs our US base case, GW</h3><div class="tbl-wrap"><table class="op-t"><thead><tr><th>Year first power was due</th><th class="n">SRS US base</th><th class="n">SRS bear</th><th class="n">Lost</th><th class="n">Delayed</th><th class="n">Lost + delayed</th><th class="n">% of base</th><th class="n">At risk</th><th class="n">Approved</th><th>Flag</th></tr></thead><tbody>${yrs.map(y => { const a = agg[y], b = PB.us_base[y], hit = a.lost + a.delayed; return `<tr><td><b>${y}</b></td><td class="n">${b}</td><td class="n">${PB.us_bear[y] ?? '–'}</td><td class="n">${f1(a.lost)}</td><td class="n">${f1(a.delayed)}</td><td class="n"><b>${f1(hit)}</b></td><td class="n">${pc(hit / b)}</td><td class="n">${f1(a.risk)}</td><td class="n">${f1(a.ok)}</td><td>${flag(hit / b)}</td></tr>`; }).join('')}</tbody></table></div>
<h3>Is it accelerating? Adverse events (lost + delayed) by window</h3><div class="tbl-wrap"><table class="op-t"><thead><tr><th>Window</th><th class="n">Events</th><th class="n">GW</th><th class="n">GW approved</th></tr></thead><tbody>${[['Last 30 days', w[0]], ['Prior 30 days', w[1]], ['Last 90 days', w[2]], ['Prior 90 days', w[3]]].map(([l, x]) => `<tr><td>${l}</td><td class="n">${x.n}</td><td class="n">${f1(x.mw)}</td><td class="n">${f1(x.ok)}</td></tr>`).join('')}</tbody></table></div>
<p class="sub">Flag on lost + delayed as a share of the SRS US base: amber ${pc(T.amber)}, red ${pc(T.red)}. ${esc(PB.rules)}</p>
<div class="op-bar" role="group" aria-label="Filters"><label class="op-l">Status<select data-trkf="dst">${trkOpt(stats, f.dst || '', 'All').replace(/>(\w+)</g, (m0, k) => '>' + (ST[k] || k) + '<')}</select></label><label class="op-l">State<select data-trkf="dstate">${trkOpt(states, f.dstate || '', 'All')}</select></label><label class="op-l">Year<select data-trkf="dyr">${trkOpt(yrs.map(String), f.dyr || '', 'All')}</select></label><label class="op-l">Search<input type="search" data-trkf="dq" value="${esc(f.dq || '')}" placeholder="Google, Texas, lawsuit…"></label><span class="sub" style="align-self:center">${rows.length} of ${P.length} events</span></div>
<div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Project</th><th>State</th><th class="n">MW</th><th>Status</th><th class="n">Year</th><th>What happened</th><th>Our view</th><th>Source</th></tr></thead><tbody>${rows.map(p => `<tr><td class="n">${esc(p.date)}</td><td><b>${esc(p.project)}</b><br><span class="sub">${esc(p.owner || '')}</span></td><td>${esc(p.state)}</td><td class="n">${p.mw ? p.mw.toLocaleString('en-US') : 'n/d'}<br><span class="sub">${esc(p.basis || '')}</span></td><td>${ST[p.status] || esc(p.status)}</td><td class="n">${p.year}</td><td>${esc(p.event)}</td><td>${esc(p.view || '')}</td><td class="note">${esc(p.src)}</td></tr>`).join('')}</tbody></table></div>
<h3>Policy actions</h3><div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Where</th><th>Action</th><th>Level</th><th>Source</th></tr></thead><tbody>${PB.policy.map(r => `<tr><td class="n">${esc(r[0])}</td><td><b>${esc(r[1])}</b></td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td class="note">${esc(r[4])}</td></tr>`).join('')}</tbody></table></div>
<h3>Street estimates of the aggregate hit</h3><ul class="b">${PB.street.map(r => `<li><b>${esc(r[0])}:</b> ${esc(r[1])} <span class="sub">(${esc(r[2])})</span></li>`).join('')}</ul>
<p class="sub">As of ${esc(PB.as_of)}. The daily digests add project events (approvals, denials, permits, delays, cancellations) as they find them.</p></section>`;
  trkBind(C, () => trkDC(C, PB));
}
function trkTok(C, TD) {
  const R = TD.rows || [], f = TRK.f, q = (f.tq || '').toLowerCase();
  const cos = [...new Set(R.map(r => r.co))].sort(), kinds = [...new Set(R.map(r => r.kind))].sort();
  const KL = { absolute: 'Absolute volume', growth: 'Growth rate', forecast: 'Forecast', share: 'Share', pricing: 'Token pricing' };
  const abs = R.filter(r => r.tpm != null).sort((a, b) => a.date.localeCompare(b.date));
  const latest = {}; abs.forEach(r => { const k = r.co + '|' + r.metric; latest[k] = latest[k] || []; latest[k].push(r); });
  const latRows = Object.values(latest).map(xs => { const l = xs[xs.length - 1], p = xs.length > 1 ? xs[xs.length - 2] : null; return { l, p, g: p ? l.tpm / p.tpm : null }; }).sort((a, b) => b.l.tpm - a.l.tpm);
  const rows = R.filter(r => (!f.tco || r.co === f.tco) && (!f.tkind || r.kind === f.tkind) && (!q || JSON.stringify(r).toLowerCase().includes(q))).sort((a, b) => b.date.localeCompare(a.date));
  const fq = v => v == null ? '–' : v >= 10 ? v.toFixed(0) : v >= 1 ? v.toFixed(2) : v.toFixed(3);
  C.innerHTML = `<section class="panel"><span class="eyebrow">AI · token demand</span><h1>Token demand and pricing: every number we have</h1>
<p class="op-call">${esc(TD.view)}</p>
<h3>Latest absolute volumes (${esc(TD.unit)})</h3><div class="tbl-wrap"><table class="op-t"><thead><tr><th>Company · metric</th><th class="n">Latest</th><th class="n">As of</th><th class="n">Prior</th><th class="n">Prior date</th><th class="n">Change</th><th>Basis</th></tr></thead><tbody>${latRows.map(x => `<tr><td><b>${esc(x.l.co)}</b> · ${esc(x.l.metric)}</td><td class="n"><b>${fq(x.l.tpm)}</b></td><td class="n">${esc(x.l.date)}</td><td class="n">${x.p ? fq(x.p.tpm) : '–'}</td><td class="n">${x.p ? esc(x.p.date) : '–'}</td><td class="n">${x.g ? x.g.toFixed(1) + 'x' : '–'}</td><td class="note">${esc(x.l.value)}</td></tr>`).join('')}</tbody></table></div>
<p class="sub">Volumes are not comparable across companies: first-party API, all surfaces and claimed serving volumes are counted differently.</p>
<div class="op-bar" role="group" aria-label="Filters"><label class="op-l">Company<select data-trkf="tco">${trkOpt(cos, f.tco || '', 'All')}</select></label><label class="op-l">Type<select data-trkf="tkind">${trkOpt(kinds, f.tkind || '', 'All').replace(/>(\w+)</g, (m0, k) => '>' + (KL[k] || k) + '<')}</select></label><label class="op-l">Search<input type="search" data-trkf="tq" value="${esc(f.tq || '')}" placeholder="Gemini, Bedrock, China…"></label><span class="sub" style="align-self:center">${rows.length} of ${R.length} datapoints</span></div>
<div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Company</th><th>Type</th><th>Metric</th><th>Number</th><th class="n">Quadrillion / month</th><th>Context</th><th>Source</th></tr></thead><tbody>${rows.map(r => `<tr><td class="n">${esc(r.date)}</td><td><b>${esc(r.co)}</b><br><span class="sub">${esc(r.tk)}</span></td><td>${esc(KL[r.kind] || r.kind)}</td><td>${esc(r.metric)}</td><td><b>${esc(r.value)}</b></td><td class="n">${fq(r.tpm)}</td><td>${esc(r.note || '')}</td><td class="note">${esc(r.src)} · ${esc(r.st || '')}</td></tr>`).join('')}</tbody></table></div>
<p class="sub">As of ${esc(TD.as_of)}. The daily digests add any token-volume or token-growth number they find.</p></section>`;
  trkBind(C, () => trkTok(C, TD));
}
"""
rep("// One AI tab: #v-aimode holds the switch", JS + "\n// One AI tab: #v-aimode holds the switch")
open(P, 'w', encoding='utf-8').write(s); print('applied')
