/* Markets tab v1 (2026-11-18): macro + technical health, market direction and cyclical/defensive rotation.
   Data: page database docs markets/summary, markets/study, markets/series_macro, markets/series_sig, markets/series_px,
   written weekly by jobs/markets-weekly (Bloomberg 1970-2018 history + FactSet). Breadth comes from technicals/breadth. */
(function () {
  const MK = { sum: null, study: null, ser: {}, err: '', loaded: false, q: '', grp: 'All', st: 'all', stale: false, sort: ['grp', 1],
    sel: 'SIG_curve', cmp: '', spx: true, range: 240, tf: 'lvl', ev: 'market', evSort: ['spread', -1], etf: 'sect', etfSort: ['r3m', -1], src: 'All' };
  try { const s = JSON.parse(localStorage.getItem('td-mk') || '{}'); ['sel', 'spx', 'range', 'tf', 'ev', 'grp', 'stale', 'etf'].forEach(k => { if (s[k] != null) MK[k] = s[k]; }); } catch (e) {}
  const save = () => { try { localStorage.setItem('td-mk', JSON.stringify({ sel: MK.sel, spx: MK.spx, range: MK.range, tf: MK.tf, ev: MK.ev, grp: MK.grp, stale: MK.stale, etf: MK.etf })); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  // signal display: fractions shown as %, threshold for the chart guide line
  const FRAC = new Set(['trend10', 'mom12', 'claims', 'permits', 'credit', 'breadth', 'rotmom']);
  const THR = { trend10: 0, mom12: 0, curve: 0, claims: .10, sahm: .5, nfp3: 0, ism: 50, ism_chg: 0, empire_chg: 0, capex: 0, ipm: 0, permits: 0, nahb: 50, ff12: 0, realff: 1.5, y10chg: .75, cpi_chg: 0, cpi: 4, umich: -1, erp: 2, fwdpe: 17, m2: 3, ci: 0, credit: 0, breadth: 0, rotmom: 0 };
  const fv = (k, v, d) => { if (v == null || isNaN(v)) return '—'; if (FRAC.has(k)) return (v * 100).toFixed(d == null ? 1 : d) + '%'; const a = Math.abs(v); return a >= 1000 ? Math.round(v).toLocaleString() : a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2); };
  const pc = (v, d = 1) => v == null || isNaN(v) ? '—' : (v > 0 ? '+' : '') + (+v).toFixed(d) + '%';
  const fmtMonth = m => { const [y, mo] = m.split('-'); return new Date(Date.UTC(+y, +mo - 1, 15)).toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }); };
  const fmtD = iso => iso ? new Date(iso.slice(0, 10) + 'T12:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }) : '—';

  const css = `
  #v-markets .mk-gauges { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 12px; }
  #v-markets .mk-g { border: 1px solid var(--rule); border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; background: var(--surface); min-width: 0; }
  #v-markets .mk-g h3 { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
  #v-markets .mk-g .big { font-family: var(--f-mono); font-size: 24px; font-weight: 600; }
  #v-markets .mk-meter { position: relative; height: 10px; border-radius: 5px; background: linear-gradient(90deg, var(--neg-wash), var(--surface-2) 50%, var(--pos-wash)); }
  #v-markets .mk-meter i { position: absolute; top: -3px; width: 4px; height: 16px; border-radius: 2px; background: var(--ink); transform: translateX(-2px); }
  #v-markets .mk-meter b { position: absolute; top: -3px; width: 2px; height: 16px; background: var(--muted); opacity: .6; transform: translateX(-1px); }
  #v-markets .mk-scale { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }
  #v-markets .mk-votes { display: flex; flex-wrap: wrap; gap: 4px; }
  #v-markets .chip.v-on { background: var(--pos-wash); color: var(--pos); } #v-markets .chip.v-off { background: var(--neg-wash); color: var(--neg); }
  #v-markets .mk-call .li { cursor: default; } #v-markets .mk-call .li[data-keys] { cursor: pointer; } #v-markets .mk-call .li[data-keys]:hover { background: var(--surface-2); }
  #v-markets .stripe.warn { background: var(--warn); }
  #v-markets .mk-kind { font-size: 10.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 650; margin-right: 6px; }
  #v-markets table.mk-t th[data-k] { cursor: pointer; user-select: none; white-space: nowrap; }
  #v-markets table.mk-t th[aria-sort="ascending"]::after { content: " ▲"; } #v-markets table.mk-t th[aria-sort="descending"]::after { content: " ▼"; }
  #v-markets table.mk-t tbody tr { cursor: pointer; } #v-markets table.mk-t tbody tr[aria-selected="true"] td { background: var(--accent-wash); }
  #v-markets table.mk-t td.sig { white-space: normal; min-width: 210px; }
  #v-markets .st { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 600; white-space: nowrap; }
  #v-markets .st.bull { background: var(--pos-wash); color: var(--pos); } #v-markets .st.bear { background: var(--neg-wash); color: var(--neg); }
  #v-markets .st.stale { background: var(--surface-2); color: var(--muted); }
  #v-markets .pbar { display: inline-flex; align-items: center; gap: 6px; } #v-markets .pbar span { width: 54px; height: 6px; background: var(--surface-2); border-radius: 3px; position: relative; display: inline-block; }
  #v-markets .pbar span i { position: absolute; top: -2px; width: 3px; height: 10px; background: var(--ink-2); border-radius: 1px; }
  #v-markets .mk-ctl { display: flex; gap: 8px 12px; flex-wrap: wrap; align-items: center; font-size: 12.5px; }
  #v-markets .mk-ctl input[type=search] { width: 200px; }
  #v-markets .mk-ctl label { display: inline-flex; gap: 6px; align-items: center; color: var(--muted); }
  #v-markets .mk-chart { width: 100%; height: auto; display: block; }
  #v-markets .mk-chart text { fill: var(--muted); font-family: var(--f-mono); font-size: 10px; }
  #v-markets .mk-chart .grid { stroke: var(--rule); } #v-markets .mk-chart .zero { stroke: var(--rule-2); }
  #v-markets .mk-chart .thr { stroke: var(--warn); stroke-dasharray: 4 4; }
  #v-markets .mk-chart .l1 { fill: none; stroke: var(--accent); stroke-width: 1.8; } #v-markets .mk-chart .l2 { fill: none; stroke: var(--mv2, #eb6834); stroke-width: 1.5; }
  #v-markets .mk-chart .lsp { fill: none; stroke: var(--muted); stroke-width: 1.2; opacity: .7; }
  #v-markets .mk-chart .bear-band { fill: var(--neg); opacity: .07; }
  #v-markets .mk-chart .hov { stroke: var(--muted); } #v-markets .mk-tip { position: fixed; z-index: 60; pointer-events: none; background: var(--surface); border: 1px solid var(--rule-2); border-radius: 6px; padding: 6px 9px; font-size: 12px; box-shadow: 0 6px 18px rgba(0,0,0,.16); }
  #v-markets .mk-key { display: flex; gap: 6px 14px; flex-wrap: wrap; font-size: 12px; color: var(--ink-2); }
  #v-markets .mk-key i { display: inline-block; width: 14px; height: 2px; vertical-align: middle; margin-right: 5px; }
  #v-markets .mk-grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 520px), 1fr)); gap: 18px; }
  #v-markets .mk-note { font-size: 12px; color: var(--muted); margin: 0; max-width: 110ch; }
  #v-markets .mk-cmp { min-width: 0; max-width: 100%; }
  #v-markets select { max-width: 100%; }
  `;
  function ensureCss() { if (document.getElementById('mk-css')) return; const s = document.createElement('style'); s.id = 'mk-css'; s.textContent = css; document.head.appendChild(s); }

  // -------------------------------------------------------------- series helpers
  function getS(id) {
    for (const d of Object.values(MK.ser)) if (d && d.s && d.s[id]) {
      const s = d.s[id]; const [y0, m0] = d.m0.split('-').map(Number);
      return { id, n: s.n, g: s.g, u: s.u, pts: s.v.map((v, j) => { const mi = y0 * 12 + (m0 - 1) + s.o + j; return { t: mi, d: `${Math.floor(mi / 12)}-${String(mi % 12 + 1).padStart(2, '0')}`, v }; }).filter(p => p.v != null) };
    }
    return null;
  }
  function transform(S, tf) {
    if (!S || tf === 'lvl') return S;
    const by = new Map(S.pts.map(p => [p.t, p.v]));
    let pts;
    if (tf === 'yoy') pts = S.pts.map(p => { const o = by.get(p.t - 12); return o ? { ...p, v: (p.v / o - 1) * 100 } : null; }).filter(Boolean);
    else if (tf === 'chg') pts = S.pts.map(p => { const o = by.get(p.t - 12); return o != null ? { ...p, v: p.v - o } : null; }).filter(Boolean);
    else pts = S.pts.map((p, j) => { const w = S.pts.slice(Math.max(0, j - 119), j + 1).map(x => x.v); if (w.length < 36) return null; const m = w.reduce((a, b) => a + b, 0) / w.length; const sd = Math.sqrt(w.reduce((a, b) => a + (b - m) ** 2, 0) / w.length); return sd ? { ...p, v: (p.v - m) / sd } : null; }).filter(Boolean);
    return { ...S, pts, u: tf === 'yoy' ? '% y/y' : tf === 'chg' ? '12m chg' : 'z (10y)' };
  }

  // -------------------------------------------------------------- chart
  function chart(A, B, spx, key, W, H) {
    const last = Math.max(...[A, B].filter(Boolean).map(s => s.pts.length ? s.pts[s.pts.length - 1].t : 0));
    const t0 = MK.range >= 9999 ? Math.min(...[A, B].filter(Boolean).map(s => s.pts.length ? s.pts[0].t : last)) : last - MK.range;
    const cut = s => s ? s.pts.filter(p => p.t >= t0) : [];
    const a = cut(A), b = cut(B), sp = spx ? cut(spx) : [];
    if (a.length < 2) return '<p class="mk-note">Not enough history in this range.</p>';
    const L = 56, R = (b.length || sp.length) ? 60 : 14, T = 14, Bm = 24, pw = W - L - R, ph = H - T - Bm;
    const X = t => L + (t - t0) / Math.max(1, last - t0) * pw;
    const ext = arr => { const v = arr.map(p => p.v); let lo = Math.min(...v), hi = Math.max(...v); if (lo === hi) { lo -= 1; hi += 1; } const pad = (hi - lo) * .06; return [lo - pad, hi + pad]; };
    let [y0, y1] = ext(a); const thr = MK.tf === 'lvl' && key && THR[key] != null ? THR[key] : null;
    if (thr != null) { y0 = Math.min(y0, thr); y1 = Math.max(y1, thr); }
    const Y = v => T + (1 - (v - y0) / (y1 - y0)) * ph;
    const rs = b.length ? b : sp; const logR = !b.length && sp.length;
    let r0 = 0, r1 = 1; if (rs.length) { const v = rs.map(p => logR ? Math.log(p.v) : p.v); r0 = Math.min(...v); r1 = Math.max(...v); if (r0 === r1) r1 = r0 + 1; }
    const YR = v => T + (1 - ((logR ? Math.log(v) : v) - r0) / (r1 - r0)) * ph;
    const path = (arr, f) => arr.map((p, j) => (j ? 'L' : 'M') + X(p.t).toFixed(1) + ' ' + f(p.v).toFixed(1)).join('');
    let g = '';
    // bearish-state shading for signals
    if (key && MK.tf === 'lvl' && MK.sum) { const rule = bullRule(key); if (rule) { let st = null; a.forEach((p, j) => { const bear = !rule(p.v); if (bear && st == null) st = p.t; if ((!bear || j === a.length - 1) && st != null) { const e = bear ? p.t : p.t; g += `<rect class="bear-band" x="${X(st).toFixed(1)}" y="${T}" width="${Math.max(1, X(e) - X(st)).toFixed(1)}" height="${ph}"/>`; st = null; } }); } }
    // grid & axes
    const yrs = []; for (let t = Math.ceil(t0 / 12) * 12; t <= last; t += 12) yrs.push(t);
    const step = Math.ceil(yrs.length / 10);
    yrs.forEach((t, j) => { if (j % step) return; const x = X(t).toFixed(1); g += `<line class="grid" x1="${x}" x2="${x}" y1="${T}" y2="${T + ph}"/><text x="${x}" y="${H - 6}" text-anchor="middle">${t / 12}</text>`; });
    for (let i = 0; i <= 4; i++) { const v = y0 + (y1 - y0) * i / 4, y = Y(v).toFixed(1); g += `<line class="grid" x1="${L}" x2="${L + pw}" y1="${y}" y2="${y}"/><text x="${L - 6}" y="${+y + 3.5}" text-anchor="end">${fv(MK.tf === 'lvl' ? key : '', v)}</text>`; }
    if (rs.length) for (let i = 0; i <= 4; i++) { const vv = r0 + (r1 - r0) * i / 4, v = logR ? Math.exp(vv) : vv; g += `<text x="${L + pw + 6}" y="${(T + (1 - i / 4) * ph + 3.5).toFixed(1)}">${fv('', v)}</text>`; }
    if (y0 < 0 && y1 > 0) g += `<line class="zero" x1="${L}" x2="${L + pw}" y1="${Y(0).toFixed(1)}" y2="${Y(0).toFixed(1)}"/>`;
    if (thr != null) g += `<line class="thr" x1="${L}" x2="${L + pw}" y1="${Y(thr).toFixed(1)}" y2="${Y(thr).toFixed(1)}"/>`;
    if (sp.length && !b.length) g += `<path class="lsp" d="${path(sp, YR)}"/>`;
    if (b.length) g += `<path class="l2" d="${path(b, YR)}"/>`;
    g += `<path class="l1" d="${path(a, Y)}"/><line class="hov" x1="0" x2="0" y1="${T}" y2="${T + ph}" style="display:none"/><rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="transparent" class="hit"/>`;
    MK._hover = { L, pw, t0, last, a, b, sp, key };
    return `<svg class="mk-chart" id="mk-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(A.n)} history">${g}</svg>`;
  }
  function bullRule(key) {
    const r = { trend10: v => v > 0, mom12: v => v > 0, curve: v => v > 0, claims: v => v < .10, sahm: v => v < .5, nfp3: v => v > 0, ism: v => v > 50, ism_chg: v => v > 0, empire_chg: v => v > 0, capex: v => v > 0, ipm: v => v > 0,
      permits: v => v > 0, nahb: v => v > 50, ff12: v => v <= 0, realff: v => v < 1.5, y10chg: v => v < .75, cpi_chg: v => v <= 0, cpi: v => v < 4, umich: v => v < -1, erp: v => v > 2, fwdpe: v => v < 17, m2: v => v > 3, ci: v => v > 0,
      credit: v => v > 0, breadth: v => v > 0, rotmom: v => v > 0, curve_resteep: v => v > .5 };
    return r[key];
  }
  function wireHover(host) {
    const svg = host.querySelector('#mk-svg'); if (!svg) return; const H = MK._hover; const hov = svg.querySelector('.hov');
    let tip = document.querySelector('.mk-tip'); if (!tip) { tip = document.createElement('div'); tip.className = 'mk-tip'; tip.style.display = 'none'; document.body.appendChild(tip); }
    const near = (arr, t) => { let best = null; for (const p of arr) { if (p.t <= t) best = p; else break; } return best; };
    svg.querySelector('.hit').addEventListener('mousemove', e => {
      const r = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal, x = (e.clientX - r.left) * vb.width / r.width;
      const t = Math.round(H.t0 + (x - H.L) / H.pw * (H.last - H.t0)); const pa = near(H.a, t); if (!pa) return;
      const px = H.L + (pa.t - H.t0) / Math.max(1, H.last - H.t0) * H.pw; hov.setAttribute('x1', px); hov.setAttribute('x2', px); hov.style.display = '';
      const pb = H.b.length ? near(H.b, t) : null, ps = H.sp.length ? near(H.sp, t) : null;
      tip.innerHTML = `<b>${fmtMonth(pa.d)}</b><br>${esc(MK._nA)}: <b class="mono">${fv(MK.tf === 'lvl' ? H.key : '', pa.v)}</b>` + (pb ? `<br>${esc(MK._nB)}: <b class="mono">${fv('', pb.v)}</b>` : '') + (ps && !pb ? `<br>S&amp;P 500: <b class="mono">${Math.round(ps.v).toLocaleString()}</b>` : '');
      tip.style.display = ''; tip.style.left = Math.min(window.innerWidth - 220, e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 12) + 'px';
    });
    svg.querySelector('.hit').addEventListener('mouseleave', () => { hov.style.display = 'none'; tip.style.display = 'none'; });
  }
  function relChart(rel, W, H) {
    if (!rel || rel.length < 5) return '';
    const L = 46, R = 12, T = 12, B = 22, pw = W - L - R, ph = H - T - B, v = rel.map(r => r[1]), lo = Math.min(...v), hi = Math.max(...v);
    const X = j => L + j / (rel.length - 1) * pw, Y = x => T + (1 - (x - lo) / ((hi - lo) || 1)) * ph;
    let g = ''; for (let i = 0; i <= 3; i++) { const x = lo + (hi - lo) * i / 3; g += `<line class="grid" x1="${L}" x2="${L + pw}" y1="${Y(x).toFixed(1)}" y2="${Y(x).toFixed(1)}"/><text x="${L - 6}" y="${(Y(x) + 3.5).toFixed(1)}" text-anchor="end">${x.toFixed(2)}</text>`; }
    let mo = ''; rel.forEach((r, j) => { const m = r[0].slice(0, 2); if (m !== mo) { mo = m; g += `<text x="${X(j).toFixed(1)}" y="${H - 6}">${new Date(Date.UTC(2000, +m - 1, 15)).toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' })}</text>`; } });
    const ma = v.map((_, j) => j >= 49 ? v.slice(j - 49, j + 1).reduce((a, b) => a + b, 0) / 50 : null);
    g += `<path class="lsp" d="${ma.map((m, j) => m == null ? '' : (ma[j - 1] == null ? 'M' : 'L') + X(j).toFixed(1) + ' ' + Y(m).toFixed(1)).join('')}"/>`;
    g += `<path class="l1" d="${v.map((x, j) => (j ? 'L' : 'M') + X(j).toFixed(1) + ' ' + Y(x).toFixed(1)).join('')}"/>`;
    return `<svg class="mk-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Cyclicals versus defensives, daily">${g}</svg>`;
  }

  // -------------------------------------------------------------- tables
  function sortRows(rows, [k, dir], get) { return rows.slice().sort((a, b) => { const x = get(a, k), y = get(b, k); if (x == null && y == null) return 0; if (x == null) return 1; if (y == null) return -1; return (x < y ? -1 : x > y ? 1 : 0) * dir; }); }
  function th(lbl, k, cur, cls = '') { const s = cur[0] === k ? (cur[1] > 0 ? 'ascending' : 'descending') : 'none'; return `<th class="${cls}" data-k="${k}" aria-sort="${s}">${lbl}</th>`; }

  function scorecard(S) {
    const groups = ['All', ...new Set(S.signals.map(s => s.group))];
    let rows = S.signals.filter(s => (MK.stale || !s.stale) && (MK.grp === 'All' || s.group === MK.grp)
      && (MK.st === 'all' || (MK.st === 'flip' ? s.flipped : s.state === MK.st)) && (!MK.q || (s.label + ' ' + s.group + ' ' + s.desc).toLowerCase().includes(MK.q.toLowerCase())));
    const get = (s, k) => ({ grp: s.group + s.label, sig: s.label, date: s.date, val: s.value, pct: s.pct, st: s.state, ic: s.mkt ? Math.abs(s.mkt.ic) : null,
      spread: s.mkt ? s.mkt.spread : null, dd: s.mkt && s.mkt.bear_dd != null ? s.mkt.bear_dd - (s.mkt.bull_dd || 0) : null, rot: s.rot ? s.rot.spread : null }[k]);
    rows = sortRows(rows, MK.sort, get);
    const body = rows.map(s => {
      const m = s.mkt || {}, r = s.rot || {};
      return `<tr data-sig="${esc(s.key)}" aria-selected="${MK.sel === 'SIG_' + s.key}" tabindex="0" title="${esc(s.desc)}">
        <td class="sig"><b>${esc(s.label)}</b>${s.flipped ? ' <span class="chip">changed</span>' : ''}<div class="sub">${esc(s.group)}</div></td>
        <td class="n">${fmtMonth(s.date)}</td><td class="n"><b>${fv(s.key, s.value)}</b></td><td class="n muted">${fv(s.key, s.m1)}</td><td class="n muted">${fv(s.key, s.m3)}</td><td class="n muted">${fv(s.key, s.m12)}</td>
        <td class="n"><span class="pbar"><span><i style="left:${s.pct == null ? 0 : s.pct * .54 - 1.5}px"></i></span>${s.pct == null ? '—' : Math.round(s.pct)}</span></td>
        <td><span class="st ${s.stale ? 'stale' : s.state}">${s.stale ? 'stale' : s.state === 'bull' ? 'Benign' : 'Cautionary'}</span></td>
        <td class="n">${m.bull_avg == null ? '—' : pc(m.bull_avg) + ' / ' + pc(m.bear_avg)}</td>
        <td class="n">${m.bull_dd == null ? '—' : Math.round(m.bull_dd * 100) + '% / ' + Math.round(m.bear_dd * 100) + '%'}</td>
        <td class="n">${m.ic == null ? '—' : m.ic.toFixed(2)}</td>
        <td class="n">${r.spread == null ? '—' : pc(r.spread)}</td></tr>`;
    }).join('');
    return `<section class="panel" id="mk-score"><div class="panel-h"><h2>Indicator scorecard</h2><span class="muted">${rows.length} of ${S.signals.length} signals · click a row to chart it</span></div>
      <div class="mk-ctl"><input type="search" id="mk-q" placeholder="Search signals" value="${esc(MK.q)}" aria-label="Search signals">
        <label>Group <select id="mk-grp">${groups.map(g => `<option ${g === MK.grp ? 'selected' : ''}>${esc(g)}</option>`).join('')}</select></label>
        <div class="seg" id="mk-st">${[['all', 'All'], ['bull', 'Benign'], ['bear', 'Cautionary'], ['flip', 'Changed']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${MK.st === v}">${l}</button>`).join('')}</div>
        <label><input type="checkbox" id="mk-stale" ${MK.stale ? 'checked' : ''}> Show stale</label></div>
      <div class="tbl-wrap"><table class="mk-t" id="mk-tbl"><thead><tr>${th('Signal', 'grp', MK.sort)}${th('Data', 'date', MK.sort, 'n')}${th('Latest', 'val', MK.sort, 'n')}<th class="n">1m ago</th><th class="n">3m ago</th><th class="n">12m ago</th>${th('Pctile', 'pct', MK.sort, 'n')}${th('State', 'st', MK.sort)}${th('Next-12m S&amp;P: benign / cautionary', 'spread', MK.sort, 'n')}${th('15% drawdown odds', 'dd', MK.sort, 'n')}${th('Rank IC', 'ic', MK.sort, 'n')}${th('Cyc − def, next 6m', 'rot', MK.sort, 'n')}</tr></thead><tbody>${body}</tbody></table></div>
      <p class="mk-note">Benign/cautionary is each signal's rule (hover a row for it). Evidence columns: average next-12-month S&amp;P price return and the share of months followed by a 15%+ drawdown within 12 months, in the benign vs cautionary state, 1970 (or series start) to today. Rank IC is the rank correlation of the signal with the next-12-month return. Cyc − def is the next-6-month return of cyclicals minus defensives in the benign state less the cautionary state, 2006-2026. Monthly overlapping windows: treat small differences as noise.</p></section>`;
  }

  function gauge(title, score, bucket, votes, labels, inv, histLine, scaleL, scaleR, prev) {
    const x = score == null ? 50 : (score + 1) * 50, px = prev == null ? null : (prev + 1) * 50;
    return `<div class="mk-g"><h3><span>${title}</span><span class="big">${score == null ? '—' : (score > 0 ? '+' : '') + score.toFixed(2)}</span></h3>
      <div class="mk-meter" title="-1 to +1">${px != null ? `<b style="left:${px}%" title="Last week ${prev.toFixed(2)}"></b>` : ''}<i style="left:${x}%"></i></div>
      <div class="mk-scale"><span>${scaleL}</span><span><b>${esc(bucket || '')}</b></span><span>${scaleR}</span></div>
      <div class="mk-votes">${Object.entries(votes).map(([k, v]) => v == null ? `<span class="chip out" title="No recent data">${esc(labels[k] || k)}</span>` : `<button type="button" class="chip ${v ? 'v-on' : 'v-off'}" data-chart="SIG_${esc(k)}" title="${v ? 'Votes ' + (inv ? 'cyclicals' : 'benign') : 'Votes ' + (inv ? 'defensives' : 'cautionary')}${inv && inv[k] ? ' (contrarian)' : ''}" style="border:0;cursor:pointer">${v ? '▲' : '▼'} ${esc(labels[k] || k)}</button>`).join('')}</div>
      <p class="mk-note">${histLine}</p></div>`;
  }

  function evidence(St) {
    const src = MK.ev === 'market' ? St.market : St.rotation; const lab = {}; (MK.sum.signals || []).forEach(s => lab[s.key] = s.label);
    let rows = Object.entries(src).map(([k, m]) => ({ k, ...m }));
    rows = sortRows(rows, MK.evSort, (r, k) => k === 'k' ? (lab[r.k] || r.k) : k === 'ddr' ? (r.bear_dd != null ? r.bear_dd - (r.bull_dd || 0) : null) : k === 'aic' ? Math.abs(r.ic) : r[k]);
    const mk = MK.ev === 'market';
    return `<div class="tbl-wrap"><table class="mk-t" id="mk-ev"><thead><tr>${th('Signal', 'k', MK.evSort)}${th('From', 'start', MK.evSort, 'n')}${th('Months', 'n', MK.evSort, 'n')}${th('Benign share', 'bull_share', MK.evSort, 'n')}${th(mk ? 'Avg next 12m, benign' : 'Cyc − def next 6m, benign', 'bull_avg', MK.evSort, 'n')}${th('…cautionary', 'bear_avg', MK.evSort, 'n')}${th('Spread', 'spread', MK.evSort, 'n')}${th('t (overlap-adj.)', 't', MK.evSort, 'n')}${th('Rank IC', 'aic', MK.evSort, 'n')}${mk ? th('15% DD odds benign / cautionary', 'ddr', MK.evSort, 'n') : ''}</tr></thead>
      <tbody>${rows.map(r => `<tr data-sig="${esc(r.k)}"><td class="sig">${esc(lab[r.k] || r.k)}</td><td class="n">${esc(r.start)}</td><td class="n">${r.n}</td><td class="n">${Math.round(r.bull_share * 100)}%</td><td class="n">${pc(r.bull_avg)}</td><td class="n">${pc(r.bear_avg)}</td><td class="n ${r.spread > 0 ? 'up' : 'dn'}">${pc(r.spread)}</td><td class="n">${r.t == null ? '—' : r.t.toFixed(1)}</td><td class="n">${r.ic.toFixed(2)}</td>${mk ? `<td class="n">${r.bull_dd == null ? '—' : Math.round(r.bull_dd * 100) + '% / ' + Math.round(r.bear_dd * 100) + '%'}</td>` : ''}</tr>`).join('')}</tbody></table></div>`;
  }

  function etfTable(T) {
    const SECT = new Set(['XLY', 'XLI', 'XLB', 'XLF', 'XLE', 'XLP', 'XLU', 'XLV', 'XLK']);
    let rows = (T.etfs || []).filter(r => MK.etf === 'all' || (MK.etf === 'sect' ? SECT.has(r.t) : !SECT.has(r.t)));
    rows = sortRows(rows, MK.etfSort, (r, k) => r[k]);
    const c = v => v == null ? '' : v >= 0 ? 'up' : 'dn';
    return `<div class="mk-ctl"><div class="seg" id="mk-etf">${[['sect', 'Sectors'], ['other', 'Index & cross-asset'], ['all', 'All']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${MK.etf === v}">${l}</button>`).join('')}</div><span class="muted">FactSet daily closes through ${fmtD(T.asof)}</span></div>
      <div class="tbl-wrap"><table class="mk-t" id="mk-etft"><thead><tr>${th('ETF', 't', MK.etfSort)}${th('Side', 'cyc', MK.etfSort)}${th('1w', 'r1w', MK.etfSort, 'n')}${th('1m', 'r1m', MK.etfSort, 'n')}${th('3m', 'r3m', MK.etfSort, 'n')}${th('6m', 'r6m', MK.etfSort, 'n')}${th('vs 50d', 'd50', MK.etfSort, 'n')}${th('vs 200d', 'd200', MK.etfSort, 'n')}${th('Off 52w high', 'off_hi', MK.etfSort, 'n')}</tr></thead>
      <tbody>${rows.map(r => `<tr data-px="PX_${esc(r.t)}"><td><span class="tk-chip">${esc(r.t)}</span> ${esc(r.name)}</td><td>${r.cyc === 'cyc' ? '<span class="chip">Cyclical</span>' : r.cyc === 'def' ? '<span class="chip">Defensive</span>' : ''}</td>
        ${['r1w', 'r1m', 'r3m', 'r6m', 'd50', 'd200', 'off_hi'].map(k => `<td class="n ${c(r[k])}">${pc(r[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  }

  // -------------------------------------------------------------- paint
  function picker() {
    const opts = {}; Object.values(MK.ser).forEach(d => d && d.s && Object.entries(d.s).forEach(([id, s]) => { (opts[s.g] = opts[s.g] || []).push([id, id.startsWith('SIG_') ? 'Signal: ' + s.n : s.n]); }));
    const o = (sel, none) => (none ? `<option value="">${none}</option>` : '') + Object.keys(opts).sort().map(g => `<optgroup label="${esc(g)}">${opts[g].sort((a, b) => a[1].localeCompare(b[1])).map(([id, n]) => `<option value="${esc(id)}" ${id === sel ? 'selected' : ''}>${esc(n)}</option>`).join('')}</optgroup>`).join('');
    return { a: o(MK.sel), b: o(MK.cmp, 'Compare with… (none)') };
  }
  function explorer() {
    const haveSer = Object.keys(MK.ser).length;
    if (!haveSer) return `<section class="panel" id="mk-ex"><h2>Chart explorer</h2><p class="mk-note">${MK.serErr ? esc(MK.serErr) : 'Loading history…'}</p></section>`;
    const A0 = getS(MK.sel) || getS('SIG_curve'); if (!A0) return '';
    const key = A0.id.startsWith('SIG_') ? A0.id.slice(4) : '';
    const A = transform(A0, MK.tf), B = MK.cmp ? transform(getS(MK.cmp), MK.tf) : null, SP = MK.spx && !B ? getS('SPX') : null;
    MK._nA = A.n; MK._nB = B ? B.n : '';
    const p = picker(); const reg = (MK.sum.registry || {})[A0.id];
    const sigInfo = key ? (MK.sum.signals || []).find(s => s.key === key) : null;
    return `<section class="panel" id="mk-ex"><div class="panel-h"><h2>${esc(A.n)} <span class="muted" style="font-weight:500">${esc(A.u || '')}</span></h2>
      <div class="seg" id="mk-rng">${[[60, '5Y'], [120, '10Y'], [240, '20Y'], [99999, 'All']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${MK.range === v}">${l}</button>`).join('')}</div></div>
      <div class="mk-ctl"><select id="mk-sel" aria-label="Series">${p.a}</select><select id="mk-cmp" class="mk-cmp" aria-label="Compare series">${p.b}</select>
        <div class="seg" id="mk-tf">${[['lvl', 'Level'], ['chg', '12m change'], ['yoy', '% y/y'], ['z', 'Z-score']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${MK.tf === v}">${l}</button>`).join('')}</div>
        <label><input type="checkbox" id="mk-spx" ${MK.spx ? 'checked' : ''} ${B ? 'disabled' : ''}> S&amp;P 500 (log, right)</label></div>
      <div class="mk-key"><span><i style="background:var(--accent)"></i>${esc(A.n)}</span>${B ? `<span><i style="background:var(--mv2,#eb6834)"></i>${esc(B.n)} (right)</span>` : SP ? `<span><i style="background:var(--muted)"></i>S&amp;P 500 (right, log)</span>` : ''}${key && MK.tf === 'lvl' && THR[key] != null ? `<span><i style="background:var(--warn)"></i>Rule threshold ${fv(key, THR[key])}</span><span><i style="background:var(--neg);opacity:.25;height:8px"></i>Cautionary state</span>` : ''}</div>
      ${chart(A, B, SP, key, 960, 340)}
      ${sigInfo ? `<p class="mk-note"><b>${esc(sigInfo.label)}:</b> ${esc(sigInfo.desc)}</p>` : ''}${reg ? `<p class="mk-note">Source: ${esc(reg.src)}</p>` : ''}</section>`;
  }

  function paint() {
    const host = document.getElementById('v-markets'); if (!host) return; ensureCss();
    const head = `<section class="panel" style="gap:10px"><span class="eyebrow">Markets · macro &amp; technicals</span><h1>Market direction and sector rotation</h1>`;
    if (!MK.sum) { host.innerHTML = head + `<p class="lede">${esc(MK.err || 'Loading the weekly markets read…')}</p></section>`; return; }
    const S = MK.sum, St = MK.study || { market: {}, rotation: {}, composite: S.composite };
    const lab = {}; S.signals.forEach(s => lab[s.key] = s.label);
    const mb = {}; (S.composite.market_buckets_fwd12 || []).forEach(b => mb[b.bucket] = b); const dd = {}; (S.composite.market_buckets_dd || []).forEach(b => dd[b.bucket] = b.dd_freq);
    const rb = {}; (S.composite.rotation_buckets_fwd6 || []).forEach(b => rb[b.bucket] = b);
    const inv = {}; (S.composite.rotation_keys || []).forEach(([k, i]) => inv[k] = i);
    const mLine = ['Bearish', 'Neutral', 'Bullish'].filter(b => mb[b]).map(b => `${b}: ${pc(mb[b].avg)} avg next 12m, ${Math.round((dd[b] || 0) * 100)}% hit a 15% drawdown`).join(' · ');
    const rLine = ['Bearish', 'Neutral', 'Bullish'].filter(b => rb[b]).map(b => `${b}: cyc − def ${pc(rb[b].avg)} next 6m (n=${rb[b].n})`).join(' · ');
    const calls = (S.callouts || []).map(c => `<div class="li" ${c.keys && c.keys.length === 1 ? `data-keys="${esc(c.keys[0])}"` : ''}><span class="stripe ${c.sev === 'pos' ? 'pos' : c.sev === 'neg' ? 'neg' : 'warn'}"></span><div class="body"><span class="mk-kind">${esc(c.kind)}</span><b>${esc(c.title)}</b>${c.body ? `<div>${esc(c.body)}</div>` : ''}</div></div>`).join('');
    const T = S.technicals || {}; const Br = (S.breadth && S.breadth.u) || {};
    const brRows = Object.entries(Br).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="n">${fmtD(v.ad_peak)}</td><td class="n">${fmtD(v.ix_peak)}</td><td class="n">${v.lead > 0 ? v.lead + 'd' : '—'}</td><td class="n ${v.ix_off < -3 ? 'dn' : ''}">${pc(v.ix_off)}</td><td class="n ${v.r10 >= 1 ? 'up' : 'dn'}">${v.r10 == null ? '—' : v.r10.toFixed(2) + 'x'}</td><td>${v.div ? '<span class="st bear">Divergence</span>' : '<span class="st bull">OK</span>'}</td></tr>`).join('');
    const gaps = Object.entries(S.registry || {}).filter(([id, r]) => /history only|refresh needed/.test(r.src)).map(([id, r]) => r.n);
    const regRows = Object.entries(S.registry || {}).filter(([id, r]) => !id.startsWith('SIG_') && (MK.src === 'All' || r.g === MK.src));
    host.innerHTML = head + `<p class="lede" style="color:var(--ink);font-size:15px"><b>${esc(S.headline)}</b></p>
        <p class="mk-note">Weekly read as of ${fmtD(S.asof)} · macro data through ${(() => { const m = S.signals.filter(x => !x.stale && x.group !== 'Trend & breadth').map(x => x.date).sort().pop(); return m ? fmtMonth(m) : '—'; })()} · prices through ${fmtD((S.technicals || {}).asof)}${S.prev && S.prev.asof ? ' · previous read ' + fmtD(S.prev.asof) : ''}. History: Bloomberg 1970–2018, FactSet after.</p></section>
      <div class="mk-gauges">
        ${gauge('Market risk regime', S.mkt_score, S.mkt_bucket, S.mkt_votes, lab, null, mLine, 'Bearish', 'Bullish', S.prev && S.prev.mkt_score)}
        ${gauge('Cyclicals vs defensives', S.rot_score, S.rot_bucket === 'Bullish' ? 'Lean cyclicals' : S.rot_bucket === 'Bearish' ? 'Lean defensives' : 'Neutral', S.rot_votes, lab, inv, rLine + ' · in-sample, 2006–2026', 'Defensives', 'Cyclicals', S.prev && S.prev.rot_score)}
      </div>
      <section class="panel mk-call"><div class="panel-h"><h2>This week's call-outs</h2><span class="muted">Click one to chart it</span></div><div class="list">${calls}</div></section>
      ${scorecard(S)}
      ${explorer()}
      <div class="mk-grid2">
        <section class="panel"><div class="panel-h"><h2>Sector rotation</h2><span class="muted">Cyclicals (XLY XLI XLB XLF XLE) ÷ defensives (XLP XLU XLV), equal weight</span></div>
          <div class="mk-key"><span><i style="background:var(--accent)"></i>Daily ratio</span><span><i style="background:var(--muted)"></i>50-day average</span></div>
          ${relChart(T.rel_d, 620, 220)}
          <p class="mk-note">${T.rel_3m == null ? '' : `3 months: ${pc(T.rel_3m)} · vs 50-day ${pc(T.rel_vs50)}${T.rel_vs200 == null ? '' : ' · vs 200-day ' + pc(T.rel_vs200)}. ${T.sectors_above_200} of ${T.sectors_n} sector SPDRs are above their 200-day average.`} <a href="#markets" data-chart="CYC_DEF_REL">Long-run ratio since 2006 →</a></p></section>
        <section class="panel"><div class="panel-h"><h2>Breadth by market</h2><a href="#technicals">Technicals tab →</a></div>
          <div class="tbl-wrap"><table class="mk-t"><thead><tr><th>Market</th><th class="n">A/D peak</th><th class="n">Index peak</th><th class="n">A/D led by</th><th class="n">Index vs peak</th><th class="n">10d A/D</th><th>Read</th></tr></thead><tbody>${brRows || '<tr><td colspan="7" class="muted">No breadth data</td></tr>'}</tbody></table></div>
          <p class="mk-note">From the Technicals tab's advance/decline data (built ${esc(S.breadth && S.breadth.built || '—')}).</p></section>
      </div>
      <section class="panel"><div class="panel-h"><h2>Sector and cross-asset tape</h2><span class="muted">Click a row to chart its monthly history</span></div>${etfTable(T)}</section>
      <section class="panel" id="mk-evid"><div class="panel-h"><h2>What has predicted what</h2><div class="seg" id="mk-evs">${[['market', 'Market direction (S&P, next 12m)'], ['rotation', 'Cyclicals vs defensives (next 6m)']].map(([v, l]) => `<button type="button" data-v="${v}" aria-pressed="${MK.ev === v}">${l}</button>`).join('')}</div></div>
        ${MK.study ? evidence(St) : '<p class="mk-note">Loading…</p>'}
        <div class="method"><ul>
          <li><b>Read it as a risk gauge.</b> Few macro signals forecast the size of the next year's return; their t-statistics, adjusted for overlapping windows, are mostly below 2. What they do sort is drawdown risk. Since 1970, months with a cautionary trend, yield curve, claims, credit, permits or inflation-direction signal were followed by a 15%+ drawdown two to three times as often.</li>
          <li><b>Growth data works contrarian for the index.</b> ISM, manufacturing output and payrolls have negative rank ICs: the best forward returns came when they were weak (an ISM below 50 averaged ${pc((St.market.ism || {}).bear_avg)} next 12m vs ${pc((St.market.ism || {}).bull_avg)} above 50). Valuation (forward P/E, IC ${((St.market.fwdpe || {}).ic || 0).toFixed(2)}) and inflation level are the best return predictors.</li>
          <li><b>Rotation, 2006–2026 only (about 40 independent 6-month windows).</b> Falling core inflation (t ${((St.rotation.cpi_chg || {}).t || 0).toFixed(1)}) and rising ISM/Empire favoured cyclicals. Elevated claims and a weak ISM also preceded cyclical outperformance: cyclicals tend to lead out of a slowdown. The rotation composite is fitted on this same sample, so treat its bucket returns as in-sample.</li>
          <li>Composites: market = ${esc((S.composite.market_keys || []).map(k => lab[k] || k).join(', '))}. Rotation = ${esc((S.composite.rotation_keys || []).map(([k, i]) => (lab[k] || k) + (i ? ' (contrarian)' : '')).join(', '))}. Each signal votes +1/−1; a signal whose data is more than 3 months old does not vote.</li>
          ${S.ism_proxy ? `<li>ISM after July 2018 is a proxy: a regression of ISM on the Empire State, Dallas and Kansas City Fed surveys (R² ${S.ism_proxy.r2.toFixed(2)}, ${S.ism_proxy.n} months). It will be replaced once the Bloomberg sheet is extended.</li>` : ''}
        </ul></div></section>
      <section class="panel"><div class="panel-h"><h2>Sources &amp; gaps</h2><label class="muted" style="font-size:12px">Group <select id="mk-src">${['All', ...new Set(Object.values(S.registry || {}).map(r => r.g))].map(g => `<option ${g === MK.src ? 'selected' : ''}>${esc(g)}</option>`).join('')}</select></label></div>
        <p class="mk-note"><b>Stale until the Bloomberg sheet is extended past July 2018:</b> ${esc(gaps.join(', ')) || 'none'}. Add these tickers to the sheet to close the remaining gaps: NAPMPMI Index, NAPMNEWO Index, CONCCONF Index, LEI TOTL Index, SPX Index BEST_PE_RATIO, CCMP Index BEST_PE_RATIO, LF98OAS Index (HY spread), MOODCBAA Index, MPMIEZMA Index, CPMINDX Index, NYA ADV/DECL (NYSE breadth), PCUSEQTR Index (put/call), AAIIBULL Index.</p>
        <div class="tbl-wrap" style="max-height:420px"><table class="mk-t"><thead><tr><th>Series</th><th>Group</th><th>Units</th><th>Source</th></tr></thead><tbody>${regRows.map(([id, r]) => `<tr data-px="${esc(id)}"><td>${esc(r.n)}</td><td class="muted">${esc(r.g)}</td><td class="muted">${esc(r.u)}</td><td class="sub" style="white-space:normal">${esc(r.src)}</td></tr>`).join('')}</tbody></table></div>
        <p class="mk-note">Stored in Supabase (macro_series, macro_observations, market_signal_snapshots, market_regime_snapshots) and refreshed weekly by the markets-weekly job.</p></section>`;
    wire(host);
  }
  function go(id) { MK.sel = id; MK.cmp = ''; if (MK.tf !== 'lvl' && id.startsWith('SIG_')) MK.tf = 'lvl'; save(); paint(); const ex = document.getElementById('mk-ex'); if (ex) ex.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  function wire(host) {
    const $ = s => host.querySelector(s);
    const q = $('#mk-q'); if (q) q.oninput = () => { MK.q = q.value; const pos = q.selectionStart; paint(); const n = document.getElementById('mk-q'); n.focus(); n.setSelectionRange(pos, pos); };
    const g = $('#mk-grp'); if (g) g.onchange = () => { MK.grp = g.value; save(); paint(); };
    host.querySelectorAll('#mk-st button').forEach(b => b.onclick = () => { MK.st = b.dataset.v; paint(); });
    const st = $('#mk-stale'); if (st) st.onchange = () => { MK.stale = st.checked; save(); paint(); };
    host.querySelectorAll('#mk-tbl thead th[data-k]').forEach(t => t.onclick = () => { MK.sort = [t.dataset.k, MK.sort[0] === t.dataset.k ? -MK.sort[1] : (t.dataset.k === 'grp' || t.dataset.k === 'sig' ? 1 : -1)]; paint(); });
    host.querySelectorAll('#mk-ev thead th[data-k]').forEach(t => t.onclick = () => { MK.evSort = [t.dataset.k, MK.evSort[0] === t.dataset.k ? -MK.evSort[1] : -1]; paint(); });
    host.querySelectorAll('#mk-etft thead th[data-k]').forEach(t => t.onclick = () => { MK.etfSort = [t.dataset.k, MK.etfSort[0] === t.dataset.k ? -MK.etfSort[1] : -1]; paint(); });
    host.querySelectorAll('tr[data-sig]').forEach(r => { const f = () => go('SIG_' + r.dataset.sig); r.onclick = f; r.onkeydown = e => { if (e.key === 'Enter') f(); }; });
    host.querySelectorAll('tr[data-px]').forEach(r => r.onclick = () => { if (getS(r.dataset.px)) go(r.dataset.px); });
    host.querySelectorAll('[data-chart]').forEach(b => b.onclick = e => { e.preventDefault(); go(b.dataset.chart); });
    host.querySelectorAll('.mk-call .li[data-keys]').forEach(l => l.onclick = () => go('SIG_' + l.dataset.keys));
    host.querySelectorAll('#mk-rng button').forEach(b => b.onclick = () => { MK.range = +b.dataset.v; save(); paint(); });
    host.querySelectorAll('#mk-tf button').forEach(b => b.onclick = () => { MK.tf = b.dataset.v; save(); paint(); });
    host.querySelectorAll('#mk-evs button').forEach(b => b.onclick = () => { MK.ev = b.dataset.v; MK.evSort = ['spread', -1]; save(); paint(); });
    host.querySelectorAll('#mk-etf button').forEach(b => b.onclick = () => { MK.etf = b.dataset.v; save(); paint(); });
    const s1 = $('#mk-sel'); if (s1) s1.onchange = () => { MK.sel = s1.value; save(); paint(); };
    const s2 = $('#mk-cmp'); if (s2) s2.onchange = () => { MK.cmp = s2.value; paint(); };
    const sx = $('#mk-spx'); if (sx) sx.onchange = () => { MK.spx = sx.checked; save(); paint(); };
    const sr = $('#mk-src'); if (sr) sr.onchange = () => { MK.src = sr.value; paint(); };
    wireHover(host);
  }
  function load() {
    if (MK.loaded) return; MK.loaded = true;
    const to = setTimeout(() => { if (!MK.sum) { MK.err = 'The markets data did not load in this view.'; paint(); } }, 10000);
    (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => {
      if (!db) { clearTimeout(to); MK.err = 'The markets data is kept in this page’s database; open the page on claude.ai to see it.'; paint(); return; }
      const c = db.collection('markets');
      c.doc('summary').get().then(sn => { clearTimeout(to); if (sn && sn.exists) { MK.sum = JSON.parse(JSON.stringify(sn.data())); } else MK.err = 'No markets data is stored yet.'; paint(); }).catch(() => { clearTimeout(to); MK.err = 'The markets data could not be read.'; paint(); });
      c.doc('study').get().then(sn => { if (sn && sn.exists) { MK.study = JSON.parse(JSON.stringify(sn.data())); paint(); } }).catch(() => {});
      Promise.all(['series_sig', 'series_macro', 'series_px'].map(id => c.doc(id).get().then(sn => [id, sn && sn.exists ? JSON.parse(JSON.stringify(sn.data())) : null]).catch(() => [id, null])))
        .then(arr => { arr.forEach(([id, d]) => { if (d) MK.ser[id] = d; }); if (!Object.keys(MK.ser).length) MK.serErr = 'History did not load.'; paint(); });
    }).catch(() => { clearTimeout(to); MK.err = 'The markets data could not be read.'; paint(); });
  }
  window.__renderMarkets = () => { paint(); load(); };
})();
