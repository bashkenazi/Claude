"""AI tab: 'GPU market' view (renewals, non-renewals, re-marketed capacity, list-price moves, rental price points;
looser vs tighter scorecard). Data: page db ai/gpu_market. Requires ai-trk v1. Marker "ai-gpu v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'ai-gpu v1' in s: print('already'); sys.exit(0)
assert 'ai-trk v1' in s
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)
rep("'data', 'dctrack', 'tokens', 'compute'", "'data', 'dctrack', 'tokens', 'gpus', 'compute'")
rep("['tokens', 'Token demand'], ['compute', 'AI compute']", "['tokens', 'Token demand'], ['gpus', 'GPU market'], ['compute', 'AI compute']")
rep("if (K) K.hidden = !(m === 'dctrack' || m === 'tokens');", "if (K) K.hidden = !(m === 'dctrack' || m === 'tokens' || m === 'gpus');")
rep("if (m === 'dctrack' || m === 'tokens') { trkLoad(m); return; }", "if (m === 'dctrack' || m === 'tokens' || m === 'gpus') { trkLoad(m); return; }")
rep("const id = m === 'dctrack' ? 'dc_tracker' : 'token_demand';", "const id = m === 'dctrack' ? 'dc_tracker' : m === 'gpus' ? 'gpu_market' : 'token_demand'; /* ai-gpu v1 */\n  const RF = m === 'dctrack' ? trkDC : m === 'gpus' ? trkGpu : trkTok;")
rep("if (TRK.docs[id]) { (m === 'dctrack' ? trkDC : trkTok)(C, TRK.docs[id]); return; }", "if (TRK.docs[id]) { RF(C, TRK.docs[id]); return; }")
rep("if (aiMode() === m) (m === 'dctrack' ? trkDC : trkTok)(C, TRK.docs[id]);", "if (aiMode() === m) RF(C, TRK.docs[id]);")
JS = r"""
function trkGpu(C, G) {
  const E = G.events || [], PR = G.prices || [], f = TRK.f, q = (f.gq || '').toLowerCase();
  const SG = { looser: '🔵 Looser', tighter: '🟠 Tighter', neutral: '⚪ Neutral' };
  const asOf = new Date(G.as_of || Date.now()), ago = n => { const d = new Date(asOf); d.setDate(d.getDate() - n); return d.toISOString().slice(0, 10); };
  const all = E.map(x => ({ date: x.date, signal: x.signal })).concat(PR.map(x => ({ date: x.date, signal: x.signal })));
  const cnt = (a, b, sg) => all.filter(x => x.date > ago(a) && x.date <= ago(b) && x.signal === sg).length;
  const win = [['Last 30 days', 30, 0], ['Prior 30 days', 60, 30], ['Last 90 days', 90, 0]].map(([l, a, b]) => { const lo = cnt(a, b, 'looser'), ti = cnt(a, b, 'tighter'); return `<tr><td>${l}</td><td class="n">${lo}</td><td class="n">${ti}</td><td>${lo > ti ? '🔵 Loosening' : ti > lo ? '🟠 Tight' : '⚪ Mixed'}</td></tr>`; }).join('');
  const ev = E.filter(x => (!f.gsig || x.signal === f.gsig) && (!q || JSON.stringify(x).toLowerCase().includes(q))).sort((a, b) => b.date.localeCompare(a.date));
  const pr = PR.filter(x => (!f.gsig || x.signal === f.gsig) && (!q || JSON.stringify(x).toLowerCase().includes(q))).sort((a, b) => b.date.localeCompare(a.date));
  C.innerHTML = `<section class="panel"><span class="eyebrow">AI · GPU market</span><h1>GPU market: renewals, non-renewals and rental prices</h1>
<p class="op-call">${esc(G.view)}</p>
<h3>Scorecard: looser vs tighter signals</h3><div class="tbl-wrap"><table class="op-t"><thead><tr><th>Window</th><th class="n">🔵 Looser</th><th class="n">🟠 Tighter</th><th>Read</th></tr></thead><tbody>${win}</tbody></table></div>
<div class="op-bar" role="group" aria-label="Filters"><label class="op-l">Signal<select data-trkf="gsig">${trkOpt(['looser', 'tighter', 'neutral'], f.gsig || '', 'All')}</select></label><label class="op-l">Search<input type="search" data-trkf="gq" value="${esc(f.gq || '')}" placeholder="H200, SpaceX, renewal…"></label></div>
<h3>Contract events: renewals, non-renewals, re-marketed capacity, list-price moves</h3><div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Signal</th><th>Event</th><th>Lessee</th><th>Lessor</th><th>GPU · quantity</th><th>Price</th><th>Available</th><th>Context</th><th>Source</th></tr></thead><tbody>${ev.map(x => `<tr><td class="n">${esc(x.date)}</td><td>${SG[x.signal] || esc(x.signal)}</td><td><b>${esc(x.event)}</b></td><td>${esc(x.lessee)}</td><td>${esc(x.lessor)}</td><td>${esc(x.gpu)}<br><span class="sub">${esc(x.qty || '')}</span></td><td>${esc(x.price || '')}</td><td>${esc(x.avail || '')}</td><td>${esc(x.note || '')}</td><td class="note">${esc(x.src)}</td></tr>`).join('')}</tbody></table></div>
<h3>Rental price points</h3><div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Signal</th><th>GPU</th><th>Term / index</th><th>Price ($/GPU-hr)</th><th>Change</th><th>Source</th></tr></thead><tbody>${pr.map(x => `<tr><td class="n">${esc(x.date)}</td><td>${SG[x.signal] || esc(x.signal)}</td><td><b>${esc(x.gpu)}</b></td><td>${esc(x.term)}</td><td>${esc(x.price)}</td><td>${esc(x.chg)}</td><td class="note">${esc(x.src)}</td></tr>`).join('')}</tbody></table></div>
<p class="sub">As of ${esc(G.as_of)}. 🔵 looser = more supply or lower prices (non-renewals, re-marketed clusters, price cuts); 🟠 tighter = renewals at premiums, price increases. The daily digests add these as they find them.</p></section>`;
  trkBind(C, () => trkGpu(C, G));
}
"""
rep("function trkTok(C, TD) {", JS + "function trkTok(C, TD) {")
open(P, 'w', encoding='utf-8').write(s); print('applied')
