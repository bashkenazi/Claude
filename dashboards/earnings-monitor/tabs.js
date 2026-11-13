(function () {
  const D = JSON.parse(document.getElementById('data').textContent);
  const SRC = D.sources || {};
  const SIG = D.signals || {};
  const CMP = D.comps || {}; let DLY = D.daily || {};
  // ---- global view options (Show N / Window / As of), shared by every tab; remembered per viewer ----
  if (!window.__G) { let g = {}; try { g = JSON.parse(localStorage.getItem('td-view') || '{}') || {}; } catch (e) {} window.__G = { n: g.n || null, days: g.days || null }; }
  const G = window.__G;
  const lim = (xs, def) => { const n = G.n || def; return n ? arr(xs).slice(0, n) : arr(xs); };
  const winDays = def => G.days ? (G.days >= 100000 ? Infinity : G.days) : def;
  const inWin = (iso, def) => { const w = winDays(def); if (w == null || w === Infinity) return true; const a = ageDays(iso); return a == null || a <= w; };
  // ---- valuation lookup from the Master comps file ----
  const normT = t => String(t || '').toUpperCase().replace(/\s+(US|UW|UN|UQ|EQUITY)$/,'').replace(/\s+JT$/,' JP').replace(/\s+TW$/,' TT').trim();
  const CROWS = {}; Object.entries(CMP.rows || {}).forEach(([k, v]) => { CROWS[normT(k)] = v; });
  const valOf = t => CROWS[normT(t)] || CROWS[normT(String(t).split(' ')[0])] || null;
  const fx = (v, suf) => v == null || v === '' || isNaN(+v) ? null : (+v).toFixed(1) + (suf || '');
  function valLine(t, compact) {
    const v = valOf(t); if (!v) return '';
    const grp = (CMP.groups || {})[arr(v.groups)[0]] || {};
    const rel = (x, m) => x == null || !m ? '' : (+x < 0.75 * m ? ' <span class="c-pos" title="cheap vs group median">▼</span>' : +x > 1.33 * m ? ' <span class="c-neg" title="rich vs group median">▲</span>' : '');
    const bits = [];
    if (fx(v.pe_cy27)) bits.push(`P/E27 ${fx(v.pe_cy27, 'x')}${rel(v.pe_cy27, grp.median_pe_cy27)}`);
    if (fx(v.peg_cy27)) bits.push(`PEG ${fx(v.peg_cy27)}${rel(v.peg_cy27, grp.median_peg_cy27)}`);
    if (fx(v.ev_sales_cy27)) bits.push(`EV/S ${fx(v.ev_sales_cy27, 'x')}`);
    if (!compact && fx(v.rev_growth_cy27)) bits.push(`Rev27 ${fx(v.rev_growth_cy27, '%')}`);
    if (fx(v.pct_from_52w_high)) bits.push(`${fx(v.pct_from_52w_high, '%')} vs 52w hi`);
    if (!compact && fx(v.px_30d)) bits.push(`30D ${fx(v.px_30d, '%')}`);
    if (!compact && fx(v.eps_rev_4w_cy27)) bits.push(`EPS27 rev 4w ${fx(v.eps_rev_4w_cy27, '%')}`);
    if (!bits.length) return '';
    return `<div class="valc${compact ? ' cpt' : ''}" title="Master comps ${esc(CMP.as_of || '')}${grp.n ? ' · group ' + esc(arr(v.groups)[0]) + ' median P/E27 ' + fx(grp.median_pe_cy27, 'x') : ''}">${v.cyclical ? '<span title="cyclical: P/E looks cheapest at peak earnings">⟳</span> ' : ''}${bits.join(' · ')}</div>`;
  }
  window.__valLine = valLine;
  const TODAY = D.today || {}, DP = D.datapoints || {}, SC = D.screens || {}, ID = D.ideas || {}, PR = D.prep || {};
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const arr = x => Array.isArray(x) ? x : [];
  const built = D.built_at ? new Date(D.built_at) : new Date();
  const dayMs = 864e5;
  const ageDays = iso => iso ? Math.floor((built - new Date(String(iso).slice(0, 10) + 'T12:00:00')) / dayMs) : null;
  const fmtD = iso => { if (!iso) return ''; const d = new Date(String(iso).slice(0, 10) + 'T12:00:00'); return isNaN(d) ? esc(iso) : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }); };
  const fmtDW = iso => { const d = new Date(String(iso).slice(0, 10) + 'T12:00:00'); return isNaN(d) ? esc(iso) : d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }); };
  const link = (url, label) => url ? `<a class="ext" href="${esc(url)}" target="_blank" rel="noopener">${label || 'Open'} ↗</a>` : '';
  // ---- company names for numeric tickers (2330 TT, 285A JT, 000660 KS…): shown next to the ticker everywhere ----
  const nk = t => String(t || '').toUpperCase().replace(/\s+EQUITY$/, '').replace(/\s+JT$/, ' JP').replace(/\s+(US|UW|UN|UQ)$/, '').replace(/\s+/g, ' ').trim();
  const NAMES = new Map();
  const nmClean = n => String(n || '').replace(/\s*\([^)]*\)\s*$/, '').trim();
  const putName = (t, n, strong) => { const k = nk(t), v = nmClean(n); if (!k || !v || v.toUpperCase() === k) return; if (strong || !NAMES.has(k)) NAMES.set(k, v); };
  arr((D.universe || {}).names).forEach(x => putName(x.t, x.n));                      // Bloomberg short names (fallback)
  Object.values((D.comps || {}).rows || {}).forEach(x => putName(x.bbg_ticker, x.name));
  arr((D.daily || {}).moves).forEach(x => putName(x.t, x.n));
  arr((D.dp_index || {}).meta).forEach(x => putName(x.t, x.n, true));
  arr((D.pipeline || {}).items).forEach(x => putName(x.ticker, x.company, true));
  arr((D.stocks || {}).companies).forEach(x => { putName(x.t, x.name, true); putName(x.bbg, x.name, true); });
  const isNumT = t => /^\d/.test(String(t || '').trim());
  const nameOf = t => NAMES.get(nk(t)) || NAMES.get(nk(t).split(' ')[0]) || '';
  const tk = (t, cls) => { if (!t) return ''; const nm = isNumT(t) ? nameOf(t) : '';
    return `<span class="tk-chip${cls ? ' ' + cls : ''}"${nm ? ` data-nm="${esc(nm)}" title="${esc(nm)}"` : ''}>${esc(t)}${nm ? `<span class="tk-nm"> · ${esc(nm)}</span>` : ''}</span>`; };
  // drop the name inside the chip where the same name is already printed right after it
  const dedupeNames = root => (root || document).querySelectorAll('.tk-chip[data-nm]:not([data-dd])').forEach(c => {
    c.dataset.dd = '1'; let n = c.nextSibling, txt = '';
    while (n && txt.trim().length < 4) { txt += (n.textContent || ''); n = n.nextSibling; }
    const a = txt.trim().toLowerCase().replace(/[^a-z0-9]/g, ''), b = c.dataset.nm.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (a && b && (a.startsWith(b.slice(0, 5)) || b.startsWith(a.slice(0, 5)))) { const s2 = c.querySelector('.tk-nm'); if (s2) s2.remove(); } });
  new MutationObserver(() => dedupeNames()).observe(document.documentElement, { childList: true, subtree: true });
  window.__tkName = t => isNumT(t) ? nameOf(t) : '';
  const signOf = v => { const s = String(v == null ? '' : v).trim().toLowerCase(); if (/^\+|^pos|bull|up\b|beat|raise|improv|accel/.test(s)) return 1; if (/^[-−–]|^neg|bear|down\b|miss|cut|deteri|decel/.test(s)) return -1; return 0; };
  const numCls = v => { const g = signOf(v); return g > 0 ? 'up' : g < 0 ? 'dn' : ''; };
  const SKILL_NAME = {
    'morning': 'Morning', 'research-folder-digest': 'Research folder', 'tech-email-digest-new': 'Tech email', 'semianalysis-digest': 'SemiAnalysis',
    'analyst-folder-extractor': 'Analyst folders', 'alphasense-digest': 'AlphaSense', 'sellside-folder-digest': 'Sell-side PDFs',
    'consensus-revisions': 'Consensus revisions', 'comps-screen': 'Comps screen', 'idea-generator': 'Idea generator', 'thesis-builder': 'Thesis builder',
    'industry-cycle': 'Industry cycle', 'operating-comps': 'Operating comps', 'management-prep': 'Management prep', 'analyst-day': 'Analyst day',
    'print-tables': 'Print tables', 'quarterly-review': 'Quarterly review', 'earnings-preview': 'Earnings preview / review', 'earnings-recap': 'Earnings recap',
    'datapoint-filter': 'Supabase loads (Datapoint Filter)',
    'universe-sweep': 'Universe sweep', 'ai-build-sweep': 'AI build & financing', 'x-scan': 'X list monitor', 'openclaw-datapoints': 'OpenClaw datapoints'
  };
  const sk = s => SKILL_NAME[s] || s;
  const fresh = a => a == null ? '' : a <= 2 ? 'fresh' : a <= 7 ? 'aging' : 'stale';
  const head = (eyebrow, title, lede) => `<section class="panel vh"><span class="eyebrow">${eyebrow}</span><h1>${title}</h1>${lede ? `<p class="lede">${lede}</p>` : ''}</section>`;
  const none = msg => `<p class="empty-panel">${msg}</p>`;
  // one sentence: the first sentence of a reason, capped at ~30 words; the full text sits in the hover title
  const oneSent = t => { let all = String(t || '').replace(/\s+/g, ' ').trim(); if (!all) return '';
    /* daily-why-blank v1 */ if (/^(moved with|no catalyst|in line with|traded with|tracked|a move with|move with|broad(er)? market|market[- ]wide)/i.test(all) || /broader market/i.test(all)) return '';
    const mw = all.match(/^Moved with ([^:(]+?)\s*(?:\([^)]*\))?\s*:\s*(.+)$/i); if (mw) { const d = mw[2].split(/;|\s\(|,\s(?=[a-z])/)[0].replace(/[\s.]+$/, ''); return `Moved with ${mw[1].trim()}: ${d}.`; } let x = all.split(/(?<=[.!?])\s+(?=[A-Z("'$])/)[0]; const w = x.split(' '); if (w.length > 30) x = w.slice(0, 30).join(' ').replace(/[\s,;:–—-]+$/, '') + '…'; return x; };
  const whyHtml = t => { const one = oneSent(t); return one ? `<span class="why1" title="${esc(t)}">${attr(one)}</span>` : ''; };
  const attr = t => esc(t).replace(/\s*\[([^\]]{2,90})\]\s*$/, ' <span class="attr">$1</span>');
  const srcList = x => arr(x && x.sources).concat(x && x.source ? [x.source] : []).filter(Boolean);
  const srcLine = (x, label) => { const l = srcList(x); return l.length ? `<div class="srcl"><span>${label || 'Source'}</span>${l.map(esc).join(' · ')}</div>` : ''; };
  window.__srcLine = srcLine; window.__attr = attr;

  // ================= TODAY =================
  function marketPanel() {
    const M = TODAY.market; if (!M) return '';
    if (arr(M.drivers).length || arr(M.under).length) {
      const L = xs => `<ul class="b">${arr(xs).map(x => `<li>${attr(x)}</li>`).join('')}</ul>`;
      return `<section class="panel mk"><div class="panel-h"><div><span class="eyebrow">Market · ${esc(String(M.as_of || '').split(';')[0])}</span><h2 style="margin-top:4px">${esc(M.headline || '')}</h2></div><a href="#daily">Daily moves →</a></div>
        <div class="grid3 mk-short"><div><h3>Why it's moving</h3>${L(M.drivers)}</div><div><h3>Under the surface</h3>${L(M.under)}</div><div><h3>What to watch</h3>${L(M.watch)}</div></div>
        ${arr(M.sources).length ? `<div class="srcl"><span>Sources</span>${arr(M.sources).map(x => x.url ? link(x.url, x.label) : esc(x.label)).join(' · ')}</div>` : ''}</section>`;
    }
    const p1 = v => v == null ? '' : (v > 0 ? '+' : '') + (+v).toFixed(1) + '%';
    // short form: first sentence, capped at ~22 words; full text stays one click away
    const brief = (t, n) => {
      const all = String(t || '').replace(/\s*\([^)]*\)/g, '').replace(/\s+/g, ' ').trim();
      let x = all.split(/(?<=[.;:])\s+/)[0];
      if (x.split(' ').length < 8) x = all;                       // a too-short lead sentence keeps going
      const w = x.split(' '); x = w.length > n ? w.slice(0, n).join(' ') : x;
      x = x.replace(/[\s,;:–—-]+$/, '');
      return x + (x.length < all.replace(/[.;:\s]+$/, '').length ? '…' : ''); };
    const row = x => `<div class="mk-row"><span class="mk-g">${esc(x.group)}</span><span class="mono ${+x.median_1d >= 0 ? 'c-pos' : 'c-neg'}">${p1(x.median_1d)}</span><span class="mk-w">${esc(brief(x.why, 12))}</span></div>`;
    const ul = (xs, n) => `<ul class="b">${arr(xs).slice(0, n).map(x => `<li>${esc(brief(x, 22))}</li>`).join('')}</ul>`;
    const full = `<details class="mk-more"><summary>Full commentary</summary><div class="grid2"><div><h3>Market</h3><ul class="b">${arr(M.market).map(x => `<li>${attr(x)}</li>`).join('')}</ul></div><div><h3>Tech</h3><ul class="b">${arr(M.tech).map(x => `<li>${attr(x)}</li>`).join('')}</ul></div></div>
      <div class="grid2"><div><h3 class="c-pos">Leading</h3>${arr(M.leaders).map(x => `<div class="mk-row"><span class="mk-g">${esc(x.group)}</span><span class="mono ${+x.median_1d >= 0 ? 'c-pos' : 'c-neg'}">${p1(x.median_1d)}</span><span class="mk-w">${attr(x.why || '')}</span></div>`).join('')}</div><div><h3 class="c-neg">Lagging</h3>${arr(M.laggards).map(x => `<div class="mk-row"><span class="mk-g">${esc(x.group)}</span><span class="mono ${+x.median_1d >= 0 ? 'c-pos' : 'c-neg'}">${p1(x.median_1d)}</span><span class="mk-w">${attr(x.why || '')}</span></div>`).join('')}</div></div>
      ${arr(M.sources).length ? `<div class="srcl"><span>Sources</span>${arr(M.sources).map(x => x.url ? link(x.url, x.label) : esc(x.label)).join(' · ')}</div>` : ''}</details>`;
    return `<section class="panel mk"><div class="panel-h"><div><span class="eyebrow">Market · ${esc(String(M.as_of || '').split(';')[0])}</span><h2 style="margin-top:4px">${esc(brief(M.headline, 24))}</h2></div><a href="#daily">Daily moves →</a></div>
      <div class="grid2 mk-short"><div><h3>Market</h3>${ul(M.market, 3)}</div><div><h3>Tech</h3>${ul(M.tech, 3)}</div></div>
      <div class="grid2 mk-short"><div><h3 class="c-pos">Leading</h3>${arr(M.leaders).slice(0, 3).map(row).join('')}</div><div><h3 class="c-neg">Lagging</h3>${arr(M.laggards).slice(0, 3).map(row).join('')}</div></div>
      ${full}</section>`;
  }
  function renderToday() {
    const digs = arr(TODAY.digests).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)));
    const latestBySkill = new Map();
    digs.forEach(d => { if (!latestBySkill.has(d.skill)) latestBySkill.set(d.skill, d); });
    const order = ['research-folder-digest', 'tech-email-digest-new', 'semianalysis-digest', 'sellside-folder-digest', 'universe-sweep', 'ai-build-sweep', 'x-scan', 'openclaw-datapoints'].concat(['morning', 'analyst-folder-extractor', 'alphasense-digest'].filter(k => latestBySkill.has(k)));
    const strip = order.map(s => {
      const d = latestBySkill.get(s); const a = d ? ageDays(d.date) : null;
      return d ? `<a class="run" href="${esc(d.url)}" target="_blank" rel="noopener"><span class="n">${esc(sk(s))}</span><span class="d"><i class="dot ${fresh(a)}"></i>${fmtD(d.date)}${d.datapoint_count != null ? ' · ' + esc(d.datapoint_count) + ' datapoints' : ''}</span></a>`
        : `<div class="run"><span class="n">${esc(sk(s))}</span><span class="d"><i class="dot"></i>No run found</span></div>`;
    }).join('');

    // callouts from digests in the last 3 days (fallback: latest per skill)
    let pool = digs.filter(d => inWin(d.date, 3));
    if (!pool.length) pool = [...latestBySkill.values()];
    const calls = [];
    pool.forEach(d => arr(d.callouts).forEach(c => calls.push(Object.assign({ skill: d.skill, date: d.date, url: d.url }, c))));
    const kindOf = c => { /* today-sentiment v1 */ const k = String(c.kind || c.sentiment || c.type || '').toLowerCase().replace(/^(most|very|strongly)[_ -]*/, ''); return k.startsWith('pos') || k.startsWith('bull') ? 'pos' : k.startsWith('neg') || k.startsWith('bear') ? 'neg' : k.startsWith('infl') || k.startsWith('chang') ? 'inf' : 'oth'; };
    const col = (k, title) => {
      const xs = lim(calls.filter(c => kindOf(c) === k), 12);
      return `<div class="panel"><div class="panel-h"><h2>${title}</h2><span class="muted">${xs.length}</span></div>${xs.length ? `<div class="list">${xs.map(c =>
        `<div class="li"><span class="stripe ${k}"></span><div class="body">${tk(c.ticker)} ${attr(c.text)}${c.ticker ? valLine(c.ticker, true) : ''}<div class="sub">${c.source ? `<b class="srcb">${esc(c.source)}</b> · ` : ''}${esc(sk(c.skill))} · ${fmtD(c.date)}</div></div></div>`).join('')}</div>` : none('None in the latest digests.')}</div>`;
    };
    const themes = [];
    pool.forEach(d => arr(d.themes).forEach(t => themes.push(Object.assign({ skill: d.skill, date: d.date, url: d.url }, t))));

    const earn = lim(arr(window.__EARN).filter(i => inWin(i.date, 4)), 8);
    const up = lim(arr(PR.upcoming).filter(u => { const a = ageDays(u.date); return a != null && a <= 0 && a >= -winDays(7); }), 14);
    const LBL = { very_positive: 'Very positive', positive: 'Positive', mixed: 'Mixed', negative: 'Negative', very_negative: 'Very negative' };
    const tone = it => `<span class="chip s-${esc(it.tone)}">${LBL[it.tone] || esc(it.tone)}</span>`;

    document.getElementById('v-today').innerHTML =
      head('Today · ' + built.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }), 'What changed',
        'Callouts from your latest digest runs with their primary sources, the prints from the last few days and what reports next.') +
      marketPanel() +
      `<div class="runs">${strip}</div>` +
      `<div class="grid3">${col('pos', 'Most positive')}${col('neg', 'Most negative')}${col('inf', 'Inflections')}</div>` +
      (calls.some(c => kindOf(c) === 'oth') ? `<div>${col('oth', 'Other callouts')}</div>` : '') +
      `<div class="panel"><div class="panel-h"><h2>Latest themes</h2><a href="#ideas">All themes →</a></div>${themes.length ? `<div class="list">${lim(themes, 6).map(t =>
        `<div class="li"><div class="body"><b>${esc(t.theme)}</b>${arr(t.winners).length ? ' ' + arr(t.winners).slice(0, 4).map(x => tk(x, 'up')).join(' ') : ''}${arr(t.losers).length ? ' ' + arr(t.losers).slice(0, 4).map(x => tk(x, 'dn')).join(' ') : ''}<div class="sub">${srcList(t).length ? `<b class="srcb">${esc(srcList(t).slice(0, 3).join(' · '))}</b> · ` : ''}${esc(sk(t.skill))} · ${fmtD(t.date)}</div></div></div>`).join('')}</div>` : none('No themes in the latest digests.')}</div>` +
      `<div class="grid2"><div class="panel"><div class="panel-h"><h2>Recent prints</h2><a href="#earnings">All earnings →</a></div>${earn.length ? `<div class="list">${earn.map(it =>
        `<div class="li"><div class="body">${tk(it.ticker)} <b>${esc(it.company)}</b> <span class="sub">${esc(it.quarter)}</span><div>${attr(it.headline)}</div>${srcLine({ sources: arr(it.sources).slice(0, 5) })}</div><div class="side chips">${tone(it)}<span>${fmtD(it.date)}</span></div></div>`).join('')}</div>` : none('No prints in the last four days.')}</div>` +
      `<div class="panel"><div class="panel-h"><h2>Reporting this week</h2><span class="muted">Source: ${esc((arr(PR.upcoming)[0] || {}).source || 'FactSet calendar')} · <a href="#prep">Full calendar →</a></span></div>${up.length ? `<div class="list">${up.map(u =>
        `<div class="li"><div class="body">${tk(u.ticker)} <b>${esc(u.company)}</b>${u.bogeys ? `<div class="sub">${esc(u.bogeys)}</div>` : ''}</div><div class="side">${fmtDW(u.date)}${u.time ? ' · ' + esc(u.time) : ''}${u.date_status === 'projected' ? ' · projected' : ''}</div></div>`).join('')}</div>` : none('No covered names report in the next seven days.')}</div></div>`;
  }

  // ================= THEMES =================
  function renderThemes() {
    const seen = new Set(), all = [];
    arr(TODAY.digests).forEach(d => arr(d.themes).forEach(t => {
      const key = (t.theme || '') + '|' + d.date + '|' + d.skill; if (seen.has(key)) return; seen.add(key);
      all.push(Object.assign({ skill: d.skill, date: d.date, url: d.url, page: d.title }, t));
    }));
    all.sort((a, b) => String(b.date).localeCompare(String(a.date)));
    const skills = [...new Set(all.map(t => t.skill))];
    const host = document.getElementById('th-host') || document.getElementById('v-themes');
    host.innerHTML = head('Themes · from every digest', 'Themes', 'What is changing across your research flow, who benefits and who gets hurt, with the primary sources behind each theme.') +
      `<div class="panel" id="th-names"></div>` +
      `<div class="ctl" role="group" aria-label="Theme filters">
        <label for="th-q">Search <input type="search" id="th-q" placeholder="Theme, ticker or source"></label>
        <div class="seg" id="th-skill"><button type="button" data-v="" aria-pressed="true">All digests</button>${skills.map(k => `<button type="button" data-v="${esc(k)}" aria-pressed="false">${esc(sk(k))}</button>`).join('')}</div>
        <div class="seg" id="th-days"><button type="button" data-v="3" aria-pressed="false">3d</button><button type="button" data-v="7" aria-pressed="false">7d</button><button type="button" data-v="999" aria-pressed="true">All</button></div>
        <span class="count" id="th-count"></span></div>
      <div id="th-list"></div>`;
    const st = { q: '', skill: '', days: String(G.days ? Math.min(G.days, 999) : 999) };
    const seg = (id, key) => host.querySelectorAll('#' + id + ' button').forEach(b => b.addEventListener('click', () => { st[key] = b.dataset.v; host.querySelectorAll('#' + id + ' button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); draw(); }));
    seg('th-skill', 'skill'); seg('th-days', 'days');
    document.getElementById('th-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); draw(); });
    host.addEventListener('click', e => { const b = e.target.closest('[data-tk]'); if (!b) return; const q = document.getElementById('th-q'); q.value = b.dataset.tk; st.q = b.dataset.tk.toLowerCase(); draw(); });
    function draw() {
      const xs = all.filter(t => {
        if (st.skill && t.skill !== st.skill) return false;
        const a = ageDays(t.date); if (a != null && a > +st.days) return false;
        if (st.q && ![t.theme, t.whats_changing, arr(t.winners).join(' '), arr(t.losers).join(' '), srcList(t).join(' ')].join(' ').toLowerCase().includes(st.q)) return false;
        return true;
      });
      document.getElementById('th-count').textContent = xs.length + ' themes';
      // names most often named as beneficiaries / hurt
      const tally = key => { const m = new Map(); xs.forEach(t => arr(t[key]).forEach(x => m.set(x, (m.get(x) || 0) + 1))); return [...m].sort((a, b) => b[1] - a[1]).slice(0, 14); };
      const w = tally('winners'), l = tally('losers');
      const chipBtn = (x, n, cls) => `<button type="button" class="tk-chip ${cls} tkbtn" data-tk="${esc(x)}" title="Filter themes to ${esc(x)}">${esc(x)} <span class="mono">${n}</span></button>`;
      document.getElementById('th-names').innerHTML = `<div class="panel-h"><h2>Most-named companies</h2><span class="muted">across the themes shown · click a name to filter</span></div>
        <div class="wl"><span style="min-width:64px">Benefits</span>${w.length ? w.map(([x, n]) => chipBtn(x, n, 'up')).join(' ') : '<span>None named</span>'}</div>
        <div class="wl"><span style="min-width:64px">Hurt</span>${l.length ? l.map(([x, n]) => chipBtn(x, n, 'dn')).join(' ') : '<span>None named</span>'}</div>`;
      document.getElementById('th-list').innerHTML = xs.length ? `<div class="grid3">${lim(xs).map(t =>
        `<div class="theme"><div class="panel-h"><h3>${esc(t.theme)}</h3>${link(t.url, fmtD(t.date))}</div><div class="sub">${esc(sk(t.skill))}</div><p>${attr(t.whats_changing)}</p>${(arr(t.winners).length || arr(t.losers).length) ? `<div class="wl">${arr(t.winners).length ? `<span>Benefits</span>${arr(t.winners).map(x => tk(x, 'up')).join(' ')}` : ''}${arr(t.losers).length ? `<span>Hurt</span>${arr(t.losers).map(x => tk(x, 'dn')).join(' ')}` : ''}</div>` : ''}${srcLine(t, 'Sources')}</div>`).join('')}</div>` : `<div class="nores">No themes match. Clear the search or widen the window.</div>`;
    }
    draw();
  }

  // ================= DAILY MOVES =================
  // market cap ($mm, Master comps file) for a ticker or Bloomberg code; $ move = cap x 1D %
  const capOf = (t, bbg) => { const R = (D.comps || {}).rows || {}; const r = (bbg && (R[bbg] || R[String(bbg).replace(/\s+equity$/i, '')])) || R[t + ' US Equity'] || R[t + ' US'] || R[t] || null; return r && r.mkt_cap_usd_mm ? +r.mkt_cap_usd_mm : null; };
  const fmtBn = v => { const b = v / 1000; return (b > 0 ? '+' : '−') + '$' + (Math.abs(b) >= 10 ? Math.abs(b).toFixed(0) : Math.abs(b).toFixed(1)) + 'bn'; };
  function capList(rows, N, pctOf) {
    const xs = rows.map(r => { const cap = capOf(r.t, r.bbg); return cap ? Object.assign({}, r, { cap, dm: cap * pctOf(r) / 100 }) : null; }).filter(Boolean);
    const dn = xs.filter(x => x.dm < 0).sort((a, b) => a.dm - b.dm).slice(0, N), up = xs.filter(x => x.dm > 0).sort((a, b) => b.dm - a.dm).slice(0, N);
    const li = x => `<div class="li"><span class="stripe ${x.dm >= 0 ? 'pos' : 'neg'}"></span><div class="body">${tk(x.t)} <b>${esc(x.n || '')}</b> <span class="mono ${x.dm >= 0 ? 'c-pos' : 'c-neg'}">${fmtBn(x.dm)}</span> <span class="mono sub">${(pctOf(x) > 0 ? '+' : '') + pctOf(x).toFixed(1)}%</span></div></div>`;
    return { up, dn, html: `<div class="grid2"><div><h3 class="c-neg">Biggest market-cap losses</h3><div class="list">${dn.map(li).join('') || none('No data.')}</div></div><div><h3 class="c-pos">Biggest market-cap gains</h3><div class="list">${up.map(li).join('') || none('No data.')}</div></div></div><p class="sub" style="margin:4px 0 0">Dollar change = market cap in the Master comps file (${esc((D.comps || {}).as_of || '')}) × today's % move. Approximate.</p>` };
  }
  const etToday = () => new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
  function renderDaily() {
    const host = document.getElementById('v-daily');
    let up = arr(DLY.up), dn = arr(DLY.down); const secs = arr(DLY.sectors);
    const N = G.n || 12;
    if (N > up.length && arr(DLY.moves).length) {
      const known = new Map(up.concat(dn).map(m => [m.ticker, m])), ST = DLY.stories || {};
      const mk = m => known.get(m.t) || { ticker: m.t, name: m.n, group: m.g, chg_1d: m.c, why: (ST[m.t] || {}).why, sources: (ST[m.t] || {}).sources };
      const sorted = arr(DLY.moves).slice().sort((a, b) => b.c - a.c);
      up = sorted.filter(m => m.c > 0).slice(0, N).map(mk); dn = sorted.filter(m => m.c < 0).reverse().slice(0, N).map(mk);
    } else { up = up.slice(0, N); dn = dn.slice(0, N); }
    const pct = v => v == null ? '' : ((+v > 0 ? '+' : '') + (+v).toFixed(1) + '%');
    const mover = (m) => `<div class="li"><span class="stripe ${+m.chg_1d >= 0 ? 'pos' : 'neg'}"></span><div class="body">${tk(m.ticker)} <b>${esc(m.name || '')}</b>${noteUI('move:' + ntKey(m.ticker) + '|' + (DLY.as_of || ''), m.ticker, (m.name || m.ticker) + ' move ' + (DLY.as_of || ''))} <span class="mono ${+m.chg_1d >= 0 ? 'c-pos' : 'c-neg'}">${pct(m.chg_1d)}</span>${m.group ? ` <span class="chip out">${esc(m.group)}</span>` : ''}<div>${m.why ? whyHtml(m.why) : ''}</div>${valLine(m.ticker, true)}${srcLine(m)}</div></div>`;
    const W = 900, bar = secs.length ? Math.max(...secs.map(s => Math.abs(+s.median_1d || 0)), 0.5) : 1;
    host.innerHTML = head('Daily moves · ' + esc(DLY.as_of || ''), 'What moved and why',
      `Biggest one-day moves across the ${esc(DLY.universe_n || '')}-name Master comps universe on ${esc(DLY.as_of || 'the last trading day')}, by company and by subsector, with the catalyst from your research flow or the news.`) +
      `<section class="panel" id="live-moves"><div class="panel-h"><h2 id="live-h">Live prices</h2><span class="muted" id="live-status">connecting…</span></div><div id="live-body"><p class="sub" style="margin:0">Intraday moves load here from the Live sheet in your newest Master comps file (Bloomberg, via Microsoft 365); FactSet closes are the fallback.</p></div></section>` +
      (() => { const stale = DLY.as_of && DLY.as_of < etToday(); const basis = /midday|intraday/i.test(DLY.notes || '') && !stale && DLY.as_of === etToday() ? 'intraday' : 'close';
        return `<section class="panel dm-asof${stale ? ' stale' : ''}"><b>Written read below: as of ${esc(fmtD(DLY.as_of || ''))} ${basis}.</b> <span class="sub">${stale ? 'This is not today. ' : ''}Written by the last refresh, with a reason for each name. For today's numbers, use the live box above.</span></section>`; })() +
      (DLY.summary ? `<section class="panel"><h2>The day in brief · ${esc(fmtD(DLY.as_of || ''))}</h2><ul class="b">${arr(DLY.summary).map(x => `<li>${attr(x)}</li>`).join('')}</ul></section>` : '') +
      `<section class="panel"><div class="panel-h"><h2>Sectors</h2><span class="muted">median 1-day move by Master comps subsector</span></div>${secs.length ? `<div class="secbars">${secs.map(s => `<div class="sb-row sb-click" data-g="${esc(s.group)}" data-src="eod" tabindex="0" role="button" aria-expanded="false"><span class="sb-l">${esc(s.group)} <span class="sub">(${esc(s.n)})</span></span><span class="sb-track"><span class="sb-bar ${+s.median_1d >= 0 ? 'pos' : 'neg'}" style="width:${(Math.abs(+s.median_1d || 0) / bar * 50).toFixed(1)}%;${+s.median_1d >= 0 ? 'left:50%' : 'right:50%'}"></span></span><span class="sb-v mono ${+s.median_1d >= 0 ? 'c-pos' : 'c-neg'}">${pct(s.median_1d)}</span><span class="sb-w sub">${s.why ? attr(s.why) : ''}</span></div>`).join('')}</div>` : none('No sector data yet.')}</section>` +
      `<div class="grid2"><section class="panel"><div class="panel-h"><h2 class="c-pos">Biggest gainers · ${esc(fmtD(DLY.as_of || ''))}</h2><span class="muted">${up.length}</span></div>${up.length ? `<div class="list">${up.map(mover).join('')}</div>` : none('No data yet.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2 class="c-neg">Biggest decliners · ${esc(fmtD(DLY.as_of || ''))}</h2><span class="muted">${dn.length}</span></div>${dn.length ? `<div class="list">${dn.map(mover).join('')}</div>` : none('No data yet.')}</section></div>` +
      (arr(DLY.moves).length && Object.keys((D.comps || {}).rows || {}).length ? `<section class="panel"><div class="panel-h"><h2>Biggest market-cap moves · ${esc(fmtD(DLY.as_of || ''))}</h2></div>${capList(arr(DLY.moves).map(m => ({ t: m.t, n: m.n, c1: +m.c })), N, r => r.c1).html}</section>` : '') +
      (DLY.notes ? `<p class="sub" style="margin:0">${esc(DLY.notes)}</p>` : '');
    wireSectors(host);
    startLive();
  }

  // ---- sector drill-down: click a sector bar to see the reason and every name in it, with each name's story ----
  let LIVE_SAVED = null;
  let LIVE_G = new Map(), LIVE_SAME = false;
  const sameDayOf = (latest, showDate) => showDate ? !!(latest && DLY.as_of === latest) : DLY.as_of === new Date().toISOString().slice(0, 10);
  function storyOf(t) {
    const st = (DLY.stories || {})[t]; if (st) return typeof st === 'string' ? { why: st } : st;
    const m = arr(DLY.up).concat(arr(DLY.down)).find(x => x.ticker === t); return m ? { why: m.why, sources: m.sources } : null;
  }
  function sectorDetail(g, src) {
    const p1 = v => v == null || !isFinite(v) ? '' : ((v > 0 ? '+' : '') + (+v).toFixed(1) + '%');
    const eod = src === 'eod', useStories = eod || LIVE_SAME;
    const sec = arr(DLY.sectors).find(x => x.group === g);
    const names = eod ? arr(DLY.moves).filter(m => m.g === g).map(m => ({ t: m.t, n: m.n, c: +m.c, c5: m.c5 }))
      : (LIVE_G.get(g) || []).map(r => ({ t: r.t, n: r.n, c: r.c1, c5: r.c5 }));
    if (eod && !names.length) arr(DLY.up).concat(arr(DLY.down)).filter(m => m.group === g).forEach(m => names.push({ t: m.ticker, n: m.name, c: +m.chg_1d, c5: m.chg_5d }));
    names.sort((a, b) => b.c - a.c);
    const why = useStories && sec && sec.why ? `<p style="margin:0 0 6px">${attr(sec.why)}</p>` : (useStories ? '' : `<p class="sub" style="margin:0 0 6px">Reasons are written after the day's tech digest; these are live prices only.</p>`);
    const rows = names.map(x => { const s = useStories ? storyOf(x.t) : null, big = Math.abs(x.c) >= 5;
      return `<div class="sd-row${big ? ' big' : ''}"><span class="sd-t">${tk(x.t)} <span class="sub">${esc(x.n || '')}</span></span><span class="mono ${x.c >= 0 ? 'c-pos' : 'c-neg'}">${p1(x.c)}</span>${x.c5 != null ? `<span class="sub mono">5d ${p1(x.c5)}</span>` : '<span></span>'}<span class="sd-w">${s && s.why ? whyHtml(s.why) + (arr(s.sources).length ? ` <span class="sub">· ${arr(s.sources).map(esc).join(' · ')}</span>` : '') : ''}</span></div>`; }).join('');
    return `<div class="sb-det">${why}${rows || '<p class="sub" style="margin:0">No names priced in this group.</p>'}</div>`;
  }
  function wireSectors(host) {
    if (host.__sbWired) return; host.__sbWired = true;
    const go = row => { const nx = row.nextElementSibling; const open = nx && nx.classList.contains('sb-det');
      if (open) { nx.remove(); row.setAttribute('aria-expanded', 'false'); return; }
      row.insertAdjacentHTML('afterend', sectorDetail(row.dataset.g, row.dataset.src)); row.setAttribute('aria-expanded', 'true'); };
    host.addEventListener('click', e => { const r = e.target.closest('.sb-click'); if (r && !e.target.closest('a')) go(r); });
    host.addEventListener('keydown', e => { const r = e.target.closest('.sb-click'); if (r && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); go(r); } });
  }

  // ---- live moves: the viewer's FactSet connector, latest closes for the Master comps universe ----
  let liveStarted = false;
  function startLive() {
    if (liveStarted) return; liveStarted = true;
    const U = D.universe || {}, names = arr(U.names), bench = arr(U.benchmarks);
    const status = t => { const el = document.getElementById('live-status'); if (el) el.textContent = t; };
    const body = h => { const el = document.getElementById('live-body'); if (el) el.innerHTML = h; };
    if (!names.length) { status('no universe'); body(none('No universe list in this build.')); return; }
    const claude = window.claude;
    if (!claude || typeof claude.use !== 'function') { status('not available here'); body(none('Live prices need the page open on claude.ai with your FactSet connector. The written read below is from the evening refresh.')); return; }
    const ids = [...new Set(names.map(n => n.id).concat(bench.map(b => b.id)))];
    const batches = []; for (let i = 0; i < ids.length; i += 50) batches.push(ids.slice(i, i + 50));
    const start = new Date(Date.now() - 12 * 864e5).toISOString().slice(0, 10);
    const got = new Map(), errs = new Map(); let stamp = 0;
    const meta = new Map(names.map(n => [n.id, n])); bench.forEach(b => meta.set(b.id, { t: b.t, n: b.t, g: '_bench' }));
    const MSG = {
      needs_reauth: 'Reconnect FactSet in claude.ai Settings → Connectors.',
      server_not_connected: 'Add the FactSet connector in claude.ai Settings → Connectors to see live closes.',
      selection_required: 'Choose which FactSet connector this page should use when claude.ai asks.',
      not_in_manifest: 'FactSet is turned off for this page. Turn it on from the page\'s Permissions menu.',
      blocked_by_policy: 'Your organization blocks FactSet for this page.',
      approval_required: 'FactSet needs your approval for this page (Bloomberg via Microsoft 365 was not available).',
      not_granted: 'Live prices are not available in this view.', capability_disabled: 'Live prices are not available in this view.',
    };
    const DENY = new Set(['needs_reauth', 'server_not_connected', 'blocked_by_policy', 'approval_required', 'not_in_manifest', 'selection_required', 'not_granted', 'capability_disabled']);
    function series(rows) {
      const by = new Map();
      arr(rows).forEach(r => { if (r && r.price != null && r.requestId) { if (!by.has(r.requestId)) by.set(r.requestId, []); by.get(r.requestId).push([String(r.date), +r.price]); } });
      by.forEach(v => v.sort((a, b) => a[0] < b[0] ? -1 : 1)); return by;
    }
    function draw() {
      const deny = [...errs.values()].find(e => DENY.has(e.code));
      if (deny && !got.size) { status('not connected');
        body(`<p class="sub" style="margin:0">${esc(MSG[deny.code] || deny.message || 'FactSet is not available.')}</p>` + (deny.code === 'approval_required' ? `<button class="btn" id="live-approve" style="margin-top:8px">Load latest closes from FactSet</button>` : ''));
        const btn = document.getElementById('live-approve');
        if (btn) btn.onclick = () => { btn.disabled = true; btn.textContent = 'Loading…'; loadOnce(); };
        return; }
      if (!got.size) return;
      const rows = [];
      got.forEach((v, id) => { const m = meta.get(id); if (!m || v.length < 2) return; const [d1, p1] = v[v.length - 1], [, p0] = v[v.length - 2]; const p5 = v.length > 5 ? v[v.length - 6][1] : null;
        rows.push({ id, t: m.t, n: m.n, g: m.g, date: d1, c1: (p1 / p0 - 1) * 100, c5: p5 ? (p1 / p5 - 1) * 100 : null }); });
      const stocks = rows.filter(r => r.g !== '_bench'), bm = rows.filter(r => r.g === '_bench');
      const latest = stocks.reduce((a, r) => r.date > a ? r.date : a, '');
      const failed = [...errs.values()].filter(e => !DENY.has(e.code)).length;
      paint(stocks, bm, latest, `FactSet closes through ${latest}${stamp ? ' · fetched ' + new Date(stamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}${failed ? ` · ${failed} batch${failed > 1 ? 'es' : ''} failed` : ''}`, true);
    }
    function paint(stocks, bm, latest, stat, showDate) {
      const head = document.getElementById('live-h');
      if (head) { const sv = !showDate && LIVE_SAVED; const old = sv && (Date.now() - sv.getTime() > 30 * 60e3 || sv.toLocaleDateString('en-CA', { timeZone: 'America/New_York' }) !== etToday());
        head.innerHTML = showDate ? `Live from FactSet · closes through ${esc(fmtD(latest || ''))}` : `Live from Bloomberg · intraday${sv ? ` · sheet saved ${esc(sv.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }))}` : ''}${old ? ' <span class="c-neg">· sheet not saved in the last 30 min; values may be stale</span>' : ''}`; }
      const pct = v => v == null || !isFinite(v) ? '—' : ((v > 0 ? '+' : '') + v.toFixed(1) + '%');
      const cls = v => v >= 0 ? 'c-pos' : 'c-neg';
      const med = a => { const s = a.slice().sort((x, y) => x - y); return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0; };
      const groups = new Map(); stocks.forEach(r => { if (!groups.has(r.g)) groups.set(r.g, []); groups.get(r.g).push(r); });
      LIVE_G = groups; LIVE_SAME = sameDayOf(latest, showDate);
      const secs = [...groups].map(([g, a]) => ({ g, n: a.length, m: med(a.map(r => r.c1)), best: a.reduce((x, y) => y.c1 > x.c1 ? y : x), worst: a.reduce((x, y) => y.c1 < x.c1 ? y : x) })).sort((a, b) => b.m - a.m);
      const bar = Math.max(...secs.map(s => Math.abs(s.m)), 0.5);
      const why = new Map(arr(DLY.up).concat(arr(DLY.down)).map(m => [m.ticker, m]));
      const sameDay = showDate ? (latest && DLY.as_of === latest) : (DLY.as_of === latest);
      const line = r => { const w = sameDay ? why.get(r.t) : null; return `<div class="li"><span class="stripe ${r.c1 >= 0 ? 'pos' : 'neg'}"></span><div class="body">${tk(r.t)} <b>${esc(r.n)}</b> <span class="mono ${cls(r.c1)}">${pct(r.c1)}</span> ${r.c5 != null ? `<span class="sub mono">5d ${pct(r.c5)}</span>` : ''} <span class="chip out">${esc(r.g)}</span>${showDate && r.date !== latest ? ` <span class="sub">close ${esc(r.date)}</span>` : ''}${w && w.why ? `<div>${whyHtml(w.why)}</div>` : ((DLY.stories || {})[r.t] && sameDay ? `<div>${whyHtml((DLY.stories || {})[r.t].why)}</div>` : '')}</div></div>`; };
      const s = stocks.slice().sort((a, b) => b.c1 - a.c1), NN = Math.min(G.n || 12, s.length), up = s.slice(0, NN), dn = s.slice(-NN).reverse();
      const upN = stocks.filter(r => r.c1 > 0).length;
      status(stat);
      body(`<p class="sub" style="margin:0 0 8px">${stocks.length} names priced · ${upN} up / ${stocks.length - upN} down · median ${pct(med(stocks.map(r => r.c1)))}${bm.length ? ' · ' + bm.map(b => `${esc(b.t)} <span class="mono ${cls(b.c1)}">${pct(b.c1)}</span>`).join(' · ') : ''}${sameDay || !DLY.as_of ? '' : ` · <b>newer than the written read below (${esc(DLY.as_of)})</b>`}</p>` +
        `<div class="secbars">${secs.map(x => `<div class="sb-row sb-click" data-g="${esc(x.g)}" data-src="live" tabindex="0" role="button" aria-expanded="false"><span class="sb-l">${esc(x.g)} <span class="sub">(${x.n})</span></span><span class="sb-track"><span class="sb-bar ${x.m >= 0 ? 'pos' : 'neg'}" style="width:${(Math.abs(x.m) / bar * 50).toFixed(1)}%;${x.m >= 0 ? 'left:50%' : 'right:50%'}"></span></span><span class="sb-v mono ${cls(x.m)}">${pct(x.m)}</span><span class="sb-w sub">best ${esc(x.best.t)} ${pct(x.best.c1)} · worst ${esc(x.worst.t)} ${pct(x.worst.c1)}</span></div>`).join('')}</div>` +
        `<div class="grid2" style="margin-top:14px"><div><h3 class="c-pos">Biggest gainers</h3><div class="list">${up.map(line).join('')}</div></div><div><h3 class="c-neg">Biggest decliners</h3><div class="list">${dn.map(line).join('')}</div></div></div>` +
        (Object.keys((D.comps || {}).rows || {}).length ? `<div style="margin-top:14px">${capList(stocks, NN, r => r.c1).html}</div>` : ''));
    }
    let MCP = null;
    const inputFor = b => ({ ids: b, data_type: 'prices', startDate: start, fields: ['price'], adjust: 'SPLIT', request_id: 'tech-daily-live-' + start });
    function loadOnce() {
      if (!MCP) return;
      batches.forEach((b, i) => MCP.callTool('FactSet', 'FactSet_GlobalPrices', inputFor(b), { cache: { staleTime: 15 * 60e3, gcTime: 24 * 3600e3 } })
        .then(r => { series(r.payload && r.payload.data).forEach((v, k) => got.set(k, v)); errs.delete(i); stamp = Math.max(stamp, (r.cache && r.cache.storedAt) || Date.now()); draw(); })
        .catch(e => { errs.set(i, e || { code: 'upstream_error' }); draw(); }));
    }
    claude.use('mcp').then(mcp => {
      MCP = mcp;
      if (!mcp) { status('not available here'); body(none('Live prices are not available in this view. The written read below is from the evening refresh.')); return; }
      startBbg(mcp, () => startFactSet(mcp));
    }).catch(() => { status('not available here'); });

    // Bloomberg: the "Live" sheet (Ticker | Price | Chg % 1D) in the newest Master comps workbook in OneDrive › Trading comps
    function startBbg(mcp, fallback) {
      const M = 'Microsoft 365', today = new Date().toISOString().slice(0, 10);
      const byT = new Map(); names.forEach(n => { const k = String(n.t || '').toUpperCase(); if (k && !byT.has(k)) byT.set(k, n); });
      const textOf = r => { const p = r && r.payload; if (typeof p === 'string') return p; return arr(r && r.content).filter(c => c && c.type === 'text').map(c => c.text).join('\n'); };
      const jsonBlocks = r => { const out = []; const p = r && r.payload; if (p && typeof p === 'object' && !Array.isArray(p) && p.uri) out.push(p);
        arr(r && r.content).forEach(c => { if (c && c.type === 'text') { try { const j = JSON.parse(c.text); (Array.isArray(j) ? j : [j]).forEach(x => x && x.uri && out.push(x)); } catch (e) { } } });
        const seen = new Set(); return out.filter(x => !seen.has(x.uri) && seen.add(x.uri)); };
      let files = [], timer = null, okOnce = false, tries = 0;
      status('finding the newest Master comps file…');
      mcp.callTool(M, 'sharepoint_search', { query: 'Trading Comparables', folderName: 'Trading comps', fileType: 'xlsx', limit: 25 }, { cache: { staleTime: 30 * 60e3, gcTime: 24 * 3600e3 } })
        .then(r => { files = jsonBlocks(r).filter(f => !/\/Drafts\//i.test(f.webUrl || '')).sort((a, b) => String(b.lastModifiedDateTime).localeCompare(String(a.lastModifiedDateTime)));
          if (!files.length) throw { code: 'no_file' }; tryFile(0); })
        .catch(e => { if (!okOnce) fallback(); });
      function tryFile(i) {
        const f = files[i]; if (!f) { if (!okOnce) fallback(); return; }
        mcp.callTool(M, 'read_resource', { uri: f.uri, startPage: 999 }, { cache: { staleTime: 30 * 60e3, gcTime: 24 * 3600e3 } })
          .then(r => { const m = textOf(r).match(/^\s*(\d+)\.\s+Live\b/m); if (!m) return tryFile(i + 1); readLive(f, +m[1]); })
          .catch(() => { if (!okOnce) fallback(); });
      }
      function readLive(f, sheet) {
        mcp.callTool(M, 'read_resource', { uri: f.uri, startPage: sheet, endPage: sheet }, { cache: { staleTime: 4 * 60e3, gcTime: 3600e3 } })
          .then(r => {
            const t = textOf(r), at = t.indexOf('## Sheet: Live');
            if (at < 0) { if (++tries < 3) return setTimeout(() => readLive(f, sheet), 4000); if (!okOnce) fallback(); return; }
            tries = 0;
            const lines = t.slice(at).split('\n'), stocks = [];
            for (const ln of lines) { if (/^Formulas:/.test(ln)) break; const c = ln.split('\t'); if (c.length < 3 || !/equity/i.test(c[0])) continue;
              const c1 = parseFloat(c[2]), px = parseFloat(c[1]); if (!isFinite(c1)) continue;
              const full = c[0].trim().replace(/\s+equity$/i, '').toUpperCase(), parts = full.split(/\s+/);
              const u = byT.get(full) || ((!parts[1] || parts[1] === 'US') ? byT.get(parts[0]) : null) || {};
              stocks.push({ t: u.t || (parts[1] && parts[1] !== 'US' ? full : parts[0]), bbg: c[0].trim(), n: u.n || '', g: (c[3] || '').trim() || u.g || 'Other', c1, c5: null, px, date: today }); }
            if (!stocks.length) { if (!okOnce) fallback(); return; }
            okOnce = true;
            const saved = f.lastModifiedDateTime ? new Date(f.lastModifiedDateTime) : null;
            const got = r.cache && r.cache.storedAt ? new Date(r.cache.storedAt) : new Date();
            const hm = d => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            LIVE_SAVED = saved;
            paint(stocks, [], today, `${f.name}${saved ? ' · file saved ' + (saved.toISOString().slice(0, 10) === today ? '' : saved.toISOString().slice(0, 10) + ' ') + hm(saved) : ''} · read ${hm(got)}`, false);
            clearTimeout(timer); timer = setTimeout(() => readLive(f, sheet), 5 * 60e3);
          })
          .catch(e => { if (!okOnce) fallback(); else { clearTimeout(timer); timer = setTimeout(() => readLive(f, sheet), 5 * 60e3); } });
      }
    }

    function startFactSet(mcp) {
      if (!mcp) { status('not available here'); body(none('Live prices are not available in this view. The written read below is from the evening refresh.')); return; }
      status('loading ' + ids.length + ' names…');
      batches.forEach((b, i) => {
        mcp.watchTool('FactSet', 'FactSet_GlobalPrices', inputFor(b),
          ev => {
            if (ev.type === 'data') { const pl = ev.result && ev.result.payload; series(pl && pl.data).forEach((v, k) => got.set(k, v)); errs.delete(i);
              const st = ev.result && ev.result.cache && ev.result.cache.storedAt; stamp = Math.max(stamp, st || Date.now()); }
            else { errs.set(i, ev.error || { code: 'upstream_error' }); if (DENY.has((ev.error || {}).code)) b.forEach(id => got.delete(id)); }
            draw();
          }, { cache: { staleTime: 15 * 60e3, gcTime: 24 * 3600e3 }, refetchInterval: 15 * 60e3 });
      });
    }
  }

  // ================= SIGNALS =================
  function spark(series, w = 120, h = 26) {
    const s = arr(series).slice(-52).map(p => +p[1] || +p.index || 0); if (s.length < 2) return '';
    const mn = Math.min(...s), mx = Math.max(...s), r = (mx - mn) || 1;
    const pts = s.map((v, i) => `${(i / (s.length - 1) * (w - 4) + 2).toFixed(1)},${(h - 3 - (v - mn) / r * (h - 6)).toFixed(1)}`).join(' ');
    const up = s[s.length - 1] >= s[0];
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${up ? 'var(--pos)' : 'var(--neg)'}" stroke-width="1.5"/><circle cx="${pts.split(' ').pop().split(',')[0]}" cy="${pts.split(' ').pop().split(',')[1]}" r="2" fill="${up ? 'var(--pos)' : 'var(--neg)'}"/></svg>`;
  }
  function renderSignals() {
    const cos = arr(SIG.companies);
    const host = document.getElementById('v-signals');
    host.innerHTML = head('Signals · your evidence, Rebecca\'s method', 'Datapoint signals',
      'Each company\'s datapoint index (100 = start; moves with direction × source credibility × confidence of every stored datapoint) and bull vs bear strength by driver, recomputed from your Supabase evidence with the Tech Coverage Monitor method.') +
      (cos.length ? '' : none('Signals have not been computed yet.')) +
      `<div class="ctl" role="group" aria-label="Signal filters">
        <label for="sg-q">Search <input type="search" id="sg-q" placeholder="Ticker or company"></label>
        <div class="seg" id="sg-sort"><button type="button" data-v="chg_90d" aria-pressed="true">90d change</button><button type="button" data-v="chg_30d" aria-pressed="false">30d change</button><button type="button" data-v="spread" aria-pressed="false">Bull − bear</button><button type="button" data-v="n_90d" aria-pressed="false">Most evidence</button></div>
        <div class="seg" id="sg-dir"><button type="button" data-v="desc" aria-pressed="true">Top</button><button type="button" data-v="asc" aria-pressed="false">Bottom</button></div>
        <span class="count" id="sg-count"></span></div>
      <div class="panel" style="padding:0"><div class="tbl-wrap"><table class="dt"><thead><tr><th>Company</th><th class="n">Rows 90d</th><th class="n">Index</th><th class="n">30d</th><th class="n">90d</th><th>52 weeks</th><th class="n">Bull</th><th class="n">Bear</th><th class="n">Spread</th></tr></thead><tbody id="sg-body"></tbody></table></div></div>
      <p class="sub" style="margin:0">${esc(SIG.method || '')} As of ${esc(SIG.as_of || '')}. Click a row for the breakdown by driver.</p>`;
    const st = { q: '', k: 'chg_90d', dir: 'desc', open: null };
    const f1 = v => v == null ? '' : (+v).toFixed(1), sg = v => v == null ? '' : ((+v > 0 ? '+' : '') + (+v).toFixed(1));
    function draw() {
      const xs = cos.filter(c => !st.q || `${c.ticker} ${c.company}`.toLowerCase().includes(st.q))
        .sort((a, b) => ((+b[st.k] || 0) - (+a[st.k] || 0)) * (st.dir === 'desc' ? 1 : -1)).slice(0, G.n || 150);
      document.getElementById('sg-count').textContent = xs.length + ' of ' + cos.length + ' companies';
      document.getElementById('sg-body').innerHTML = xs.map(c => {
        const row = `<tr class="sg-row" data-t="${esc(c.ticker)}" tabindex="0" style="cursor:pointer"><td>${tk(c.ticker)} <span class="sub">${esc(c.company)}</span></td><td class="n">${esc(c.n_90d)}</td><td class="n">${f1(c.index_now)}</td><td class="n ${numCls(sg(c.chg_30d))}">${sg(c.chg_30d)}</td><td class="n ${numCls(sg(c.chg_90d))}">${sg(c.chg_90d)}</td><td>${spark(c.series)}</td><td class="n">${f1(c.bull)}</td><td class="n">${f1(c.bear)}</td><td class="n ${numCls(sg(c.spread))}">${sg(c.spread)}</td></tr>`;
        const det = st.open === c.ticker ? `<tr><td colspan="9" style="background:var(--surface-2)"><table class="dt" style="width:auto"><thead><tr><th>Driver</th><th class="n">Rows</th><th class="n">Bull</th><th class="n">Bear</th></tr></thead><tbody>${arr(c.by_field).map(f => `<tr><td>${esc(f.field_key)}</td><td class="n">${esc(f.n)}</td><td class="n">${f1(f.bull)}</td><td class="n">${f1(f.bear)}</td></tr>`).join('')}</tbody></table></td></tr>` : '';
        return row + det; }).join('');
      host.querySelectorAll('.sg-row').forEach(r => { const go = () => { st.open = st.open === r.dataset.t ? null : r.dataset.t; draw(); }; r.addEventListener('click', go); r.addEventListener('keydown', e => { if (e.key === 'Enter') go(); }); });
    }
    const seg = (id, key) => host.querySelectorAll('#' + id + ' button').forEach(b => b.addEventListener('click', () => { st[key] = b.dataset.v; host.querySelectorAll('#' + id + ' button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); draw(); }));
    seg('sg-sort', 'k'); seg('sg-dir', 'dir');
    document.getElementById('sg-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); draw(); });
    draw();
  }

  // ================= SOURCES =================
  function renderSources() {
    const list = arr(SRC.sources);
    const host = document.getElementById('v-sources');
    // every source string used on this desk
    const corpus = [];
    const add = x => { if (x) corpus.push(String(x).toLowerCase()); };
    const brk = t => { const m = String(t || '').match(/\[([^\]]+)\]\s*$/); if (m) add(m[1]); };
    arr(DP.rows).forEach(r => add(r.primary_source));
    [].concat(arr(D.bobby), arr(D.rebecca)).forEach(n => { arr(n.sources).forEach(add); arr(n.summary).forEach(brk); arr(n.whats_changing).forEach(brk); });
    arr(TODAY.digests).forEach(d => { arr(d.callouts).forEach(c => add(c.source)); arr(d.themes).forEach(t => arr(t.sources).forEach(add)); });
    [].concat(arr(ID.ideas), arr(ID.theses), arr(ID.opcomps), arr(PR.prep)).forEach(x => arr(x.sources).forEach(add));
    const reEsc = x => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const uses = new Map();
    list.forEach(sv => {
      const m = String(sv.source).match(/^(.*?)\s*\((.*)\)\s*$/);
      const firm = (m ? m[1] : sv.source).trim().toLowerCase(), who = m ? m[2].trim().toLowerCase().split(/[\s/,]+/).pop() : '';
      if (firm.length < 2) return;
      const fr = new RegExp('(^|[^a-z0-9])' + reEsc(firm) + '([^a-z0-9]|$)'), wr = who ? new RegExp('(^|[^a-z])' + reEsc(who) + '([^a-z]|$)') : null;
      let n = 0; corpus.forEach(c => { if (fr.test(c) && (!wr || wr.test(c))) n++; });
      uses.set(sv.source, n);
    });
    const types = [...new Set(list.map(x => x.main_type).filter(Boolean))].sort();
    const dots = v => { const n = Math.round(+v || 0); return `<span class="dots" title="${esc(v)} of 5">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= n ? 'on' : ''}"></i>`).join('')}</span>`; };
    host.innerHTML = head('Sources · from Rebecca\'s Tech Coverage Monitor', 'Source credibility',
      'Every source in the Tech Coverage Monitor, with its starting prior by who it is and the type of evidence, adjusted when later, more credible datapoints confirm or refute its earlier claims. "On this desk" counts how often the source is cited across the tabs here.') +
      `<p class="sub" style="margin:0">Copied from <a class="ext" href="${esc(SRC.origin_url)}" target="_blank" rel="noopener">${esc(SRC.origin || 'Tech Coverage Monitor')} ↗</a> as of ${esc(SRC.asof || '')}. ${list.length} sources.</p>` +
      `<div class="ctl" role="group" aria-label="Source filters">
        <label for="sv-q">Search <input type="search" id="sv-q" placeholder="Firm or analyst"></label>
        <label for="sv-t">Type <select id="sv-t"><option value="">All types</option>${types.map(t => `<option>${esc(t)}</option>`).join('')}</select></label>
        <div class="seg" id="sv-use"><button type="button" data-v="" aria-pressed="true">All</button><button type="button" data-v="1" aria-pressed="false">Cited on this desk</button></div>
        <span class="count" id="sv-count"></span></div>
      <div class="panel" style="padding:0"><div class="tbl-wrap"><table class="dt sortable"><thead><tr>
        <th data-k="source">Source</th><th data-k="main_type">Main type</th><th class="n" data-k="n">Datapoints</th><th class="n" data-k="prior">Prior</th><th class="n" data-k="hits">Confirmed</th><th class="n" data-k="misses">Refuted</th><th data-k="cred">Her credibility</th><th class="n" data-k="mine">Yours</th><th class="n" data-k="use">On this desk</th>
      </tr></thead><tbody id="sv-body"></tbody></table></div></div>
      <button type="button" class="btn more" id="sv-more" hidden>Show 100 more</button>`;
    const st = { q: '', t: '', use: '', k: 'n', dir: -1, shown: 100 };
    const n1 = v => v == null ? '' : (+v).toFixed(1);
    function draw() {
      const mineMap = new Map(arr(SIG.sources).map(m => [String(m.source).toLowerCase(), m]));
      const mineOf = n => { const k = String(n).toLowerCase(); return mineMap.get(k) || mineMap.get(k.replace(/\s*\(.*\)$/, '')); };
      const xs = list.map(x => { const m = mineOf(x.source); return Object.assign({ use: uses.get(x.source) || 0, mine: m ? m.cred : null, mine_n: m && m.n, mine_h: m && m.hits, mine_m: m && m.misses }, x); }).filter(x =>
        (!st.q || String(x.source).toLowerCase().includes(st.q)) && (!st.t || x.main_type === st.t) && (!st.use || x.use > 0));
      xs.sort((a, b) => { const A = a[st.k], B = b[st.k]; return (typeof A === 'number' || typeof B === 'number' ? ((+A || 0) - (+B || 0)) : String(A || '').localeCompare(String(B || ''))) * st.dir; });
      document.getElementById('sv-count').textContent = xs.length + ' sources';
      document.getElementById('sv-body').innerHTML = xs.length ? xs.slice(0, st.shown).map(x => `<tr><td><b>${esc(x.source)}</b></td><td><span class="chip out">${esc(x.main_type)}</span></td><td class="n">${esc(x.n)}</td><td class="n">${n1(x.prior)}</td><td class="n">${esc(Math.round(x.hits || 0))}</td><td class="n">${esc(Math.round(x.misses || 0))}</td><td>${dots(x.cred)} <span class="mono">${n1(x.cred)}</span></td><td class="n">${x.mine != null ? `<span class="mono" title="Your evidence: ${esc(x.mine_n)} rows, ${esc(x.mine_h)} confirmed / ${esc(x.mine_m)} refuted">${n1(x.mine)}</span>` : '<span class="sub">–</span>'}</td><td class="n">${x.use || '<span class="sub">–</span>'}</td></tr>`).join('')
        : `<tr><td colspan="9" class="nores">No sources match.</td></tr>`;
      document.getElementById('sv-more').hidden = xs.length <= st.shown;
      host.querySelectorAll('th[data-k]').forEach(th => th.setAttribute('aria-sort', th.dataset.k === st.k ? (st.dir > 0 ? 'ascending' : 'descending') : 'none'));
    }
    host.querySelectorAll('th[data-k]').forEach(th => { th.tabIndex = 0; const go = () => { const k = th.dataset.k; st.dir = st.k === k ? -st.dir : (k === 'source' || k === 'main_type' ? 1 : -1); st.k = k; draw(); }; th.addEventListener('click', go); th.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } }); });
    document.getElementById('sv-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); st.shown = 100; draw(); });
    document.getElementById('sv-t').addEventListener('change', e => { st.t = e.target.value; st.shown = 100; draw(); });
    host.querySelectorAll('#sv-use button').forEach(b => b.addEventListener('click', () => { st.use = b.dataset.v; st.shown = 100; host.querySelectorAll('#sv-use button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); draw(); }));
    document.getElementById('sv-more').addEventListener('click', () => { st.shown += 100; draw(); });
    draw();
  }

  // ================= DATAPOINTS =================
  const PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#6250d6', '#008300', '#e34948', '#7a8599'];
  function renderDatapoints() {
    const X = D.dp_index || {}, host = document.getElementById('v-datapoints');
    const dates = arr(X.dates), cos = arr(X.companies), meta = arr(X.meta), secs = arr(X.sectors);
    if (!dates.length) { host.innerHTML = head('Supabase · research_evidence', 'Datapoints', '') + none('No datapoint index in this build.'); return; }
    const byRid = new Map(meta.map(m => [m.rid, m])), coByRid = new Map(cos.map(c => [c.rid, c]));
    const SEC_ORDER = ['Semis', 'Hardware', 'Power & DC infra', 'Software', 'Internet', 'IT Services', 'Industry', 'Other'];
    const secList = SEC_ORDER.filter(s => meta.some(m => m.sec === s));
    const st = { sec: '', sub: '', sel: [], range: G.days ? Math.min(G.days, 270) : 270, mode: 'c', pil: '', imp: 'all', stype: '', q: '', shown: 100 };
    const FIELD_PIL = k => /^growth|^tam/.test(k) ? 'Growth' : /^margin/.test(k) ? 'Margins' : /^competition/.test(k) ? 'Competition' : /^risk/.test(k) ? 'Risk' : 'Other';
    const sgn = v => v == null ? '' : (v > 0 ? '+' : '') + (+v).toFixed(1);
    host.innerHTML = head('Supabase · research_evidence · ' + esc(fmtD(X.since)) + ' – ' + esc(fmtD(X.as_of)), 'Datapoints & Composite Evidence Index',
      `${(+X.n_rows || 0).toLocaleString()} datapoints from the last 9 months across ${meta.length} companies. Pick a sector and any tickers to chart their Composite Evidence Index and read the evidence behind it.`) +
      `<div class="ctl dp-ctl" role="group" aria-label="Filters">
        <label for="dp-sec">Sector <select id="dp-sec"><option value="">All sectors</option>${secList.map(s => `<option>${esc(s)}</option>`).join('')}</select></label>
        <label for="dp-sub">Subsector <select id="dp-sub"><option value="">All</option></select></label>
        <div class="ms" id="dp-ms"><label for="dp-tq">Tickers</label><div class="ms-box"><span id="dp-chips"></span><input id="dp-tq" type="search" placeholder="Add tickers…" autocomplete="off" aria-autocomplete="list" aria-controls="dp-opts"></div><div class="ms-opts" id="dp-opts" role="listbox" hidden></div></div>
        <div class="seg" id="dp-range"><button type="button" data-v="90" aria-pressed="false">3M</button><button type="button" data-v="180" aria-pressed="false">6M</button><button type="button" data-v="270" aria-pressed="true">9M</button></div>
      </div>
      <section class="panel"><div class="panel-h"><h2 id="ix-title">Composite Evidence Index</h2><div class="seg" id="ix-mode"><button type="button" data-v="c" aria-pressed="true">Absolute</button><button type="button" data-v="x" aria-pressed="false">vs universe</button></div></div>
        <div id="ix-chart"></div><div class="legend" id="ix-legend"></div><p class="sub" id="ix-note" style="margin:6px 0 0"></p></section>
      <section class="panel" style="padding:0"><div class="panel-h" style="padding:12px 14px 0"><h2>Companies</h2><span class="muted" id="lb-count"></span></div><div class="tbl-wrap"><table class="dt"><thead><tr><th>Company</th><th>Sector</th><th class="n">Index</th><th class="n">vs univ.</th><th class="n">30d Δ</th><th class="n">Growth</th><th class="n">Margins</th><th class="n">Comp.</th><th class="n">Risk</th><th class="n">Rows 90d</th><th></th></tr></thead><tbody id="lb-body"></tbody></table></div></section>
      <div class="ctl" role="group" aria-label="Datapoint filters">
        <label for="dp-q">Search <input type="search" id="dp-q" placeholder="Word in the evidence"></label>
        <label for="dp-pil">Driver <select id="dp-pil"><option value="">All</option><option>Growth</option><option>Margins</option><option>Competition</option><option>Risk</option><option>Other</option></select></label>
        <label for="dp-st">Source <select id="dp-st"><option value="">All</option></select></label>
        <div class="seg" id="dp-imp"><button type="button" data-v="all" aria-pressed="true">Any</button><button type="button" data-v="pos" aria-pressed="false">Positive</button><button type="button" data-v="neg" aria-pressed="false">Negative</button><button type="button" data-v="mix" aria-pressed="false">Mixed</button></div>
        <span class="count" id="dp-count"></span></div>
      <div class="panel" style="padding:0"><div class="tbl-wrap"><table class="dt"><thead><tr><th>Event</th><th>Ticker</th><th>Driver</th><th>Impact</th><th>Evidence</th><th>Source</th></tr></thead><tbody id="dp-body"><tr><td colspan="6" class="nores">Loading datapoints…</td></tr></tbody></table></div></div>
      <button type="button" class="btn more" id="dp-more" hidden>Show 100 more</button>
      <details class="panel"><summary><b>How the index is built</b></summary><pre class="method">${esc(X.method || '')}</pre></details>`;

    const $ = id => document.getElementById(id);
    const inScope = m => (!st.sec || m.sec === st.sec) && (!st.sub || m.sub === st.sub);
    function fillSubs() {
      const subs = [...new Set(meta.filter(m => !st.sec || m.sec === st.sec).map(m => m.sub).filter(Boolean))].sort();
      $('dp-sub').innerHTML = `<option value="">All</option>${subs.map(s => `<option${s === st.sub ? ' selected' : ''}>${esc(s)}</option>`).join('')}`;
    }
    // ---- ticker multi-select ----
    function chips() { $('dp-chips').innerHTML = st.sel.map(r => { const m = byRid.get(r) || {}; return `<button type="button" class="ms-chip" data-r="${r}" aria-label="Remove ${esc(m.t)}">${esc(m.t)} ×</button>`; }).join(''); }
    function opts() {
      const q = $('dp-tq').value.trim().toLowerCase();
      const list = meta.filter(m => inScope(m) && !st.sel.includes(m.rid) && (!q || `${m.t} ${m.n}`.toLowerCase().includes(q))).sort((a, b) => b.count - a.count).slice(0, 30);
      const box = $('dp-opts');
      box.innerHTML = list.length ? list.map((m, i) => `<div class="ms-opt" role="option" data-r="${m.rid}" tabindex="-1"${i === 0 ? ' aria-selected="true"' : ''}><b>${esc(m.t)}</b> <span class="sub">${esc(m.n || '')} · ${esc(m.sub || m.sec)} · ${m.count}</span></div>`).join('') : '<div class="ms-opt sub">No match</div>';
      box.hidden = false;
    }
    const add = r => { r = +r; if (r && !st.sel.includes(r)) st.sel.push(r); $('dp-tq').value = ''; chips(); st.shown = 100; drawAll(); opts(); };
    $('dp-tq').addEventListener('focus', opts); $('dp-tq').addEventListener('input', opts);
    $('dp-tq').addEventListener('keydown', e => { if (e.key === 'Enter') { const o = $('dp-opts').querySelector('.ms-opt[data-r]'); if (o) { e.preventDefault(); add(o.dataset.r); } } else if (e.key === 'Escape') $('dp-opts').hidden = true; else if (e.key === 'Backspace' && !e.target.value && st.sel.length) { st.sel.pop(); chips(); drawAll(); } });
    $('dp-opts').addEventListener('mousedown', e => { const o = e.target.closest('.ms-opt[data-r]'); if (o) { e.preventDefault(); add(o.dataset.r); } });
    $('dp-tq').addEventListener('blur', () => setTimeout(() => { $('dp-opts').hidden = true; }, 120));
    $('dp-chips').addEventListener('click', e => { const c = e.target.closest('.ms-chip'); if (c) { st.sel = st.sel.filter(r => r !== +c.dataset.r); chips(); drawAll(); } });
    $('dp-sec').addEventListener('change', e => { st.sec = e.target.value; st.sub = ''; fillSubs(); st.shown = 100; drawAll(); });
    $('dp-sub').addEventListener('change', e => { st.sub = e.target.value; st.shown = 100; drawAll(); });
    const seg = (id, key, cb) => host.querySelectorAll('#' + id + ' button').forEach(b => b.addEventListener('click', () => { st[key] = isNaN(+b.dataset.v) ? b.dataset.v : +b.dataset.v; host.querySelectorAll('#' + id + ' button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); st.shown = 100; cb(); }));
    seg('dp-range', 'range', drawAll); seg('ix-mode', 'mode', drawChart); seg('dp-imp', 'imp', drawRows);
    $('dp-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); st.shown = 100; drawRows(); });
    $('dp-pil').addEventListener('change', e => { st.pil = e.target.value; st.shown = 100; drawRows(); });
    $('dp-st').addEventListener('change', e => { st.stype = e.target.value; st.shown = 100; drawRows(); });
    $('dp-more').addEventListener('click', () => { st.shown += 100; drawRows(); });

    // ---- chart ----
    function drawChart() {
      const startIx = Math.max(0, dates.length - Math.ceil(st.range / 7) - 1);
      const ds = dates.slice(startIx), key = st.mode;
      let lines = [];
      if (st.sel.length) lines = st.sel.map(r => coByRid.get(r)).filter(Boolean).map(c => ({ name: c.t, v: c[key] }));
      else if (st.sec) { const s = secs.find(x => x.sec === st.sec); if (s) lines.push({ name: st.sec, v: s[key] }); }
      else lines = secs.filter(s => s.sec !== 'Other' && s.sec !== 'Industry').map(s => ({ name: s.sec, v: s[key] }));
      if (key === 'c' && X.universe) lines.push({ name: 'Universe', v: X.universe.c, dim: 1 });
      const missing = st.sel.filter(r => !coByRid.has(r)).map(r => (byRid.get(r) || {}).t);
      $('ix-title').textContent = 'Composite Evidence Index' + (st.sel.length ? '' : st.sec ? ' · ' + st.sec : ' · by sector');
      $('ix-note').textContent = (missing.length ? `Not enough scored evidence to index: ${missing.join(', ')}. ` : '') + (key === 'x' ? '0 = as positive as the whole universe that week.' : 'Range −100 to +100; most evidence skews positive, so compare against the universe line.');
      const W = 900, H = 240, L = 36, R = 8, T = 10, B = 22;
      const vals = lines.flatMap(l => l.v.slice(startIx)).filter(v => v != null);
      if (!vals.length) { $('ix-chart').innerHTML = none('No index values for this selection.'); $('ix-legend').innerHTML = ''; return; }
      let lo = Math.min(0, ...vals), hi = Math.max(0, ...vals); const pad = (hi - lo) * 0.08 || 5; lo -= pad; hi += pad;
      const x = i => L + (W - L - R) * (ds.length > 1 ? i / (ds.length - 1) : 0.5), y = v => T + (H - T - B) * (1 - (v - lo) / (hi - lo));
      let svg = `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Composite Evidence Index">`;
      const step = Math.pow(10, Math.floor(Math.log10(Math.max(1, hi - lo)))) / (hi - lo > 50 ? 1 : 2);
      for (let g = Math.ceil(lo / step) * step; g <= hi; g += step) svg += `<line x1="${L}" x2="${W - R}" y1="${y(g).toFixed(1)}" y2="${y(g).toFixed(1)}" stroke="var(--rule)" stroke-width="${g === 0 ? 1.5 : 1}"/><text x="${L - 4}" y="${(y(g) + 3).toFixed(1)}" text-anchor="end">${Math.round(g)}</text>`;
      ds.forEach((d, i) => { if (i % Math.ceil(ds.length / 8) === 0) svg += `<text x="${x(i).toFixed(1)}" y="${H - 6}" text-anchor="middle">${fmtD(d)}</text>`; });
      lines.forEach((l, li) => {
        const col = l.dim ? 'var(--muted, #7a8599)' : PAL[li % PAL.length];
        const pts = l.v.slice(startIx).map((v, i) => v == null ? null : `${x(i).toFixed(1)},${y(v).toFixed(1)}`).filter(Boolean).join(' ');
        const lv = l.v[l.v.length - 1];
        svg += `<polyline points="${pts}" fill="none" stroke="${col}" stroke-width="${l.dim ? 1.5 : 2}"${l.dim ? ' stroke-dasharray="4 3"' : ''}><title>${esc(l.name)}: ${sgn(lv)}</title></polyline>`;
      });
      $('ix-chart').innerHTML = svg + '</svg>';
      $('ix-legend').innerHTML = lines.map((l, li) => `<span><i style="background:${l.dim ? 'var(--muted, #7a8599)' : PAL[li % PAL.length]}"></i>${esc(l.name)} <b class="mono">${sgn(l.v[l.v.length - 1])}</b></span>`).join('');
    }
    // ---- leaderboard ----
    function drawBoard() {
      const n = dates.length - 1, back = Math.max(0, n - 4);
      const list = cos.filter(c => (st.sel.length ? st.sel.includes(c.rid) : inScope(c))).map(c => ({ ...c, d30: c.c[n] - c.c[back] })).sort((a, b) => b.c[n] - a.c[n]);
      $('lb-count').textContent = `${list.length} companies indexed (≥5 scored datapoints)`;
      $('lb-body').innerHTML = list.slice(0, G.n || 150).map(c => `<tr><td>${tk(c.t)} <span class="sub">${esc(c.n || '')}</span></td><td class="sub">${esc(c.sub || c.sec)}</td><td class="n mono">${sgn(c.c[n])}</td><td class="n mono ${c.x[n] >= 0 ? 'c-pos' : 'c-neg'}">${sgn(c.x[n])}</td><td class="n mono ${c.d30 >= 0 ? 'c-pos' : 'c-neg'}">${sgn(c.d30)}</td><td class="n mono">${sgn(c.g[n])}</td><td class="n mono">${sgn(c.m[n])}</td><td class="n mono">${sgn(c.k[n])}</td><td class="n mono">${sgn(c.r[n])}</td><td class="n">${c.e[n]}</td><td>${st.sel.includes(c.rid) ? '' : `<button type="button" class="btn lb-add" data-r="${c.rid}" aria-label="Chart ${esc(c.t)}">Chart</button>`}</td></tr>`).join('') || `<tr><td colspan="11" class="nores">No indexed companies in this selection.</td></tr>`;
    }
    $('lb-body').addEventListener('click', e => { const b = e.target.closest('.lb-add'); if (b) add(b.dataset.r); });
    // ---- rows (lazy) ----
    let ROWS = null, SRC = [];
    const DIR = { 1: ['positive', 'pos'], '-1': ['negative', 'neg'], 0: ['mixed', 'mix'] };
    function drawRows() {
      const body = $('dp-body'), more = $('dp-more');
      if (!ROWS) return;
      const cutoff = new Date(new Date(X.as_of + 'T12:00:00') - st.range * 864e5).toISOString().slice(0, 10);
      const sel = new Set(st.sel);
      const list = ROWS.filter(r => {
        if (r[2] < cutoff) return false;
        const m = byRid.get(r[1]); if (!m) return false;
        if (sel.size ? !sel.has(r[1]) : !inScope(m)) return false;
        if (st.pil && FIELD_PIL(r[3]) !== st.pil) return false;
        if (st.stype && r[6] !== st.stype) return false;
        if (st.imp === 'pos' && r[4] !== 1) return false; if (st.imp === 'neg' && r[4] !== -1) return false; if (st.imp === 'mix' && r[4] !== 0) return false;
        if (st.q && !r[9].toLowerCase().includes(st.q)) return false;
        return true;
      });
      $('dp-count').textContent = list.length.toLocaleString() + ' rows';
      if (G.n && st.shown === 100) st.shown = Math.min(G.n, 100000);
      body.innerHTML = list.length ? list.slice(0, st.shown).map(r => { const m = byRid.get(r[1]) || {}, d = DIR[r[4]]; return `<tr><td class="mono">${fmtD(r[2])}</td><td>${tk(m.t)}</td><td class="sub">${esc(r[3])}</td><td>${d ? `<span class="chip ${d[1] === 'pos' ? 'up' : d[1] === 'neg' ? 'dn' : ''}">${d[0]}</span>` : ''}</td><td class="ev-wrap">${esc(r[9])}</td><td class="sub ev-src">${esc(SRC[r[7]] || '')}${r[6] ? ` <span class="chip out">${esc(r[6])}</span>` : ''}</td></tr>`; }).join('')
        : `<tr><td colspan="6" class="nores">No datapoints match. Widen the range or clear a filter.</td></tr>`;
      more.hidden = list.length <= st.shown;
    }
    function load() {
      getDP().then(o => {
        SRC = o.SRC; ROWS = o.ROWS;
        const types = [...new Set(ROWS.map(r => r[6]).filter(Boolean))].sort();
        $('dp-st').innerHTML = `<option value="">All</option>${types.map(t => `<option>${esc(t)}</option>`).join('')}`;
        drawRows();
      }).catch(() => { $('dp-body').innerHTML = `<tr><td colspan="6" class="nores">The datapoint files did not load. Reload the page; the index above is unaffected.</td></tr>`; });
    }
    function drawAll() { drawChart(); drawBoard(); drawRows(); }
    fillSubs(); chips(); drawAll(); load();
  }

  // ================= SCREENS =================
  function table(rows, cols) {
    rows = lim(rows); if (!rows.length) return none('Nothing in the latest run.');
    return `<div class="tbl-wrap"><table class="dt"><thead><tr>${cols.map(c => `<th${c.n ? ' class="n"' : ''}>${c.h}</th>`).join('')}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(c => {
      const v = typeof c.f === 'function' ? c.f(r) : esc(r[c.k]);
      return `<td class="${c.n ? 'n ' + numCls(r[c.k]) : ''}${c.w ? ' wrap' : ''}">${v == null ? '' : v}</td>`; }).join('')}</tr>`).join('')}</tbody></table></div>`;
  }
  const tkCol = { h: 'Ticker', f: r => tk(r.ticker) + (r.company ? ` <span class="sub">${esc(r.company)}</span>` : '') + valLine(r.ticker, true) };
  function renderScreens() {
    const rv = SC.revisions || {}, cp = SC.comps || {};
    const callouts = arr(rv.callouts);
    document.getElementById('v-screens').innerHTML =
      head('Consensus revisions · comps screen', 'Estimates &amp; screens', 'Where Street numbers moved over the last four weeks, how the stocks reacted, and the long and short candidates from the Master comps screen.') +
      `<section class="panel"><div class="panel-h"><h2>Consensus revisions</h2><span class="muted">${rv.date ? 'Run ' + fmtD(rv.date) : ''}${rv.as_of ? ' · Source: ' + esc(rv.as_of) : ''} ${link(rv.url, 'Notion')}</span></div>` +
      (callouts.length ? `<div class="list">${callouts.map(c => `<div class="li"><span class="stripe inf"></span><div class="body">${attr(c)}</div></div>`).join('')}</div>` : '') +
      `<div class="grid2"><div><h3 style="margin-bottom:6px">Revised up most</h3>${table(rv.top_up, [tkCol, { h: 'Rev rev', k: 'rev_rev', n: 1 }, { h: 'EPS rev', k: 'eps_rev', n: 1 }, { h: 'Period', k: 'period' }, { h: '30D perf', k: 'perf', n: 1 }])}</div>` +
      `<div><h3 style="margin-bottom:6px">Revised down most</h3>${table(rv.top_down, [tkCol, { h: 'Rev rev', k: 'rev_rev', n: 1 }, { h: 'EPS rev', k: 'eps_rev', n: 1 }, { h: 'Period', k: 'period' }, { h: '30D perf', k: 'perf', n: 1 }])}</div></div>` +
      `<h3>Estimates vs price disconnects</h3>${table(rv.disconnects, [tkCol, { h: 'Type', k: 'type' }, { h: 'Est', k: 'est', n: 1 }, { h: 'Perf', k: 'perf', n: 1 }, { h: 'Note', k: 'note', w: 1 }])}` +
      (arr(rv.sectors).length ? `<h3>By sector</h3>${table(rv.sectors, [{ h: 'Sector', k: 'sector' }, { h: 'Names', k: 'n', n: 1 }, { h: 'Median rev', k: 'median_rev', n: 1 }, { h: 'Median perf', k: 'median_perf', n: 1 }, { h: 'Note', k: 'note', w: 1 }])}` : '') + `</section>` +
      (!cp.url ? `<section class="panel"><div class="panel-h"><h2>Comps screen</h2></div>${none('No comps-screen run has been published yet. Run "comps screen" and the long and short candidates, PEG screens and movers will appear here.')}</section>` :
      `<section class="panel"><div class="panel-h"><h2>Comps screen</h2><span class="muted">${cp.date ? 'Run ' + fmtD(cp.date) : ''}${cp.as_of ? ' · Source: ' + esc(cp.as_of) : ''} ${link(cp.url, 'Notion')}</span></div>` +
      `<div class="grid2"><div><h3 style="margin-bottom:6px" class="c-pos">Long candidates</h3>${table(cp.longs, [tkCol, { h: 'Score', k: 'score', n: 1 }, { h: 'Why', f: r => esc(r.why) + (arr(r.screens).length ? `<div class="chips" style="margin-top:3px">${arr(r.screens).map(s => `<span class="chip">${esc(s)}</span>`).join('')}</div>` : ''), w: 1 }])}</div>` +
      `<div><h3 style="margin-bottom:6px" class="c-neg">Short candidates</h3>${table(cp.shorts, [tkCol, { h: 'Score', k: 'score', n: 1 }, { h: 'Why', f: r => esc(r.why) + (arr(r.screens).length ? `<div class="chips" style="margin-top:3px">${arr(r.screens).map(s => `<span class="chip">${esc(s)}</span>`).join('')}</div>` : ''), w: 1 }])}</div></div>` +
      `<div class="grid2"><div><h3 style="margin-bottom:6px">PEG cheap</h3>${table(cp.peg_cheap, [tkCol, { h: 'PEG', k: 'peg', n: 1 }, { h: 'P/E', k: 'pe', n: 1 }, { h: 'Growth', k: 'growth', n: 1 }, { h: 'Note', k: 'note', w: 1 }])}</div>` +
      `<div><h3 style="margin-bottom:6px">PEG expensive</h3>${table(cp.peg_expensive, [tkCol, { h: 'PEG', k: 'peg', n: 1 }, { h: 'P/E', k: 'pe', n: 1 }, { h: 'Growth', k: 'growth', n: 1 }, { h: 'Note', k: 'note', w: 1 }])}</div></div>` +
      (arr(cp.movers_7d).length ? `<h3>Biggest 7-day movers</h3>${table(cp.movers_7d, [tkCol, { h: 'Move', k: 'move', n: 1 }, { h: 'Note', k: 'note', w: 1 }])}` : '') + `</section>`) +
      (arr(SC.history).length ? `<section class="panel"><h2>Earlier runs</h2><div class="list">${arr(SC.history).map(h => `<div class="li"><div class="body"><b>${esc(sk(h.skill))}</b> · ${esc(h.title)}</div><div class="side">${fmtD(h.date)} ${link(h.url, 'Notion')}</div></div>`).join('')}</div></section>` : '');
  }

  // ================= IDEAS & CYCLE =================
  function renderIdeas() {
    const ideas = lim(arr(ID.ideas).filter(i => inWin(i.date, null))), theses = lim(arr(ID.theses).filter(t => inWin(t.updated || t.date, null))), cycles = arr(ID.cycles), oc = lim(arr(ID.opcomps).filter(o => inWin(o.date, null)));
    const dir = d => { const s = String(d || '').toLowerCase(); return ['long', 'short', 'pair', 'watch'].find(k => s.includes(k)) || 'watch'; };
    document.getElementById('v-ideas').innerHTML =
      head('Pipeline · idea generator · digests · thesis builder · industry cycle', 'Pipeline, ideas &amp; themes', 'The names we are tracking, new single-stock ideas and the themes behind them in one place. Filter by type, direction and bucket.') +
      `<div class="ctl" role="group" aria-label="Show"><div class="seg" id="it-type"><button type="button" data-v="" aria-pressed="true">Everything</button><button type="button" data-v="pipeline" aria-pressed="false">Pipeline</button><button type="button" data-v="ideas" aria-pressed="false">New ideas</button><button type="button" data-v="themes" aria-pressed="false">Themes</button><button type="button" data-v="more" aria-pressed="false">Theses, cycle &amp; comps</button></div>
        <div class="seg" id="it-dir"><button type="button" data-v="" aria-pressed="true">Longs &amp; shorts</button><button type="button" data-v="long" aria-pressed="false">Longs</button><button type="button" data-v="short" aria-pressed="false">Shorts</button></div>
        <label for="it-q">Search <input type="search" id="it-q" placeholder="Ticker or word"></label></div>` +
      `<div id="pl-host" data-it="pipeline"></div><section class="panel" id="id-ideas" data-it="ideas"></section><div id="th-host" data-it="themes"></div>` +
      `<section class="panel" data-it="more"><div class="panel-h"><h2>Industry cycle</h2></div>${cycles.length ? `<div class="grid3">${cycles.map(c =>
        `<article class="idea"><div class="top"><b>${esc(c.industry)}</b>${c.phase ? `<span class="chip phase">${esc(c.phase)}</span>` : ''}${link(c.url, fmtD(c.date))}</div><dl class="kv">${c.margin_vs_peak ? `<dt>Margin vs peak</dt><dd>${esc(c.margin_vs_peak)}</dd>` : ''}${c.valuation ? `<dt>Valuation</dt><dd>${esc(c.valuation)}</dd>` : ''}</dl>${arr(c.signals).length ? `<ul class="b">${arr(c.signals).map(s => `<li>${attr(s)}</li>`).join('')}</ul>` : ''}${srcLine(c)}</article>`).join('')}</div>` : none('No industry-cycle output found since September.')}</section>` +
      `<section class="panel" data-it="more"><div class="panel-h"><h2>Theses</h2><span class="muted">${theses.length} · dated by last edit</span></div>${theses.length ? `<div class="list">${theses.map(t =>
        `<div class="li"><div class="body">${tk(t.ticker)} <b>${esc(t.company)}</b> ${t.stance ? `<span class="chip dir-${dir(t.stance)}">${esc(t.stance)}</span>` : ''}<div>${esc(t.summary)}</div>${srcLine(t)}${arr(t.tenets).length ? `<details><summary>Tenets</summary><ul class="b">${arr(t.tenets).map(x => `<li>${esc(x)}</li>`).join('')}</ul>${t.what_would_change ? `<p class="sub" style="margin:6px 0 0">What would change it: ${esc(t.what_would_change)}</p>` : ''}</details>` : ''}</div><div class="side">${fmtD(t.updated)} ${link(t.url, 'Notion')}</div></div>`).join('')}</div>` : none('No thesis-builder output found since September.')}</section>` +
      `<section class="panel" data-it="more"><div class="panel-h"><h2>Operating comps</h2></div>${oc.length ? `<div class="grid2">${oc.map(o =>
        `<article class="idea"><div class="top"><b>${esc(o.title)}</b>${link(o.url, fmtD(o.date))}</div>${o.peer_set ? `<div class="sub">${esc(o.peer_set)}</div>` : ''}<ul class="b">${arr(o.findings).map(f => `<li>${attr(f)}</li>`).join('')}</ul>${srcLine(o)}</article>`).join('')}</div>` : none('No operating-comps output found since September.')}</section>`;
    // ---- ideas: longs and shorts, filtered by idea-generator bucket ----
    const bucketOf = i => { const c = String(i.conviction || ''); return /most exciting|amazing/i.test(c) ? 'amazing' : /contrarian/i.test(c) ? 'contrarian' : /good/i.test(c) ? 'good' : /callout/i.test(c) ? 'callout' : 'other'; };
    const BL = { amazing: 'Amazing', contrarian: 'Contrarian', good: 'Good', callout: 'Callout', other: 'Other' };
    const ist = { b: '', dir: '', q: '' };
    const card = i => `<article class="idea"><div class="top">${tk(i.ticker)}<b>${esc(i.company)}</b>${noteUI('idea:' + ntKey(i.ticker) + '|' + (i.date || ''), i.ticker, (i.company || i.ticker) + ' idea')}<span class="chip b-${bucketOf(i)}">${BL[bucketOf(i)]}</span>${i.conviction ? `<span class="chip out">${esc(i.conviction)}</span>` : ''}${link(i.url, fmtD(i.date))}</div><p><b>${esc(i.idea)}</b></p>${i.why_now ? `<p>${esc(i.why_now)}</p>` : ''}${arr(i.catalysts).length ? `<div class="sub">Catalysts: ${arr(i.catalysts).map(esc).join(' · ')}</div>` : ''}${arr(i.risks).length ? `<div class="sub">Risks: ${arr(i.risks).map(esc).join(' · ')}</div>` : ''}${srcLine(i)}</article>`;
    function drawIdeas() {
      const xs = ideas.filter(i => (!ist.b || bucketOf(i) === ist.b) && (!ist.dir || dir(i.direction) === ist.dir) && (!ist.q || `${i.ticker} ${i.company} ${i.idea} ${i.why_now}`.toLowerCase().includes(ist.q)));
      const L = xs.filter(i => dir(i.direction) === 'long'), S = xs.filter(i => dir(i.direction) === 'short'), P = xs.filter(i => !['long', 'short'].includes(dir(i.direction)));
      const counts = b => ideas.filter(i => !b || bucketOf(i) === b).length;
      const col = (title, cls, ys) => `<div><div class="panel-h"><h3 class="${cls}">${title}</h3><span class="muted">${ys.length}</span></div>${ys.length ? `<div class="id-col">${ys.map(card).join('')}</div>` : none('None in this filter.')}</div>`;
      document.getElementById('id-ideas').innerHTML = `<div class="panel-h"><h2>Ideas</h2><div class="seg" id="id-b">${['', 'amazing', 'contrarian', 'good', 'callout'].map(b => `<button type="button" data-v="${b}" aria-pressed="${ist.b === b}">${b ? BL[b] : 'All'} <span class="sub">${counts(b)}</span></button>`).join('')}</div></div>` +
        (ideas.length ? `<div class="grid2">${col('Longs', 'c-pos', L)}${col('Shorts', 'c-neg', S)}</div>${P.length ? col('Pairs & other', '', P) : ''}` : none('No idea-generator output found in this window.'));
      document.querySelectorAll('#id-b button').forEach(btn => btn.addEventListener('click', () => { ist.b = btn.dataset.v; drawIdeas(); }));
    }
    drawIdeas();
    renderPipeline();
    renderThemes();
    const vI = document.getElementById('v-ideas');
    const applyType = v => vI.querySelectorAll('[data-it]').forEach(el => { el.style.display = v && el.dataset.it !== v ? 'none' : ''; });
    vI.querySelectorAll('#it-type button').forEach(b => b.addEventListener('click', () => { vI.querySelectorAll('#it-type button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); applyType(b.dataset.v); }));
    vI.querySelectorAll('#it-dir button').forEach(b => b.addEventListener('click', () => { vI.querySelectorAll('#it-dir button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); ist.dir = b.dataset.v; drawIdeas(); const pb = vI.querySelector('#pl-dir button[data-v="' + b.dataset.v + '"]'); if (pb) pb.click();
      vI.querySelectorAll('#th-host .theme').forEach(el => { const w = el.querySelector('.wl'); el.style.display = ist.dir && !(w && w.innerHTML.includes(ist.dir === 'long' ? 'Benefits' : 'Hurt')) ? 'none' : ''; }); }));
    document.getElementById('it-q').addEventListener('input', e => { ist.q = e.target.value.trim().toLowerCase(); drawIdeas(); const pq = document.getElementById('pl-q'); if (pq) { pq.value = e.target.value; pq.dispatchEvent(new Event('input')); } const tq = document.getElementById('th-q'); if (tq) { tq.value = e.target.value; tq.dispatchEvent(new Event('input')); } });
  }

  // ================= PREP =================
  function renderPrep() {
    const up = lim(arr(PR.upcoming).filter(u => { const a = ageDays(u.date); return G.days ? (a == null || -a <= winDays(28)) : true; }).sort((a, b) => String(a.date).localeCompare(String(b.date))));
    const prep = arr(PR.prep).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)));
    const types = [...new Set(prep.map(p => p.type).filter(Boolean))];
    const byDay = new Map(); up.forEach(u => { const k = String(u.date).slice(0, 10); if (!byDay.has(k)) byDay.set(k, []); byDay.get(k).push(u); });
    const host = document.getElementById('v-prep');
    host.innerHTML = head('Management prep · analyst day · print tables · quarterly review', 'Prep &amp; calendar', 'What reports next in your coverage, and the prep you have already built for each company.') +
      `<section class="panel"><div class="panel-h"><h2>Upcoming prints</h2><span class="muted">${up.length} in the next four weeks · Source: ${esc((up[0] || {}).source || 'FactSet calendar')}</span></div>${up.length ? `<div class="cal">${[...byDay].map(([d, xs]) =>
        `<div class="cal-day"><div class="dd">${fmtDW(d)}<span>${xs.length} print${xs.length > 1 ? 's' : ''}</span></div><div class="list">${xs.map(u =>
          `<div class="li" style="padding:4px 0;border:0"><div class="body">${tk(u.ticker)} <b>${esc(u.company)}</b>${u.time ? ` <span class="sub">${esc(u.time)}</span>` : ''}${u.tier ? ` <span class="chip out">Tier ${esc(u.tier)}</span>` : ''}${u.date_status === 'projected' ? ` <span class="chip a-split" title="FactSet projected date, not confirmed">Projected date</span>` : ''}${u.bogeys ? `<div class="sub">${esc(u.bogeys)}</div>` : ''}</div>${u.preview_url ? `<div class="side">${link(u.preview_url, 'Preview')}</div>` : ''}</div>`).join('')}</div></div>`).join('')}</div>` : none('No upcoming prints in the snapshot.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2>Company prep</h2><div class="seg" id="pp-type"><button type="button" data-v="" aria-pressed="true">All</button>${types.map(t => `<button type="button" data-v="${esc(t)}" aria-pressed="false">${esc(t)}</button>`).join('')}</div></div><div id="pp-list"></div></section>`;
    let cur = '';
    const draw = () => {
      const xs = lim(prep.filter(p => (!cur || p.type === cur) && inWin(p.date, null)));
      document.getElementById('pp-list').innerHTML = xs.length ? `<div class="grid2">${xs.map(p =>
        `<article class="idea"><div class="top">${tk(p.ticker)}<b>${esc(p.company)}</b><span class="chip">${esc(p.type)}</span>${link(p.url, fmtD(p.date))}</div>${srcLine(p, 'Built from')}${arr(p.key_points).length ? `<ul class="b">${arr(p.key_points).map(k => `<li>${attr(k)}</li>`).join('')}</ul>` : ''}${arr(p.questions).length ? `<details><summary>Questions to ask</summary><ul class="b">${arr(p.questions).map(k => `<li>${esc(k)}</li>`).join('')}</ul></details>` : ''}</article>`).join('')}</div>` : none('No prep outputs found since September.');
    };
    host.querySelectorAll('#pp-type button').forEach(b => b.addEventListener('click', () => { cur = b.dataset.v; host.querySelectorAll('#pp-type button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); draw(); }));
    draw();
  }

  // ================= HEALTH =================
  function renderHealth() {
    const runs = [].concat(arr(TODAY.runs), arr(SC.runs), arr(ID.runs), arr(PR.runs));
    arr(D.bobby).forEach(b => runs.push({ skill: 'earnings-preview', date: b.report_date, title: b.title, url: b.url }));
    arr(D.rebecca).forEach(r => runs.push({ skill: 'earnings-recap', date: r.report_date, title: r.title, url: r.url }));
    const bySrc = arr(DP.by_source);
    const groups = [
      ['Daily digests', ['morning', 'research-folder-digest', 'tech-email-digest-new', 'semianalysis-digest', 'analyst-folder-extractor', 'alphasense-digest', 'sellside-folder-digest']],
      ['Earnings', ['earnings-preview', 'earnings-recap', 'print-tables', 'quarterly-review']],
      ['Screens and models', ['consensus-revisions', 'comps-screen', 'industry-cycle', 'operating-comps']],
      ['Ideas and prep', ['idea-generator', 'thesis-builder', 'management-prep', 'analyst-day']]
    ];
    const row = s => {
      const rs = runs.filter(r => r.skill === s && r.date).sort((a, b) => String(b.date).localeCompare(String(a.date)));
      const last = rs[0]; const a = last ? ageDays(last.date) : null;
      const n30 = rs.filter(r => ageDays(r.date) <= 30).length;
      return `<tr><td><b>${esc(sk(s))}</b> <span class="sub mono">${esc(s)}</span></td><td><span class="chips"><i class="dot ${fresh(a)}"></i>${last ? fmtD(last.date) + ` <span class="sub">(${a === 0 ? 'today' : a + 'd ago'})</span>` : '<span class="sub">No output found</span>'}</span></td><td class="n">${n30}</td><td class="wrap">${last ? link(last.url, esc(last.title || 'Latest')) : ''}</td></tr>`;
    };
    const ondemand = ['alphasense', 'srs-documents', 'va-financials', 'deep-research', 'datapoint-organizer', 'datapoint-filter', 'notion-cleaner', 'apps-dashboarding', 'xlsx', 'pptx', 'docx', 'pdf'];
    document.getElementById('v-health').innerHTML = head('Skill health', 'When each skill last published', 'Green ran in the last two days, amber in the last week, red longer ago. Grey means no output was found.') +
      groups.map(([g, ss]) => `<section class="panel" style="padding:0"><div class="panel-h" style="padding:14px 16px 0"><h2>${g}</h2></div><div class="tbl-wrap"><table class="dt"><thead><tr><th>Skill</th><th>Last output</th><th class="n">Runs 30d</th><th>Latest</th></tr></thead><tbody>${ss.map(row).join('')}</tbody></table></div></section>`).join('') +
      `<section class="panel" style="padding:0"><div class="panel-h" style="padding:14px 16px 0"><h2>Supabase loads by source type</h2><span class="muted">research_evidence</span></div>${bySrc.length ? `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Source type</th><th>Last row</th><th class="n">Rows 30d</th></tr></thead><tbody>${bySrc.map(b => { const a = ageDays(b.last); return `<tr><td class="mono">${esc(b.source_type)}</td><td><span class="chips"><i class="dot ${fresh(a)}"></i>${fmtD(b.last)}</span></td><td class="n">${esc(b.n_30d)}</td></tr>`; }).join('')}</tbody></table></div>` : `<div style="padding:0 16px 16px">${none('No load history in the snapshot.')}</div>`}</section>` +
      `<section class="panel"><h2>On-demand tools</h2><p class="lede" style="font-size:13px">These skills answer one-off requests or support the skills above, so they have no output page to track.</p><div class="chips">${ondemand.map(s => `<span class="chip mono">${esc(s)}</span>`).join('')}</div></section>`;
  }

  // ---- shared loader for the datapoint rows (dp/part*.json), used by Datapoints and Stocks ----
  let DPP = null;
  function getDP() {
    if (DPP) return DPP;
    const X = D.dp_index || {}, n = +X.parts || 0, get = p => fetch(p).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
    DPP = Promise.all([get('dp/sources.json')].concat(Array.from({ length: n }, (_, i) => get(`dp/part${i + 1}.json`)))).then(([s, ...ps]) => ({ SRC: arr(s.sources), ROWS: ps.flatMap(p => arr(p.rows)) }));
    DPP.catch(() => { DPP = null; });
    return DPP;
  }

  // ================= STOCKS: one page per Tier 1-2 company =================
  /* stock-deep v1 */
  const SDP = { docs: {}, started: false, err: '' };
  function sdStart() {
    if (SDP.started) return; SDP.started = true;
    (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => {
      if (!db) return;
      db.collection('stock_deep').onSnapshot(snap => {
        SDP.docs = {}; snap.docs.forEach(d => { SDP.docs[String(d.id).toUpperCase()] = JSON.parse(JSON.stringify(d.data())); });
        if ((location.hash || '').startsWith('#stocks/')) renderStocks();
      }, () => { SDP.err = 'The deep-dive tabs could not be read from this page’s database.'; });
    }).catch(() => {});
  }
  const sdDoc = cur => cur ? (SDP.docs[String(cur.t).toUpperCase()] || SDP.docs[String(cur.bbg || '').toUpperCase()] || null) : null;
  const sdTabs = cur => { const d = sdDoc(cur); return d ? arr(d.tabs).map(t => ['dd-' + t.key, t.label]) : []; };
  // block html was escaped by the builder (bold and http links only); anything else is escaped here
  function sdBlocks(bs) {
    return arr(bs).map(b => {
      if (b.k === 'h') return `<h3>${b.h}</h3>`;
      if (b.k === 'p') return `<p class="sd-p">${b.h}</p>`;
      if (b.k === 'note') return `<p class="tn-view">${b.h}</p>`;
      if (b.k === 'ul') return `<ul class="b sd-ul">${arr(b.items).map(i => `<li class="sd-d${Math.min(+i.d || 0, 3)}">${i.h}</li>`).join('')}</ul>`;
      if (b.k === 'table') return `<div class="tbl-wrap"><table class="dt sd-t"><thead><tr>${arr(b.cols).map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>${arr(b.rows).map(r => `<tr>${arr(r).map(c => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
      if (b.k === 'toggle') return `<details class="fr-sec sd-tog"><summary>${b.title}</summary><div class="sd-in">${sdBlocks(b.b)}</div></details>`;
      return '';
    }).join('');
  }
  function sdView(cur, sub, host) {
    const d = sdDoc(cur), t = d && arr(d.tabs).find(x => 'dd-' + x.key === sub);
    if (!t) { host.innerHTML = `<section class="panel">${none('This tab has no content yet.')}</section>`; return; }
    const src = d.source || {}, asOf = d.as_of || '';
    host.innerHTML = `<section class="panel sd"><div class="panel-h"><h2>${esc(t.label)}</h2><span class="muted">${src.url ? `<a class="ext" href="${esc(src.url)}" target="_blank" rel="noopener">Notion: ${esc(d.title || 'deep dive')}</a>` : esc(d.title || '')}${asOf ? ` · as of ${esc(fmtD(asOf))}` : ''}</span></div>${sdBlocks(t.blocks)}</section>` +
      `<section class="panel"><div class="panel-h"><h2>Latest datapoints</h2><span class="muted" id="sd-dpn">Supabase, newest first</span></div><div class="list" id="sd-dp"><p class="sub">Loading…</p></div></section>`;
    getDP().then(({ SRC, ROWS }) => {
      const box = document.getElementById('sd-dp'); if (!box) return;
      let rx; try { rx = new RegExp(t.dp_rx || '.', 'i'); } catch (e) { rx = /./; }
      const rs = new Set(cur.rids), xs = ROWS.filter(r => rs.has(r[1]) && rx.test(String(r[9] || ''))).sort((a, b) => String(b[2]).localeCompare(String(a[2]))).slice(0, 25);
      const nw = xs.filter(r => asOf && String(r[2]) > asOf).length;
      box.innerHTML = xs.length ? xs.map(r => { const h = rowHtml(r, SRC); return asOf && String(r[2]) > asOf ? h.replace('<span class="mono sub">', '<span class="chip x-nchip">new since page</span> <span class="mono sub">') : h; }).join('') : none('No matching datapoints.');
      const n = document.getElementById('sd-dpn'); if (n) n.textContent = `Supabase, newest first · ${xs.length} shown${nw ? ` · ${nw} newer than the Notion page` : ''}`;
    }).catch(() => { const box = document.getElementById('sd-dp'); if (box) box.innerHTML = none('The datapoint files did not load.'); });
  }
  function renderStocks() {
    sdStart();
    const ST = arr((D.stocks || {}).companies), host = document.getElementById('v-stocks');
    const parts = (location.hash || '').split('/'), key = decodeURIComponent(parts[1] || ''), sub = parts[2] || 'debate';
    const cur = ST.find(c => c.key === key) || null;
    const ix = new Map(arr((D.dp_index || {}).companies).map(c => [c.rid, c]));
    const PL = new Map(arr((D.pipeline || {}).items).map(p => [String(p.ticker).toUpperCase(), p]));
    const TH = new Map(arr(ID.theses).map(t => [String(t.ticker).toUpperCase(), t]));
    const MV = new Map(arr(DLY.moves).map(m => [String(m.t).toUpperCase(), m]));
    const sgn = v => v == null || !isFinite(v) ? '' : (v > 0 ? '+' : '') + (+v).toFixed(1);
    const idxOf = c => { const xs = c.rids.map(r => ix.get(r)).filter(Boolean); return xs.sort((a, b) => b.count - a.count)[0]; };
    if (!host.__st) host.__st = { q: '', tier: '', sec: '', sub: '', sort: '', dir: 'desc', flt: '', minN: '' };
    const fs = host.__st;
    /* stock-scores v1 */
    const SKM = c => { const I = idxOf(c); if (!I) return null; const n = I.c.length - 1, mv = MV.get(String(c.t).toUpperCase()) || MV.get(String(c.bbg).toUpperCase()); return { x: I.x[n], c: I.c[n], d30: I.c[n] - I.c[Math.max(0, n - 4)], g: I.g[n], m: I.m[n], k: I.k[n], r: I.r[n], e: I.e[n], cnt: I.count, mv: mv ? +mv.c : null }; };
    const SK_COLS = [['x', 'vs universe', 'Composite index minus the same index on every name: 0 = as positive as the average name'], ['c', 'Index', 'Composite Evidence Index, −100 to +100'], ['d30', '30d Δ', 'Change in the index over the last 4 weeks'], ['g', 'Growth', 'Growth pillar (40% of the index)'], ['m', 'Margins', 'Margins pillar (25%)'], ['k', 'Competition', 'Competition pillar (20%)'], ['r', 'Risk', 'Risk pillar (15%)'], ['e', 'Evidence 90d', 'Datapoints in the last 90 days that feed the index'], ['mv', 'Today %', 'Today’s price move']];
    const skVal = (c, k) => { const m = SKM(c); return m ? m[k] : null; };
    const skPass = c => { const m = SKM(c); if (fs.flt === 'noidx') return !m; if (fs.flt && !m) return false;
      if (fs.flt === 'above' && !(m.x > 0)) return false; if (fs.flt === 'below' && !(m.x < 0)) return false;
      if (fs.flt === 'rising' && !(m.d30 > 0)) return false; if (fs.flt === 'falling' && !(m.d30 < 0)) return false;
      if (fs.minN && !(m && m.e >= +fs.minN)) return false; return true; };
    const skCmp = (a, b) => { const va = skVal(a, fs.sort), vb = skVal(b, fs.sort); if (va == null && vb == null) return a.t.localeCompare(b.t); if (va == null) return 1; if (vb == null) return -1; return fs.dir === 'asc' ? va - vb : vb - va; };
    const SO = ['Semis', 'Hardware', 'Power & DC infra', 'Software', 'Internet', 'IT Services', 'Other'];
    const secs = SO.filter(x => ST.some(c => c.sector === x));
    const subsAll = [...new Set(ST.filter(c => !fs.sec || c.sector === fs.sec).flatMap(c => arr(c.subs)))].sort();
    const list = ST.filter(c => (!fs.tier || String(c.tier) === fs.tier) && (!fs.sec || c.sector === fs.sec) && (!fs.sub || arr(c.subs).includes(fs.sub)) && (!fs.q || `${c.t} ${c.name} ${c.sub}`.toLowerCase().includes(fs.q)) && skPass(c))
      .sort((a, b) => fs.sort ? skCmp(a, b) : SO.indexOf(a.sector) - SO.indexOf(b.sector) || String(arr(a.subs)[0]).localeCompare(String(arr(b.subs)[0])) || (a.tier || 9) - (b.tier || 9) || a.t.localeCompare(b.t));
    const nav = `<div class="sk-nav"><input type="search" id="sk-q" placeholder="Search ${ST.length} names" value="${esc(fs.q)}">
      <div class="seg" id="sk-tier"><button type="button" data-v="" aria-pressed="${!fs.tier}">All</button><button type="button" data-v="1" aria-pressed="${fs.tier === '1'}">Tier 1</button><button type="button" data-v="2" aria-pressed="${fs.tier === '2'}">Tier 2</button></div>
      <select id="sk-sec"><option value="">All sectors</option>${secs.map(x => `<option${x === fs.sec ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select>
      <select id="sk-sub"><option value="">All subsectors</option>${subsAll.map(x => `<option${x === fs.sub ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select>
      <div class="sk-ctl2"><label>Sort <select id="sk-sort"><option value=""${!fs.sort ? ' selected' : ''}>Sector</option>${SK_COLS.map(([k, l]) => `<option value="${k}"${fs.sort === k ? ' selected' : ''}>${l}</option>`).join('')}</select></label>${fs.sort ? `<button type="button" class="nav-reset" id="sk-dir" title="Flip the order">${fs.dir === 'asc' ? '↑ low first' : '↓ high first'}</button>` : ''}</div>
      <div class="sk-ctl2"><select id="sk-flt" aria-label="Filter by score"><option value="">All scores</option><option value="above"${fs.flt === 'above' ? ' selected' : ''}>Above universe</option><option value="below"${fs.flt === 'below' ? ' selected' : ''}>Below universe</option><option value="rising"${fs.flt === 'rising' ? ' selected' : ''}>Rising (30d)</option><option value="falling"${fs.flt === 'falling' ? ' selected' : ''}>Falling (30d)</option><option value="noidx"${fs.flt === 'noidx' ? ' selected' : ''}>No index yet</option></select><select id="sk-min" aria-label="Minimum evidence"><option value="">Any evidence</option>${[5, 10, 25, 50].map(v => `<option value="${v}"${fs.minN === String(v) ? ' selected' : ''}>${v}+ in 90d</option>`).join('')}</select></div>
      <a class="sk-rank" href="#stocks">Ranking table · how the score works</a>
      <div class="sub sk-key" title="Composite Evidence Index minus the universe, from your Supabase datapoints: reliability × confidence × recency. 0 = as positive as the average name.">Number = evidence index vs universe (−100 to +100; 0 = average, + more bullish)</div>
      <div class="sk-list">${list.map((c, i) => { const I = idxOf(c), n = I ? I.c.length - 1 : 0, sb = arr(c.subs)[0] || c.sector, hdr = !fs.sort && (i === 0 || (arr(list[i - 1].subs)[0] || list[i - 1].sector) !== sb) ? `<div class="sk-grp">${esc(c.sector)} · ${esc(sb)}</div>` : ''; return hdr + `<a href="#stocks/${encodeURIComponent(c.key)}/${sub}"${cur && c.key === cur.key ? ' aria-current="page"' : ''}><b>${esc(c.t)}</b><span class="sub">${esc(c.name)}</span><span class="chip out">T${esc(c.tier)}</span>${fs.sort && fs.sort !== 'x' ? (() => { const v = skVal(c, fs.sort); return v == null ? '' : `<span class="mono sk-m ${['d30', 'mv'].includes(fs.sort) ? (v >= 0 ? 'c-pos' : 'c-neg') : ''}" title="${esc((SK_COLS.find(x => x[0] === fs.sort) || [])[1] || '')}">${fs.sort === 'e' ? v : sgn(v) + (fs.sort === 'mv' ? '%' : '')}</span>`; })() : I ? `<span class="mono ${I.x[n] >= 0 ? 'c-pos' : 'c-neg'}" title="Composite vs universe">${sgn(I.x[n])}</span>` : ''}</a>`; }).join('')}</div></div>`;
    let body;
    if (!cur) {
      const rows = ST.filter(c => (!fs.tier || String(c.tier) === fs.tier) && (!fs.sec || c.sector === fs.sec) && (!fs.sub || arr(c.subs).includes(fs.sub)) && (!fs.q || `${c.t} ${c.name} ${c.sub}`.toLowerCase().includes(fs.q)) && skPass(c));
      const sk = fs.sort || 'x', dir = fs.sort ? fs.dir : 'desc', S2 = Object.assign({}, fs, { sort: sk, dir });
      rows.sort((a, b) => { const va = skVal(a, sk), vb = skVal(b, sk); if (va == null && vb == null) return a.t.localeCompare(b.t); if (va == null) return 1; if (vb == null) return -1; return dir === 'asc' ? va - vb : vb - va; });
      const cell = (v, k) => v == null ? '<td class="n muted">–</td>' : `<td class="n ${['x', 'd30', 'mv'].includes(k) ? (v >= 0 ? 'up' : 'dn') : ''}">${k === 'e' ? v : k === 'mv' ? sgn(v) + '%' : sgn(v)}</td>`;
      body = `<section class="panel"><div class="panel-h"><h2>Evidence scores</h2><span class="muted">${rows.length} names · click a header to sort · filters on the left apply</span></div>
        <div class="tbl-wrap"><table class="dt sk-rt"><thead><tr><th>Company</th><th>Tier</th><th>Subsector</th>${SK_COLS.map(([k, l, t]) => `<th class="n" data-sk="${k}" title="${esc(t)}" aria-sort="${sk === k ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}">${l}</th>`).join('')}<th class="n" title="All datapoints on file">Total</th></tr></thead>
        <tbody>${rows.map(c => { const m = SKM(c) || {}; return `<tr><td><a href="#stocks/${encodeURIComponent(c.key)}/debate"><b>${esc(c.t)}</b></a> <span class="sub">${esc(c.name)}</span></td><td>T${esc(c.tier)}</td><td class="sub">${esc(arr(c.subs)[0] || c.sector)}</td>${SK_COLS.map(([k]) => cell(m[k] ?? null, k)).join('')}<td class="n">${m.cnt ?? '–'}</td></tr>`; }).join('')}</tbody></table></div></section>
        <section class="panel"><details class="sk-how"><summary>How the score works</summary><div class="method">
        <p><b>Inputs:</b> every Supabase datapoint (research_evidence) on the company whose category is Growth or TAM, Margins, Competition or Risk. Other categories are counted in Total but do not move the score. A company needs 5+ scored datapoints to get an index.</p>
        <ul><li><b>Signal per datapoint</b> = direction (positive +1, negative −1, mixed 0) × confidence (high 1.0, medium 0.75, low 0.5). Size of the news is not scored yet.</li>
        <li><b>Weight</b> = source reliability × recency. Reliability: management, filings and channel checks / independent research 1.0; sell-side 0.6; news, Substack and email 0.5; Twitter 0.3; Reddit 0.2; anything inferred 0.3. Recency halves every 90 days.</li>
        <li><b>Pillar score</b> = weighted average signal, shrunk toward 0 when there is little evidence (× W ÷ (W + 5), W = sum of weights), so a name with a handful of positives cannot score +100.</li>
        <li><b>Index</b> = Growth 40% + Margins 25% + Competition 20% + Risk 15%, × 100 → −100 to +100.</li>
        <li><b>vs universe</b> = the index minus the same calculation on every datapoint in the universe that week. About 75% of stored datapoints are positive (sell-side skew), so the raw index runs high; 0 here means "as positive as the average name".</li>
        <li><b>30d Δ</b> = the index now minus four weeks ago. <b>Evidence 90d</b> = datapoints in the last 90 days.</li></ul>
        <p class="sub">Built nightly from research_evidence by store/build_datapoints.py (Composite Evidence Index v3, after your Hex "Composite Index v2"). Known gaps: no magnitude, duplicate reports of one event each count, and price/valuation are not inputs.</p></div></details></section>`;
    } else if (false) body = `<section class="panel"><h2>Pick a company</h2><p class="sub">Each Tier 1–2 name has six views: the Tech Specialist debate, the thesis tenets, a live Visible Alpha quarterly review, every datapoint organized by its drivers, the earnings-review metrics table, and what management has said over time.</p></section>`;
    else {
      const I = idxOf(cur), n = I ? I.c.length - 1 : 0, pl = PL.get(String(cur.t).toUpperCase()) || PL.get(String(cur.bbg).toUpperCase()), mv = MV.get(String(cur.t).toUpperCase()) || MV.get(String(cur.bbg).toUpperCase());
      const tabs = [['debate', 'Debate'], ['thesis', 'Thesis'], ['qr', 'Quarterly review'], ['kpis', 'KPIs & guidance'], ['datapoints', 'Datapoints'], ['earnings', 'Earnings metrics'], ['management', 'Management'], ['insiders', 'Questions & insiders']]; sdTabs(cur).forEach((x, i) => tabs.splice(2 + i, 0, x));
      body = `<section class="panel sk-head"><div class="panel-h"><div><span class="eyebrow">Tier ${esc(cur.tier)} · ${esc(cur.sector)} · ${esc(cur.sub)}</span><h2 style="margin-top:4px">${tk(cur.t)} ${esc(cur.name)}</h2></div>
        <div class="sk-kpis">${mv ? `<span><span class="sub">Today</span> <b class="mono ${+mv.c >= 0 ? 'c-pos' : 'c-neg'}">${sgn(+mv.c)}%</b></span>` : ''}${I ? `<span><span class="sub">Index</span> <b class="mono">${sgn(I.c[n])}</b></span><span><span class="sub">vs univ.</span> <b class="mono ${I.x[n] >= 0 ? 'c-pos' : 'c-neg'}">${sgn(I.x[n])}</b></span><span><span class="sub">30d Δ</span> <b class="mono">${sgn(I.c[n] - I.c[Math.max(0, n - 4)])}</b></span>` : ''}</div></div>
        ${pl ? `<p class="sk-pitch"><span class="chip ${pl.direction === 'short' ? 'dn' : 'up'}">${esc(pl.direction)}</span> <span class="chip out">${esc(pl.status || '')}</span> ${attr(pl.pitch || '')}${pl.upside && (pl.upside.pct_low != null || pl.upside.pct_high != null) ? ` <b class="mono">${sgn(100 * (pl.upside.pct_high ?? pl.upside.pct_low))}% to target</b>` : ''}</p>` : ''}
        <div class="sk-notes">${noteUI('stock:' + cur.key, cur.t, cur.name)} <span class="sub">Add a note on ${esc(cur.t)}</span><div id="sk-tnotes" data-tk="${esc(ntKey(cur.t))}" data-tk2="${esc(ntKey(cur.bbg))}"></div></div>
        <nav class="sk-tabs">${tabs.map(([k, l]) => `<a href="#stocks/${encodeURIComponent(cur.key)}/${k}"${k === sub ? ' aria-current="page"' : ''}>${l}</a>`).join('')}</nav></section><div id="sk-body"><section class="panel"><p class="sub">Loading datapoints…</p></section></div>`;
    }
    host.innerHTML = head('Stocks', 'Tier 1–2 companies', 'The Tech Specialist debate, the thesis tenets, a live Visible Alpha quarterly review, every datapoint organized by what matters for the stock, the earnings-review metrics, and what management has said over time.') + `<div class="sk-wrap">${nav}<div class="sk-main">${body}</div></div>`;
    const $ = id => document.getElementById(id);
    $('sk-q').addEventListener('input', e => { fs.q = e.target.value.trim().toLowerCase(); const pos = e.target.selectionStart; renderStocks(); const q = $('sk-q'); q.focus(); q.setSelectionRange(pos, pos); });
    host.querySelectorAll('#sk-tier button').forEach(b => b.addEventListener('click', () => { fs.tier = b.dataset.v; renderStocks(); }));
    $('sk-sec').addEventListener('change', e => { fs.sec = e.target.value; fs.sub = ''; renderStocks(); });
    $('sk-sub').addEventListener('change', e => { fs.sub = e.target.value; renderStocks(); });
    $('sk-sort').addEventListener('change', e => { fs.sort = e.target.value; fs.dir = 'desc'; renderStocks(); });
    if ($('sk-dir')) $('sk-dir').addEventListener('click', () => { fs.dir = fs.dir === 'asc' ? 'desc' : 'asc'; renderStocks(); });
    $('sk-flt').addEventListener('change', e => { fs.flt = e.target.value; renderStocks(); });
    $('sk-min').addEventListener('change', e => { fs.minN = e.target.value; renderStocks(); });
    host.querySelectorAll('table.sk-rt th[data-sk]').forEach(th => th.addEventListener('click', () => { const k = th.dataset.sk, curS = fs.sort || 'x'; fs.dir = curS === k && (fs.sort ? fs.dir : 'desc') === 'desc' ? 'asc' : 'desc'; fs.sort = k; renderStocks(); }));
    if (!cur) return;
    if (String(sub).startsWith('dd-')) { sdView(cur, sub, $('sk-body')); return; }
    if (sub === 'earnings') { $('sk-body').innerHTML = earningsView(cur); return; }
    if (sub === 'insiders') { stockMgView(cur, $('sk-body')); return; }
    if (sub === 'kpis') { stockKpiView(cur, $('sk-body')); return; }
    if (sub === 'qr') { $('sk-body').innerHTML = `<section class="panel"><div class="panel-h"><h2>Quarterly review</h2><span class="muted">Visible Alpha · live</span></div><div class="qr" id="sk-qr"></div></section>`; qrMount($('sk-qr'), cur); return; }
    getDP().then(({ SRC, ROWS }) => {
      const hp = (location.hash || '').split('/'); if (!document.getElementById('sk-body') || decodeURIComponent(hp[1] || '') !== cur.key || (hp[2] || 'debate') !== sub) return;
      const rs = new Set(cur.rids);
      const mine = ROWS.filter(r => rs.has(r[1]) && inWin(r[2], null));
      $('sk-body').innerHTML = sub === 'datapoints' ? dpView(cur, mine, SRC) : sub === 'management' ? mgmtView(cur, mine, SRC) : sub === 'thesis' ? thesisView(cur, mine, SRC, TH.get(String(cur.t).toUpperCase())) : debateView(cur, mine, SRC, TH.get(String(cur.t).toUpperCase()));
      const b = $('sk-body'); b.querySelectorAll('[data-f]').forEach(x => x.addEventListener('click', () => { b.dataset.f = x.dataset.f; b.querySelectorAll('[data-f]').forEach(y => y.setAttribute('aria-pressed', String(y === x))); b.querySelectorAll('.sk-fam').forEach(fz => { fz.hidden = !!b.dataset.f && fz.dataset.fam !== b.dataset.f; }); }));
    }).catch(e => { console.error(e); $('sk-body').innerHTML = `<section class="panel">${none('The datapoint files did not load. Reload the page.')}</section>`; });
  }

  // ---- Stocks › Questions & insiders: this company's Canary questions and insider trades (same data as the Mgmt & insiders tab) ----
  function stockMgView(cur, el) {
    const M = D.mgmt || {}, I = M.insiders || {}, qmeta = M.questions || {};
    const keyOf = t => String(t || '').toUpperCase().trim();
    const same = c => [cur.t, cur.bbg, cur.key].map(keyOf).includes(keyOf(c.t));
    const money = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); const s = a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : a >= 1e3 ? (a / 1e3).toFixed(0) + 'k' : a.toFixed(0); return (v < 0 ? '−$' : '$') + s; };
    const ins = arr(I.companies).find(same), nc = arr(I.not_covered).find(same);
    const insHtml = ins ? `<section class="panel"><div class="panel-h"><h2>Insider transactions</h2><span class="sub">${esc(ins.source || arr(I.sources).join(' · '))}${I.window ? ' · ' + esc(fmtD(I.window.start)) + ' to ' + esc(fmtD(I.window.end)) : ''}</span></div>` +
        (ins.read ? `<p style="margin:0"><b>${esc(ins.read)}</b></p>` : '') +
        `<div class="summary"><div class="stat"><span class="v c-pos">${money((ins.buys_6m || {}).value_usd)}</span><span class="l">Buys, 6 months (${(ins.buys_6m || {}).n || 0})</span></div><div class="stat"><span class="v c-neg">${money((ins.sells_6m || {}).value_usd)}</span><span class="l">Sells, 6 months (${(ins.sells_6m || {}).n || 0})</span></div><div class="stat"><span class="v ${(ins.net_6m_usd || 0) >= 0 ? 'c-pos' : 'c-neg'}">${money(ins.net_6m_usd)}</span><span class="l">Net, 6 months</span></div><div class="stat"><span class="v">${money((ins.buys_30d || {}).value_usd)} / ${money((ins.sells_30d || {}).value_usd)}</span><span class="l">Buys / sells, 30 days</span></div><div class="stat"><span class="v">${ins.plan_sell_pct != null ? Math.round(ins.plan_sell_pct) + '%' : '–'}</span><span class="l">Sells under 10b5-1</span></div></div>` +
        (arr(ins.notable).length ? `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Date</th><th>Insider</th><th>Type</th><th class="n">Shares</th><th class="n">Price</th><th class="n">Value</th><th>Plan</th></tr></thead><tbody>${arr(ins.notable).map(x => `<tr><td class="nowrap">${esc(x.date || '6M total')}</td><td>${esc(x.insider || '')}<div class="sub">${esc(x.title || '')}</div></td><td class="${/buy/i.test(x.buy_sell || x.type || '') ? 'c-pos' : 'c-neg'}">${/buy/i.test(x.buy_sell || x.type || '') ? 'Buy' : 'Sell'}${x.basis ? `<div class="sub">${esc(x.basis)}</div>` : ''}</td><td class="n">${x.shares != null ? Number(x.shares).toLocaleString() : '–'}</td><td class="n">${x.price != null ? esc(x.price) : '–'}</td><td class="n">${money(x.value_usd)}</td><td>${x.plan_10b5_1 ? '10b5-1' : x.plan_10b5_1 === false ? '<b>open</b>' : '–'}</td></tr>`).join('')}</tbody></table></div>` : '') +
        (ins.data_note || ins.fx_note ? `<p class="sub">${esc([ins.data_note, ins.fx_note].filter(Boolean).join(' '))}</p>` : '') + `</section>`
      : `<section class="panel"><h2>Insider transactions</h2>${none(nc ? 'No insider data: ' + esc(nc.reason || '') : 'No open-market insider trades found for ' + esc(cur.t) + ' in the last 6 months.')}</section>`;
    const qPanel = Q => { const c = arr(Q && Q.companies).find(same);
      if (!c) return `<section class="panel"><h2>Questions for management</h2>${none(Q ? 'Canary has no super-analyst questions for ' + esc(cur.t) + '.' : 'Loading questions…')}</section>`;
      const qs = arr(c.questions), th = [...new Set(qs.map(x => x.theme || 'Questions'))];
      const preps = arr((D.prep || {}).runs).filter(r => /management-prep/i.test(r.skill || '') && new RegExp('\\b' + String(cur.t).split(' ')[0].replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b').test(r.title || ''));
      return `<section class="panel"><div class="panel-h"><h2>Questions for management</h2><span class="sub">${esc(Q.source || 'Canary super analyst')}${Q.as_of ? ' · ' + esc(fmtD(Q.as_of)) : ''} · ${qs.length}${c.questions_total ? ' of ' + esc(c.questions_total) : ''} questions</span></div>` +
        th.map(t => `<h3>${esc(t)}</h3><ol class="mg-q">${qs.filter(x => (x.theme || 'Questions') === t).map(x => `<li>${String(x.q || '').length > 380 ? `<details class="mg-long"><summary>${esc(String(x.q).slice(0, 300).replace(/\s+\S*$/, ''))}…</summary>${esc(x.q)}</details>` : esc(x.q)}${x.why ? `<div class="sub">${esc(x.why)}</div>` : ''}</li>`).join('')}</ol>`).join('') +
        (arr(c.debates).length ? `<h3>Open debates</h3><ul class="b">${arr(c.debates).map(d => `<li><b>${esc(d.title)}</b>${d.summary ? ' · ' + esc(d.summary) : ''}</li>`).join('')}</ul>` : '') +
        (c.monitoring ? `<p class="sub"><b>What to monitor:</b> ${esc(c.monitoring)}</p>` : '') +
        (preps.length ? `<p class="sub">Your management-prep pages: ${preps.map(r => `<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>`).join(' · ')}</p>` : '') + `</section>`; };
    const paint = Q => { if (el.isConnected) el.innerHTML = insHtml + qPanel(Q); };
    if (MG.Q || !qmeta.file) { paint(MG.Q || qmeta); return; }
    paint(null);
    fetch(qmeta.file).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(j => { MG.Q = j; paint(j); }).catch(() => { if (el.isConnected) el.innerHTML = insHtml + `<section class="panel"><h2>Questions for management</h2><p class="sub c-neg">Could not load the questions file.</p></section>`; });
  }
  const FAMOF = k => /^growth/.test(k) ? 'Growth' : /^tam/.test(k) ? 'TAM' : /^margin/.test(k) ? 'Margins' : /^competition/.test(k) ? 'Competition' : /^risk/.test(k) ? 'Risk' : /^shareholder/.test(k) ? 'Capital return' : 'Other';
  const FAMS = ['Growth', 'TAM', 'Margins', 'Competition', 'Risk', 'Capital return', 'Other'];
  const MGMT = /management|\bmgmt\b|\bceo\b|\bcfo\b|\bcoo\b|\bcto\b|earnings call|conference call|transcript|investor day|analyst day|\bir\b|press release|guidance|10-k|10-q|8-k|filing|shareholder letter/i;
  const REL = (st, p) => /inferred|extrapolat/i.test(p || '') ? 0.3 : /semianalysis|cleveland|bwg|trendforce|channel check|third bridge|tegus|expert/i.test(p || '') ? 1 : MGMT.test(p || '') || st === 'company' ? 1 : ({ independent_research: 1, sell_side: 0.6, news: 0.5, substack: 0.5, email: 0.5, evernote: 0.6, twitter: 0.3, reddit: 0.2 })[st] ?? 0.5;
  function assign(cur, r) {
    const fam = FAMOF(r[3]), t = r[9].toLowerCase();
    const ds = cur.drivers.filter(d => d.fam === fam || (fam === 'Growth' && d.fam === 'TAM'));
    let best = null, bs = 0;
    ds.forEach(d => { let sc = 0; d.kw.forEach(k => { if (k.length >= 3 && t.includes(k)) sc += k.length > 6 ? 2 : 1; }); if (sc > bs) { bs = sc; best = d; } });
    return best ? best.label : (fam === 'Other' ? 'Other' : 'Other ' + fam.toLowerCase());
  }
  const DIRC = v => v === 1 ? 'pos' : v === -1 ? 'neg' : 'mix';
  const rowHtml = (r, SRC) => `<div class="li sk-dp"><span class="stripe ${DIRC(r[4])}${r[5] === 'h' ? '' : r[5] === 'l' ? ' lo' : ' md'}"></span><div class="body"><span class="mono sub">${fmtD(r[2])}</span> ${esc(r[9])}<div class="sub">${esc(SRC[r[7]] || '')}${r[6] ? ` · ${esc(r[6])}` : ''}${r[5] ? ` · ${({ h: 'high', m: 'medium', l: 'low' })[r[5]] || ''} confidence` : ''}</div></div></div>`;
  function grouped(cur, rows) {
    const g = new Map();
    rows.forEach(r => { const fam = FAMOF(r[3]), d = assign(cur, r), k = fam + '|' + d; if (!g.has(k)) g.set(k, { fam, label: d, rows: [] }); g.get(k).rows.push(r); });
    const order = new Map(cur.drivers.map((d, i) => [d.label, i]));
    return [...g.values()].sort((a, b) => FAMS.indexOf(a.fam) - FAMS.indexOf(b.fam) || (order.get(a.label) ?? 99) - (order.get(b.label) ?? 99) || b.rows.length - a.rows.length);
  }
  const famBar = () => `<div class="seg"><button type="button" data-f="" aria-pressed="true">All</button>${FAMS.slice(0, 6).map(f => `<button type="button" data-f="${f}" aria-pressed="false">${f}</button>`).join('')}</div>`;
  const IMPSC = (r, SRC) => { const age = (Date.now() - new Date(r[2] + 'T12:00:00')) / 864e5; if (age > 183) return 0;
    return REL(r[6], SRC[r[7]]) * ({ h: 1, m: 0.75, l: 0.45 }[r[5]] || 0.7) * (/\d/.test(r[9]) ? 1.25 : 1) * (r[4] === 0 || r[4] == null ? 0.7 : 1) * Math.pow(0.5, age / 120); };
  function importantSet(cur, rows, SRC) {
    const sc = rows.map(r => ({ r, s: IMPSC(r, SRC), d: assign(cur, r) })).filter(x => x.s > 0).sort((a, b) => b.s - a.s);
    const keep = new Set(sc.slice(0, 30).map(x => x.r[0])), per = new Map();
    sc.forEach(x => { const n = per.get(x.d) || 0; if (n < 2) { keep.add(x.r[0]); per.set(x.d, n + 1); } });
    return keep;
  }
  const STYPE = { sell_side: 'Sell-side', company: 'Company / mgmt', independent_research: 'Independent research', news: 'News', substack: 'Substack', email: 'Email', evernote: 'Notes', twitter: 'X / Twitter', reddit: 'Reddit', fintool: 'Fintool' };
  function dpView(cur, rows, SRC) {
    if (!rows.length) return `<section class="panel">${none('No datapoints on this name in the window.')}</section>`;
    const imp = importantSet(cur, rows, SRC);
    const types = [...new Set(rows.map(r => r[6]).filter(Boolean))].sort();
    const drivers = [...new Set(rows.map(r => assign(cur, r)))].sort();
    setTimeout(() => wireDp(cur, rows, SRC, imp), 0);
    return `<section class="panel"><div class="panel-h"><h2>Datapoints</h2><span class="muted" id="skd-count"></span></div>
      <div class="ctl sk-ctl" role="group" aria-label="Datapoint filters">
        <div class="seg" id="skd-imp"><button type="button" data-v="imp" aria-pressed="true">Most important</button><button type="button" data-v="all" aria-pressed="false">All</button></div>
        ${famBar()}
        <label>Driver <select id="skd-drv"><option value="">All</option>${drivers.map(d => `<option>${esc(d)}</option>`).join('')}</select></label>
        <div class="seg" id="skd-dir"><button type="button" data-v="" aria-pressed="true">Any</button><button type="button" data-v="1" aria-pressed="false">Positive</button><button type="button" data-v="-1" aria-pressed="false">Negative</button><button type="button" data-v="0" aria-pressed="false">Mixed</button></div>
        <label>Source <select id="skd-src"><option value="">All</option>${types.map(t => `<option value="${esc(t)}">${esc(STYPE[t] || t)}</option>`).join('')}<option value="__channel">Channel checks &amp; experts</option><option value="__mgmt">Management only</option></select></label>
        <label>Confidence <select id="skd-conf"><option value="">Any</option><option value="h">High</option><option value="hm">High + medium</option></select></label>
        <label>Search <input type="search" id="skd-q" placeholder="Word or number"></label>
      </div>
      <div class="legend"><span><i style="background:var(--pos)"></i>positive</span><span><i style="background:var(--neg)"></i>negative</span><span><i style="background:var(--warn,#eda100)"></i>mixed</span><span class="sub">fainter = lower confidence · newest first</span></div>
      <div class="list" id="skd-list"></div><button type="button" class="btn more" id="skd-more" hidden>Show 50 more</button></section>`;
  }
  function wireDp(cur, rows, SRC, imp) {
    const b = document.getElementById('sk-body'); if (!b || !document.getElementById('skd-list')) return;
    const st = { imp: 'imp', fam: '', drv: '', dir: '', src: '', conf: '', q: '', shown: 50 };
    const CHAN = /semianalysis|cleveland|bwg|trendforce|channel check|third bridge|tegus|expert|supply chain/i;
    const sorted = rows.slice().sort((a, b) => b[2].localeCompare(a[2]) || b[0] - a[0]);
    const draw = () => {
      const xs = sorted.filter(r => (st.imp === 'all' || imp.has(r[0])) && (!st.fam || FAMOF(r[3]) === st.fam) && (!st.drv || assign(cur, r) === st.drv) && (st.dir === '' || String(r[4]) === st.dir)
        && (!st.src || (st.src === '__channel' ? CHAN.test(SRC[r[7]] || '') : st.src === '__mgmt' ? (r[6] === 'company' || MGMT.test(SRC[r[7]] || '')) : r[6] === st.src))
        && (!st.conf || (st.conf === 'h' ? r[5] === 'h' : r[5] === 'h' || r[5] === 'm')) && (!st.q || r[9].toLowerCase().includes(st.q)));
      document.getElementById('skd-count').textContent = `${xs.length} of ${rows.length} datapoints`;
      document.getElementById('skd-list').innerHTML = xs.slice(0, st.shown).map(r => rowHtml(r, SRC).replace('<span class="mono sub">', `<span class="chip out">${esc(assign(cur, r))}</span> <span class="mono sub">`)).join('') || none('Nothing matches these filters.');
      document.getElementById('skd-more').hidden = xs.length <= st.shown;
    };
    const seg = (id, k) => b.querySelectorAll('#' + id + ' button').forEach(x => x.addEventListener('click', () => { st[k] = x.dataset.v; st.shown = 50; b.querySelectorAll('#' + id + ' button').forEach(y => y.setAttribute('aria-pressed', String(y === x))); draw(); }));
    seg('skd-imp', 'imp'); seg('skd-dir', 'dir');
    b.querySelectorAll('[data-f]').forEach(x => x.addEventListener('click', () => { st.fam = x.dataset.f; st.shown = 50; draw(); }));
    const sel = (id, k) => document.getElementById(id).addEventListener('change', e => { st[k] = e.target.value; st.shown = 50; draw(); });
    sel('skd-drv', 'drv'); sel('skd-src', 'src'); sel('skd-conf', 'conf');
    document.getElementById('skd-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); st.shown = 50; draw(); });
    document.getElementById('skd-more').addEventListener('click', () => { st.shown += 50; draw(); });
    draw();
  }
  function debateView(cur, rows, SRC, th) {
    if (!rows.length) return agentPanel(cur) + `<section class="panel">${none('No datapoints on this name in the window.')}</section>`;
    const now = Date.now(), score = r => (r[4] || 0) * ({ h: 1, m: 0.75, l: 0.5 }[r[5]] || 0.75) * REL(r[6], SRC[r[7]]) * Math.pow(0.5, (now - new Date(r[2] + 'T12:00:00')) / 864e5 / 90);
    const sc = rows.map(r => ({ r, s: score(r), d: assign(cur, r), f: FAMOF(r[3]) }));
    const bull = sc.filter(x => x.s > 0).sort((a, b) => b.s - a.s), bear = sc.filter(x => x.s < 0).sort((a, b) => a.s - b.s);
    const pick = (xs, n) => { const seen = new Set(), out = []; for (const x of xs) { if (seen.has(x.d) && out.length < n * 2) continue; seen.add(x.d); out.push(x); if (out.length >= n) break; } return out; };
    const N = G.n ? Math.min(G.n, 25) : 6;
    const it = x => `<div class="li sk-dp"><span class="stripe ${DIRC(x.r[4])}"></span><div class="body"><span class="chip out">${esc(x.d)}</span> <span class="mono sub">${fmtD(x.r[2])}</span> ${esc(x.r[9])}<div class="sub">${esc(SRC[x.r[7]] || '')}</div></div></div>`;
    const by = new Map(); sc.forEach(x => { if (!by.has(x.d)) by.set(x.d, { d: x.d, f: x.f, p: 0, n: 0, sp: 0, sn: 0 }); const y = by.get(x.d); if (x.s > 0) { y.p++; y.sp += x.s; } else if (x.s < 0) { y.n++; y.sn -= x.s; } });
    const contested = [...by.values()].filter(y => y.p && y.n).map(y => ({ ...y, heat: Math.min(y.sp, y.sn) })).sort((a, b) => b.heat - a.heat).slice(0, 5);
    const bal = [...by.values()].sort((a, b) => (b.sp + b.sn) - (a.sp + a.sn)).slice(0, 10);
    const tot = bal.reduce((m, y) => Math.max(m, y.sp, y.sn), 0.001);
    return agentPanel(cur) + summaryPanel(cur, th, true) + `<section class="panel"><div class="panel-h"><h2>The evidence behind it</h2><span class="muted">${rows.length} datapoints · weighted by source reliability × confidence × recency (90-day half-life)</span></div>
      <div class="grid2"><div><h3 class="c-pos">Bull case</h3><div class="list">${pick(bull, N).map(it).join('') || none('No positive evidence in the window.')}</div></div><div><h3 class="c-neg">Bear case</h3><div class="list">${pick(bear, N).map(it).join('') || none('No negative evidence in the window.')}</div></div></div>
      <h3 style="margin-top:14px">Where the evidence leans, by driver</h3><div class="sk-bal">${bal.map(y => `<div class="sk-balr"><span>${esc(y.d)} <span class="sub">${y.p}▲ ${y.n}▼</span></span><span class="sk-bt"><span class="l"><i class="neg" style="width:${(y.sn / tot * 100).toFixed(1)}%"></i></span><span class="r"><i class="pos" style="width:${(y.sp / tot * 100).toFixed(1)}%"></i></span></span></div>`).join('')}</div>
      ${contested.length ? `<h3 style="margin-top:14px">What decides it</h3><p class="sub" style="margin:0 0 6px">Drivers with strong evidence on both sides.</p><ul class="b">${contested.map(y => `<li><b>${esc(y.d)}</b> — ${y.p} positive vs ${y.n} negative datapoints</li>`).join('')}</ul>` : ''}</section>`;
  }

  // Tech Specialist debate agent output (stock-debate skill / Tech Specialist Debate History pages), shown in full
  function agentPanel(cur) {
    const P = cur.debate_page, FULL = window.__FULL || {};
    if (!P) return `<section class="panel sk-agent"><div class="panel-h"><h2>Tech Specialist debate</h2><span class="chip out">Not run on ${esc(cur.t)} yet</span></div>
      <p class="sub" style="margin:0">The debate agent reads about nine months of Tech Specialist desk notes on the name, plus the latest earnings review and your Supabase datapoints, and writes the debate onto the thesis page. It has run on ${DEBN} names so far. Until it runs on ${esc(cur.t)}, the short read below is drafted from your datapoints.</p></section>`;
    const f = FULL[String(P.url).split('?')[0]];
    const age = Math.round((Date.now() - new Date(P.date + 'T12:00:00')) / 864e5);
    const hdr = `<div class="panel-h"><div><span class="eyebrow">${P.kind === 'stock-debate' ? 'Stock debate agent' : 'Tech Specialist debate history'} · ${esc(fmtD(P.date))}${isFinite(age) ? ` · ${age} days old` : ''}${P.dry_run ? ' · dry run' : ''}</span><h2 style="margin-top:4px">${esc(String(P.title || '').replace(/^(🔍\s*)+/, ''))}</h2></div>${link(P.url, 'Notion')}</div>`;
    if (!f) return `<section class="panel sk-agent">${hdr}<p class="sub">${window.__FULL ? 'The page text is not in this build.' : 'Loading the debate…'}</p></section>`;
    const openT = /overview|debate|callouts|key issues|bull|bear/i;
    return `<section class="panel sk-agent">${hdr}${f.sections.map((x, i) => x.subs
      ? `<details class="fr-sec" open><summary>${x.title}</summary><div class="fr-body">${x.subs.map(u => `<details class="fr-sec fr-sub"${openT.test(u.title) ? ' open' : ''}><summary>${u.title === 'Overview' ? 'Summary' : u.title}</summary><div class="fr-html">${u.html}</div></details>`).join('')}</div></details>`
      : `<details class="fr-sec"${i < 2 || openT.test(x.title) && i < 3 ? ' open' : ''}><summary>${x.title === 'Overview' ? 'The debate in five bullets' : x.title}</summary><div class="fr-html">${x.html}</div></details>`).join('')}</section>`;
  }
  const DEBN = arr((D.stocks || {}).companies).filter(c => c.debate_page).length;
  // Thesis tab: key tenets from the revised thesis page (or drafted thesis-builder style), with the evidence on each
  function thesisView(cur, rows, SRC, th) {
    const DB = cur.debate || {}, RT = cur.thesis || null;
    const tenets = RT && arr(RT.tenets).length ? RT.tenets : arr(DB.tenets);
    const isDraft = !(RT && arr(RT.tenets).length);
    const conv = v => { const n = +v; return isFinite(n) && n > 0 ? `<span class="sk-conv" title="Conviction ${n}/10"><i style="width:${n * 10}%"></i></span><b class="mono">${n}/10</b>` : ''; };
    const STOPW = new Set('the and for with from into over that this than will are its not but has have been more less into onto via per our their they them what when which while about after before under above across through'.split(' '));
    const words = t => [...new Set(String(t || '').toLowerCase().replace(/[^a-z0-9%$.\- ]/g, ' ').split(/\s+/).filter(w => w.length >= 4 && !STOPW.has(w)))];
    const now = Date.now(), score = r => ({ h: 1, m: 0.75, l: 0.5 }[r[5]] || 0.75) * REL(r[6], SRC[r[7]]) * Math.pow(0.5, (now - new Date(r[2] + 'T12:00:00')) / 864e5 / 90);
    const evFor = t => { const ws = words(t.tenet + ' ' + (t.why || '')); if (!ws.length) return [];
      return rows.map(r => { const txt = r[9].toLowerCase(); let hit = 0; ws.forEach(w => { if (txt.includes(w)) hit += w.length > 6 ? 2 : 1; }); return { r, s: hit >= 3 ? hit * score(r) : 0 }; }).filter(x => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 4).map(x => x.r); };
    const lean = t => { const l = String(t.lean || t.status || ''); const c = /support|strength|🟢|improv/i.test(l) ? 'c-pos' : /challeng|weak|🔴|deterior/i.test(l) ? 'c-neg' : ''; return l ? `<span class="chip out ${c}">${esc(l)}</span>` : ''; };
    if (!tenets.length) return `<section class="panel">${none('No thesis tenets for this name yet.')}</section>`;
    return `<section class="panel sk-thesis"><div class="panel-h"><h2>Thesis</h2>${isDraft ? '<span class="chip out">Draft from your datapoints · not yet a revised thesis page</span>' : `<span class="chip out">From your revised thesis${RT.updated ? ' · ' + esc(String(RT.updated).slice(0, 10)) : ''}</span> ${link(RT.url, 'Notion')}`}</div>
      ${RT && RT.summary_pitch ? `<p class="sk-pitch2"><b>Summary pitch</b> ${esc(RT.summary_pitch)}</p>` : ''}
      ${RT && RT.stance ? `<p class="sub" style="margin:0 0 8px">Stance: <b>${esc(RT.stance)}</b></p>` : th && th.stance ? `<p class="sub" style="margin:0 0 8px">Stance: <b>${esc(th.stance)}</b></p>` : ''}
      <ol class="sk-tenets">${tenets.map(t => { const ev = evFor(t); return `<li><div class="sk-ten-h"><b>${esc(t.tenet || '')}</b> ${conv(t.conviction)} ${lean(t)}</div>${t.why || t.evidence ? `<p class="sub">${esc(t.why || t.evidence)}</p>` : ''}${ev.length ? `<details><summary>Latest evidence on this tenet (${ev.length})</summary><div class="list">${ev.map(r => rowHtml(r, SRC)).join('')}</div></details>` : ''}</li>`; }).join('')}</ol>
      ${arr(DB.decides).length ? `<h3>What decides it</h3><ul class="b">${arr(DB.decides).map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}</section>`;
  }
  function summaryPanel(cur, th, noTenets) {
    const DB = cur.debate || {}, RT = cur.thesis || null;
    const tenets = RT && arr(RT.tenets).length ? RT.tenets : arr(DB.tenets);
    const isDraft = !(RT && arr(RT.tenets).length);
    const conv = v => { const n = +v; return isFinite(n) && n > 0 ? `<span class="sk-conv" title="Conviction ${n}/10"><i style="width:${n * 10}%"></i></span><b class="mono">${n}</b>` : '<span class="sub">—</span>'; };
    const lean = t => { const l = String(t.lean || t.status || ''); const c = /support|strength|🟢|improv/i.test(l) ? 'c-pos' : /challeng|weak|🔴|deterior/i.test(l) ? 'c-neg' : ''; return l ? `<span class="${c}">${esc(l)}</span>` : ''; };
    const ul = (xs, cls) => arr(xs).length ? `<ul class="b ${cls || ''}">${arr(xs).map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : none('Not written yet.');
    return `<section class="panel sk-sum">
      ${RT && RT.summary_pitch ? `<p class="sk-pitch2"><b>Summary pitch</b> ${esc(RT.summary_pitch)} ${link(RT.url, 'Thesis')}</p>` : ''}
      ${noTenets ? `<div class="panel-h"><h2>Short read</h2><span class="muted">Bull and bear in a line each, drafted from your datapoints</span></div>` : ''}<div class="grid2"><div><h3 class="c-pos">Bull case</h3>${ul(DB.bull)}</div><div><h3 class="c-neg">Bear case</h3>${ul(DB.bear)}</div></div>
      ${arr(DB.decides).length ? `<h3>What decides it</h3>${ul(DB.decides)}` : ''}
      ${tenets.length && !noTenets ? `<h3>Thesis tenets ${isDraft ? '<span class="chip out">Draft from evidence — edit in Notion</span>' : `<span class="chip out">From your revised thesis</span> ${link(RT.url, 'Notion')}`}</h3>
        <table class="dt sk-ten"><thead><tr><th>Tenet</th><th>Conviction</th><th>${isDraft ? 'Evidence lean' : 'Status'}</th><th>Why</th></tr></thead><tbody>${tenets.map(t => `<tr><td>${esc(t.tenet || '')}</td><td class="nowrap">${conv(t.conviction)}</td><td>${lean(t)}</td><td class="sub">${esc(t.why || t.evidence || '')}</td></tr>`).join('')}</tbody></table>` : ''}
      ${th && !RT ? `<p class="sub" style="margin-top:8px">Thesis page: ${esc(th.stance || '')} ${esc(th.summary || '')}</p>` : ''}
      ${!DB.bull ? '<p class="sub">The written debate for this name is not in this build yet; the evidence below is.</p>' : ''}</section>`;
  }
  function mgmtView(cur, rows, SRC) {
    const ms = rows.filter(r => r[6] === 'company' || MGMT.test(SRC[r[7]] || ''));
    if (!ms.length) return `<section class="panel">${none('No management commentary stored for this name in the window.')}</section>`;
    const gs = grouped(cur, ms.slice().sort((a, b) => a[2].localeCompare(b[2])));
    return `<section class="panel"><div class="panel-h"><h2>What management has said, over time</h2><span class="muted">${ms.length} statements · oldest → newest within each driver</span></div>${famBar()}` +
      FAMS.map(f => { const xs = gs.filter(x => x.fam === f); if (!xs.length) return ''; return `<div class="sk-fam" data-fam="${f}"><h3>${f}</h3>${xs.map(x => `<details class="sk-drv" open><summary><b>${esc(x.label)}</b> <span class="sub">${x.rows.length} · ${fmtD(x.rows[0][2])} → ${fmtD(x.rows[x.rows.length - 1][2])}</span></summary><div class="sk-tl">${x.rows.slice(-(G.n || 12)).map(r => rowHtml(r, SRC)).join('')}</div></details>`).join('')}</div>`; }).join('') + `</section>`;
  }
  function earningsView(cur) {
    const ms = arr(cur.metrics); if (!ms.length) return `<section class="panel">${none('No earnings review stored for this name yet.')}</section>`;
    const qs = [...new Set(ms.map(m => m.cq))].sort();
    const SEC = [['quarter', 'Quarter'], ['next_q_guide', 'Next-quarter guide'], ['fy_guide', 'Fiscal-year guide']];
    const pc = v => v == null || v === '' ? '' : `<span class="mono ${+v >= 0 ? 'c-pos' : 'c-neg'}">${(+v > 0 ? '+' : '') + (+v).toFixed(1)}%</span>`;
    const qh = q => { const m = ms.find(x => x.cq === q); return `${esc(m.fq || q)}<div class="sub">${fmtD(m.d)} · ${esc(String(m.verdict || '').replace(/_/g, ' '))}</div>`; };
    return SEC.map(([k, l]) => { const xs = ms.filter(m => m.section === k); if (!xs.length) return ''; const mets = [...new Set(xs.map(m => m.metric))];
      return `<section class="panel" style="padding:0"><div class="panel-h" style="padding:12px 14px 0"><h2>${l}</h2><span class="muted">Actual · vs 📊 Street · vs 🎯 bogey</span></div><div class="tbl-wrap"><table class="dt"><thead><tr><th>Metric</th>${qs.map(q => `<th>${qh(q)}</th>`).join('')}</tr></thead><tbody>${mets.map(mt => `<tr><td>${esc(mt)}</td>${qs.map(q => { const m = xs.find(x => x.metric === mt && x.cq === q); return `<td>${m ? `${m.marker ? esc(m.marker) + ' ' : ''}<b>${esc(m.actual || '')}</b>${m.street ? `<div class="sub">📊 ${esc(m.street)} ${pc(m.vs_st)}</div>` : ''}${m.bogey ? `<div class="sub">🎯 ${esc(m.bogey)} ${pc(m.vs_bg)}</div>` : ''}` : '<span class="sub">—</span>'}</td>`; }).join('')}</tr>`).join('')}</tbody></table></div></section>`; }).join('');
  }

  // ================= QUARTERLY REVIEW: live Visible Alpha table (Stocks tab + Earnings cards) =================
  // Rows are Visible Alpha KPIs pulled through the viewer's SRS MCP connector (va_company_data). The row set,
  // labels and guidance/disclosure notes per company are saved in the page db (collection "qr") so edits stick.
  const QR = { mcp: null, db: null, ready: null, cfg: new Map() };
  const VA = 'SRS MCP', VAT = 'va_company_data';
  QR.ready = (window.claude && typeof window.claude.use === 'function')
    ? Promise.all([window.claude.use('mcp').catch(() => null), window.claude.use('db').catch(() => null)]).then(([m, d]) => { QR.mcp = m; QR.db = d; })
    : Promise.resolve();
  const qrId = t => ntKey(t).replace(/[^A-Za-z0-9]+/g, '_');
  const vaCall = (input, fresh) => QR.mcp.callTool(VA, VAT, input, { cache: fresh ? { refresh: true, staleTime: 6 * 3600e3, gcTime: 7 * 864e5 } : { staleTime: 6 * 3600e3, gcTime: 7 * 864e5 } }).then(r => r.payload);
  const vaErr = e => {
    const c = e && e.code;
    if (c === 'server_not_connected' || c === 'selection_required') return 'Add the SRS MCP connector in claude.ai Settings → Connectors to load Visible Alpha.';
    if (c === 'needs_reauth') return 'Reconnect SRS MCP in claude.ai Settings → Connectors.';
    if (c === 'not_in_manifest' || c === 'approval_required' || c === 'consent_required') return 'Visible Alpha needs your OK for this page: press Update and allow SRS MCP.';
    if (c === 'blocked_by_policy') return 'Your organization blocks this Visible Alpha call.';
    if (c === 'server_unavailable') return 'Visible Alpha did not answer. Press Update to try again.';
    return 'Visible Alpha call failed' + (e && e.message ? ': ' + String(e.message).slice(0, 160) : '.');
  };
  function qrFmt(v, row, unit) {
    if (v == null || !isFinite(v)) return '';
    const n = String(row.label || row.name || '');
    if (unit === '%' || row.kind === 'ratio') return (+v * (row.kind === 'ratio' || Math.abs(v) <= 1.5 ? 100 : 1)).toFixed(1) + '%';
    if (/\bEPS\b|per share|DPS/i.test(n)) return (+v).toFixed(2);
    const a = Math.abs(v);
    if (unit && unit !== 'Amount') return a >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : a >= 1e3 ? Math.round(v).toLocaleString() : (+v).toFixed(a < 10 ? 2 : 1);
    return a >= 1e9 ? (v / 1e9).toFixed(2) + 'B' : a >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : a >= 1e3 ? (v / 1e3).toFixed(1) + 'K' : (+v).toFixed(2);
  }
  const pct = v => v == null || !isFinite(v) ? '' : (v > 0 ? '+' : '') + (v * 100).toFixed(1) + '%';
  async function qrDefault(co, fresh) {
    let r = await vaCall({ action: 'resolve', company: co.bbg || co.t }, fresh);
    if (r.status !== 'single_match' && co.name) {
      const c = arr(r.candidates).find(x => String(x.bloomberg_ticker || '').toUpperCase() === String(co.bbg || '').toUpperCase());
      if (c) r = { status: 'single_match', selection: c };
      else { const r2 = await vaCall({ action: 'resolve', company: co.name }, fresh); if (r2.status === 'single_match') r = r2; else if (arr(r.candidates).length) r = { status: 'single_match', selection: r.candidates[0] }; }
    }
    if (r.status !== 'single_match') throw { code: 'no_va', message: r.display_message || 'Not found in Visible Alpha' };
    const id = r.selection.va_company_id, vt = r.selection.va_ticker;
    const list = async kw => { try { const x = await vaCall(Object.assign({ action: 'list_kpis', va_company_id: id, period_type: 'QTR' }, kw ? { search: [kw] } : {}), fresh); return arr(x.candidates || (x.selection ? [x.selection] : [])); } catch (e) { return []; } };
    const common = await list(null);
    const rows = [], add = (k, extra) => { if (k && !rows.some(x => x.kpi_id === k.kpi_id)) rows.push(Object.assign({ kind: 'kpi', kpi_id: k.kpi_id, name: k.kpi_name, label: k.kpi_name }, extra || {})); };
    const rev = common.find(k => /^(total )?revenues?$/i.test(k.kpi_name)) || common.find(k => /revenue/i.test(k.kpi_name) && !/ - |mix|cost|deferred/i.test(k.kpi_name));
    add(rev, { role: 'rev', label: 'Total revenue' });
    common.filter(k => /^(total )?revenues? - /i.test(k.kpi_name) && !/miscellaneous|other$/i.test(k.kpi_name)).slice(0, 10)
      .forEach(k => add(k, { label: k.kpi_name.replace(/^(total )?revenues? - /i, '  '), seg: true }));
    const pick = (xs, pref) => xs.find(k => pref.test(k.kpi_name)) || xs[0];
    const gp = pick((await list('Gross profit')).filter(k => /gross profit/i.test(k.kpi_name) && !/mix|margin|adjust|segment/i.test(k.kpi_name)), / - Operating$/i);
    if (gp) { add(gp, { role: 'gp', label: 'Gross profit' }); }
    const oi = pick((await list('Operating income')).filter(k => /operating income/i.test(k.kpi_name) && !/mix|margin|adjust|segment| - (?!Operating)/i.test(k.kpi_name)), / - Operating$/i) || pick((await list('EBIT')).filter(k => /^EBIT\b/i.test(k.kpi_name) && !/margin|mix/i.test(k.kpi_name)), /^EBIT( - Operating)?$/i);
    if (oi) add(oi, { role: 'oi', label: 'Operating income' });
    const eps = pick((await list('EPS')).filter(k => /diluted/i.test(k.kpi_name)), /^EPS - Diluted - Operating$/i);
    if (eps) add(eps, { role: 'eps', label: 'EPS (diluted)' });
    const R = rows.find(x => x.role === 'rev');
    const after = (role, row) => { const i = rows.findIndex(x => x.role === role); if (i >= 0) rows.splice(i + 1, 0, row); };
    if (R && gp) after('gp', { kind: 'ratio', num: gp.kpi_id, den: R.kpi_id, label: 'Gross margin' });
    if (R && oi) after('oi', { kind: 'ratio', num: oi.kpi_id, den: R.kpi_id, label: 'Operating margin' });
    return { va_company_id: id, va_ticker: vt, rows, nq: 12, auto: true };
  }
  async function qrLoadCfg(co) {
    const id = qrId(co.t);
    if (QR.cfg.has(id)) return QR.cfg.get(id);
    let cfg = null;
    if (QR.db) { try { const s = await QR.db.collection('qr').doc(id).get(); if (s.exists) cfg = JSON.parse(JSON.stringify(s.data())); } catch (e) {} }
    if (!cfg) cfg = await qrDefault(co, false);
    QR.cfg.set(id, cfg); return cfg;
  }
  async function qrSave(co, cfg) {
    QR.cfg.set(qrId(co.t), cfg);
    if (!QR.db) throw new Error('Saving needs the page open on claude.ai.');
    const clean = JSON.parse(JSON.stringify(Object.assign({}, cfg, { auto: false, updated: new Date().toISOString(), ticker: co.t })));
    await QR.db.collection('qr').doc(qrId(co.t)).set(clean);
  }
  async function qrData(cfg, fresh, fy, extra) {
    const y = new Date().getFullYear(), out = new Map();
    const ids = [...new Set(cfg.rows.flatMap(r => r.kind === 'ratio' ? [r.num, r.den] : [r.kpi_id]).concat(extra || []).filter(Boolean))];
    const errs = [];
    await Promise.all(ids.map(k => vaCall({ action: 'kpi_data', va_company_id: cfg.va_company_id, kpi_id: k, period_type: fy ? 'FY' : 'QTR', min_year: y - 3, max_year: y + (fy ? 3 : 1) }, fresh)
      .then(p => out.set(k, arr(Array.isArray(p) ? p : (p && p.rows) || [])))
      .catch(e => { errs.push(e); out.set(k, []); })));
    return { byK: out, errs };
  }
  // columns for one period set (quarters or fiscal years)
  function qrCols(data, fy, cfg) {
    const per = new Map();
    data.byK.forEach(rs => rs.forEach(r => { if (!per.has(r.PERIOD)) per.set(r.PERIOD, { p: r.PERIOD, y: r.YEAR, n: r.PERIOD_NUMBER || 0, end: r.PERIOD_END_DATE, act: false, fy, data }); if (r.REPORTED_VALUE != null) per.get(r.PERIOD).act = true; }));
    let ps = [...per.values()].sort((a, b) => a.y - b.y || a.n - b.n);
    const lastA = ps.map(p => p.act).lastIndexOf(true);
    const nA = fy ? 3 : Math.max(4, (cfg.nq || 12) - 4), nE = fy ? 3 : 4;
    return ps.slice(Math.max(0, lastA + 1 - nA), lastA + 1 + nE);
  }
  function qrTable(co, cfg, sets, opt) {
    const ps = [];
    sets.forEach((s, si) => qrCols(s.data, s.fy, cfg).forEach((p, j) => { p.first = si > 0 && j === 0; ps.push(p); }));
    const cell = (k, p) => (p.data.byK.get(k) || []).find(r => r.PERIOD === p.p);
    const val = (k, p) => { const c = cell(k, p); return c ? (c.REPORTED_VALUE != null ? c.REPORTED_VALUE : c.CONSENSUS_VALUE) : null; };
    const lbl = p => p.fy ? 'FY' + String(p.y).slice(2) : p.n + 'Q' + String(p.y).slice(2);
    const cls = p => `n${p.act ? '' : ' qr-e'}${p.first ? ' qr-fy1' : ''}`;
    const prevQ = (p, j) => j && !ps[j - 1].fy === !p.fy && !ps[j].first ? ps[j - 1] : null;
    const rev = cfg.rows.find(r => r.role === 'rev');
    const th = ps.map(p => `<th class="${cls(p)}" title="${esc(p.end || '')}">${lbl(p)}${p.act ? 'A' : 'E'}</th>`).join('');
    const ed = opt.edit;
    let body = '';
    cfg.rows.forEach((r, i) => {
      const ctl = ed ? `<span class="qr-ctl"><button type="button" data-qa="up" data-i="${i}" title="Move up">↑</button><button type="button" data-qa="dn" data-i="${i}" title="Move down">↓</button><button type="button" data-qa="rm" data-i="${i}" title="Remove row">✕</button></span>` : '';
      const name = ed ? `<input class="qr-lbl" data-i="${i}" value="${esc(r.label || r.name)}" aria-label="Row label">` : esc(r.label || r.name);
      const cells = ps.map(p => {
        if (r.kind === 'ratio') { const a = val(r.num, p), b = val(r.den, p); const v = a != null && b ? a / b : null; return `<td class="${cls(p)}">${qrFmt(v, r)}</td>`; }
        const c = cell(r.kpi_id, p); if (!c) return `<td class="${cls(p)} sub">—</td>`;
        const v = c.REPORTED_VALUE != null ? c.REPORTED_VALUE : c.CONSENSUS_VALUE, bm = c.BEAT_MISS_PCT;
        const tip = `Reported ${c.REPORTED_VALUE ?? '—'} · Consensus ${c.CONSENSUS_VALUE ?? '—'}${c.NUMBER_OF_BROKER ? ' (' + c.NUMBER_OF_BROKER + ' brokers)' : ''}${bm != null ? ' · vs cons ' + pct(bm) : ''}`;
        return `<td class="n${c.REPORTED_VALUE != null ? '' : ' qr-e'}${p.first ? ' qr-fy1' : ''}" title="${esc(tip)}">${qrFmt(v, r, c.UNIT_SYMBOL)}${opt.beat && bm != null ? `<div class="qr-s ${bm >= 0 ? 'c-pos' : 'c-neg'}">${pct(bm)}</div>` : ''}</td>`;
      }).join('');
      body += `<tr class="${r.seg ? 'qr-seg' : r.kind === 'ratio' ? 'qr-ratio' : 'qr-main'}"><td class="qr-name">${ctl}${name}</td>${cells}</tr>`;
      if (r.kind === 'kpi' && opt.yy) body += `<tr class="qr-sub"><td class="qr-name sub">y/y</td>${ps.map(p => { const c = cell(r.kpi_id, p); const v = c ? (c.REPORTED_YY != null ? c.REPORTED_YY : c.CONSENSUS_YY) : null; return `<td class="n ${v == null ? '' : v >= 0 ? 'c-pos' : 'c-neg'}${c && c.REPORTED_VALUE == null ? ' qr-e' : ''}${p.first ? ' qr-fy1' : ''}">${c && c.UNIT_SYMBOL === '%' ? '' : pct(v)}</td>`; }).join('')}</tr>`;
      if (r.kind === 'kpi' && opt.qq && ps.some(p => !p.fy)) body += `<tr class="qr-sub"><td class="qr-name sub">q/q</td>${ps.map((p, j) => { if (p.fy) return `<td class="n${p.first ? ' qr-fy1' : ''}"></td>`; const q = prevQ(p, j), a = val(r.kpi_id, p), b = q ? val(r.kpi_id, q) : null; const v = a != null && b ? a / b - 1 : null; return `<td class="n ${v == null ? '' : v >= 0 ? 'c-pos' : 'c-neg'}">${pct(v)}</td>`; }).join('')}</tr>`;
      if (r.kind === 'kpi' && r.seg && rev && opt.mix) body += `<tr class="qr-sub"><td class="qr-name sub">% of revenue</td>${ps.map(p => { const a = val(r.kpi_id, p), b = val(rev.kpi_id, p); return `<td class="n sub${p.first ? ' qr-fy1' : ''}">${a != null && b ? (a / b * 100).toFixed(1) + '%' : ''}</td>`; }).join('')}</tr>`;
      if (ed) body += `<tr class="qr-sub"><td colspan="${ps.length + 1}"><input class="qr-note" data-i="${i}" value="${esc(r.note || '')}" placeholder="Gd: / Discl: shorthand for this row (e.g. 3Q26: HSD q/q, 2H wtd)"></td></tr>`;
      else if (r.note) body += `<tr class="qr-sub"><td class="qr-note-v" colspan="${ps.length + 1}">${esc(r.note)}</td></tr>`;
    });
    return `<div class="tbl-wrap"><table class="dt qr-t"><thead><tr><th>${esc(cfg.va_ticker || '')} · Visible Alpha</th>${th}</tr></thead><tbody>${body}</tbody></table></div>`;
  }

  // ---- Valuation scenarios: 5 columns (last FY actual, FY+1, FY+2, FY+2 upside, FY+2 downside), seeded with consensus ----
  // Extra Visible Alpha lines found by keyword; the line used is shown on hover so a wrong match is visible.
  async function qrValKpis(cfg) {
    if (cfg.valk) return cfg.valk;
    const id = cfg.va_company_id;
    const ls = async kw => { try { const x = await vaCall({ action: 'list_kpis', va_company_id: id, search: [kw], period_type: 'FY' }); return arr(x.candidates || (x.selection ? [x.selection] : [])); } catch (e) { return []; } };
    const pick = (xs, ok, pref) => { const ys = xs.filter(k => ok.test(k.kpi_name)); return (pref && ys.find(k => pref.test(k.kpi_name))) || ys[0] || null; };
    const op = / - Operating$/i;
    const [pre, tax, shr, ni, cash, debt, cap1, cap2, fin] = await Promise.all(['before', 'income tax', 'shares', 'net income', 'cash', 'debt', 'capital expenditure', 'property', 'net profit'].map(ls));
    const k = {
      pretax: pick(pre.concat(await ls('pre-tax')), /(before (income )?tax|pre-?tax)/i, op),
      tax: pick(tax, /^(provision|income tax|tax)/i, op) || pick(tax, /tax/i, op),
      shares: pick(shr, /dil/i, op),
      ni: pick(ni.concat(fin), /^net (income|profit)/i, op),
      cfo: pick(cash, /operating activities|operating cash flow|cash from operations/i, null),
      cash: pick(cash, /^cash/i, /short-term|investments|marketable/i) || pick(cash, /^cash (and|&) cash equivalents$/i, null),
      capex: pick(cap1.concat(cap2), /(capex|capital expend|purchase|investment|additions).*(property|equipment|pp&e)|^capex|capital expenditure/i, null),
      debt_total: pick(debt, /^total debt|^debt$|total borrowings/i, null),
      debt_lt: pick(debt, /long[- ]term debt|long term borrowings/i, null),
      debt_st: pick(debt, /short[- ]term debt|current portion|short term borrowings/i, null),
    };
    const out = {};
    Object.entries(k).forEach(([n, v]) => { if (v) out[n] = { id: v.kpi_id, name: v.kpi_name }; });
    cfg.valk = out; return out;
  }
  function qrValModel(co, cfg, fy, st) {
    const V = cfg.val || (cfg.val = { inp: {}, top: {}, segMode: false });
    const K = cfg.valk || {}, R = role => cfg.rows.find(r => r.role === role);
    const rev = R('rev'), gp = R('gp'), oi = R('oi'), eps = R('eps'), segs = cfg.rows.filter(r => r.kind === 'kpi' && r.seg);
    if (!rev) return '<p class="sub">Add a total revenue row to use the valuation block.</p>';
    const ser = k => (fy.byK.get(k) || []);
    const v = (k, y) => { const r = ser(k).find(x => x.YEAR === y); return r ? (r.REPORTED_VALUE != null ? r.REPORTED_VALUE : r.CONSENSUS_VALUE) : null; };
    const rep = (k, y) => { const r = ser(k).find(x => x.YEAR === y); return r ? r.REPORTED_VALUE : null; };
    const ys = ser(rev.kpi_id).filter(r => r.REPORTED_VALUE != null).map(r => r.YEAR);
    if (!ys.length) return '<p class="sub">Visible Alpha has no reported fiscal-year revenue for this company.</p>';
    const Y0 = Math.max(...ys);
    const kv = (n, y) => K[n] ? v(K[n].id, y) : null;
    const debtOf = y => kv('debt_total', y) != null ? kv('debt_total', y) : (kv('debt_lt', y) || 0) + (kv('debt_st', y) || 0) || null;
    const A = n => Math.abs(n);
    // consensus seeds for year y (ratios relative to year y-1, so the default columns reproduce consensus)
    const seed = y => {
      const r = v(rev.kpi_id, y), r0 = v(rev.kpi_id, y - 1), g = gp && v(gp.kpi_id, y), o = oi && v(oi.kpi_id, y);
      const g0 = gp && v(gp.kpi_id, y - 1), o0 = oi && v(oi.kpi_id, y - 1), pt = kv('pretax', y), tx = kv('tax', y), ni = kv('ni', y), e = eps && v(eps.kpi_id, y);
      const s = { rev_g: r && r0 ? r / r0 - 1 : null, gm: g != null && r ? g / r : null,
        opex_g: g != null && o != null && g0 != null && o0 != null && (g0 - o0) ? (g - o) / (g0 - o0) - 1 : null,
        below: pt != null && o != null ? pt - o : 0, tax: tx != null && pt ? A(tx) / pt : 0.15,
        shares: ni != null && e ? ni / e : kv('shares', y), cfo_m: kv('cfo', y) != null && r ? kv('cfo', y) / r : null,
        capex_s: kv('capex', y) != null && r ? A(kv('capex', y)) / r : null };
      segs.forEach(sg => { const a = v(sg.kpi_id, y), b = v(sg.kpi_id, y - 1); s['seg' + sg.kpi_id] = a != null && b ? a / b - 1 : null; });
      return s;
    };
    const cols = [{ id: 'A', y: Y0, h: 'FY' + String(Y0).slice(2) + 'A' }, { id: 'B', y: Y0 + 1, base: 'A', h: 'FY' + String(Y0 + 1).slice(2) + 'E' },
      { id: 'C', y: Y0 + 2, base: 'B', h: 'FY' + String(Y0 + 2).slice(2) + 'E' }, { id: 'U', y: Y0 + 2, base: 'B', h: 'Upside FY' + String(Y0 + 2).slice(2) }, { id: 'D', y: Y0 + 2, base: 'B', h: 'Downside FY' + String(Y0 + 2).slice(2) }];
    // current price, cash, debt, shares (editable at the top; defaults: Master comps price, last reported balance sheet)
    const cp = ((D.comps || {}).rows || {}); const crow = cp[co.bbg + ' Equity'] || cp[co.bbg] || cp[co.t] || null;
    const T = Object.assign({ price: crow && crow.price != null ? crow.price : null, cash: kv('cash', Y0), debt: debtOf(Y0), shares: null }, V.top || {});
    const out = {};
    const A0 = { rev: v(rev.kpi_id, Y0), gp: gp ? v(gp.kpi_id, Y0) : null, ebit: oi ? v(oi.kpi_id, Y0) : null, pretax: kv('pretax', Y0), ni: kv('ni', Y0), eps: eps ? v(eps.kpi_id, Y0) : null, cfo: kv('cfo', Y0), capex: kv('capex', Y0) != null ? A(kv('capex', Y0)) : null, seg: {} };
    segs.forEach(sg => { A0.seg[sg.kpi_id] = v(sg.kpi_id, Y0); });
    A0.opex = A0.gp != null && A0.ebit != null ? A0.gp - A0.ebit : null; A0.shares = A0.ni != null && A0.eps ? A0.ni / A0.eps : kv('shares', Y0);
    A0.fcf = A0.cfo != null && A0.capex != null ? A0.cfo - A0.capex : null;
    out.A = A0; if (T.shares == null) T.shares = A0.shares;
    const I = {};
    cols.slice(1).forEach(c => {
      const b = out[c.base], sd = seed(c.y), ov = (V.inp || {})[c.id] || {};
      const inp = Object.assign({}, sd, Object.fromEntries(Object.entries(ov).filter(([, x]) => x != null && x !== '')));
      I[c.id] = { sd, inp, ov };
      const o = { seg: {} };
      let segSum = 0, segSum0 = 0;
      segs.forEach(sg => { const b0 = b.seg[sg.kpi_id]; const gg = inp['seg' + sg.kpi_id]; o.seg[sg.kpi_id] = b0 != null && gg != null ? b0 * (1 + gg) : null; if (o.seg[sg.kpi_id] != null) { segSum += o.seg[sg.kpi_id]; segSum0 += b0; } });
      o.rev = V.segMode && segSum ? segSum + (b.rev - segSum0) * (1 + (inp.rev_g || 0)) : b.rev != null && inp.rev_g != null ? b.rev * (1 + inp.rev_g) : null;
      o.gp = o.rev != null && inp.gm != null ? o.rev * inp.gm : null;
      o.opex = b.opex != null && inp.opex_g != null ? b.opex * (1 + inp.opex_g) : null;
      if (ov.ebitm != null && ov.ebitm !== '' && o.rev != null) { o.ebit = o.rev * ov.ebitm; if (o.gp != null) o.opex = o.gp - o.ebit; }
      else o.ebit = o.gp != null && o.opex != null ? o.gp - o.opex : null;
      o.pretax = o.ebit != null ? o.ebit + (inp.below || 0) : null;
      o.ni = o.pretax != null ? o.pretax * (1 - (inp.tax || 0)) : null;
      o.shares = inp.shares; o.eps = o.ni != null && o.shares ? o.ni / o.shares : null;
      o.cfo = o.rev != null && inp.cfo_m != null ? o.rev * inp.cfo_m : null; o.capex = o.rev != null && inp.capex_s != null ? o.rev * inp.capex_s : null;
      o.fcf = o.cfo != null && o.capex != null ? o.cfo - o.capex : null; o.fcfps = o.fcf != null && o.shares ? o.fcf / o.shares : null;
      out[c.id] = o;
    });
    // multiples: default = today's multiples on FY+1
    const B = out.B, mcap = T.price != null && T.shares ? T.price * T.shares : null, ev = mcap != null ? mcap - (T.cash || 0) + (T.debt || 0) : null;
    const mSeed = { pe: T.price != null && B.eps ? T.price / B.eps : null, pfcf: T.price != null && B.fcfps ? T.price / B.fcfps : null, evs: ev != null && B.rev ? ev / B.rev : null };
    cols.slice(1).forEach(c => { const o = out[c.id], ov = I[c.id].ov; ['pe', 'pfcf', 'evs'].forEach(m => { o[m] = ov[m] != null && ov[m] !== '' ? +ov[m] : mSeed[m]; I[c.id].sd[m] = mSeed[m]; });
      o.px_pe = o.eps != null && o.pe != null ? o.eps * o.pe : null; o.px_fcf = o.fcfps != null && o.pfcf != null ? o.fcfps * o.pfcf : null;
      o.ev = o.rev != null && o.evs != null ? o.rev * o.evs : null; o.px_evs = o.ev != null && T.shares ? (o.ev - (T.debt || 0) + (T.cash || 0)) / T.shares : null; });
    // ---- render ----
    const M = x => x == null || !isFinite(x) ? '' : (Math.abs(x) >= 1e9 ? (x / 1e9).toFixed(2) + 'B' : (x / 1e6).toFixed(1) + 'M');
    const P = x => x == null || !isFinite(x) ? '' : (x * 100).toFixed(1) + '%';
    const X = x => x == null || !isFinite(x) ? '' : (+x).toFixed(1) + 'x';
    const $ = x => x == null || !isFinite(x) ? '' : (+x).toFixed(2);
    const up = x => T.price && x != null && isFinite(x) ? `<div class="qr-s ${x >= T.price ? 'c-pos' : 'c-neg'}">${pct(x / T.price - 1)}</div>` : '';
    const kind = { rev_g: 'p', gm: 'p', opex_g: 'p', ebitm: 'p', below: 'm', tax: 'p', shares: 'm', cfo_m: 'p', capex_s: 'p', pe: 'x', pfcf: 'x', evs: 'x' };
    const show = (k, x) => x == null || !isFinite(x) ? '' : kind[k] === 'p' || /^seg/.test(k) ? (x * 100).toFixed(1) : kind[k] === 'm' ? (x / 1e6).toFixed(1) : (+x).toFixed(1);
    const inCell = (c, k, comp) => { if (c.id === 'A') return `<td class="n">${comp != null ? comp : ''}</td>`; const it = I[c.id], ovv = it.ov[k];
      const ph = k === 'ebitm' ? (out[c.id].rev ? out[c.id].ebit / out[c.id].rev : null) : it.sd[k];
      return `<td class="n qv-c"><input class="qv-in${ovv != null && ovv !== '' ? ' set' : ''}" data-c="${c.id}" data-k="${k}" value="${ovv != null && ovv !== '' ? esc(show(k, ovv)) : ''}" placeholder="${esc(show(k, ph))}" inputmode="decimal" title="Consensus default ${esc(show(k, it.sd[k]))}; type to override, clear to go back"></td>`; };
    const row = (lab, fn, cl) => `<tr class="${cl || ''}"><td class="qr-name">${lab}</td>${cols.map(c => `<td class="n">${fn(out[c.id], c)}</td>`).join('')}</tr>`;
    const inRow = (lab, k, actFn, unit) => `<tr class="qv-inr"><td class="qr-name">${lab} <span class="sub">${unit || ''}</span></td>${cols.map(c => inCell(c, k, c.id === 'A' ? actFn(out.A) : null)).join('')}</tr>`;
    const src = n => K[n] ? `<span class="sub" title="Visible Alpha line used: ${esc(K[n].name)}">ⓘ</span>` : (n ? '<span class="sub" title="No matching Visible Alpha line; enter it">—</span>' : '');
    let h = `<div class="qv-top"><label>Price <input class="qv-t" data-t="price" value="${esc(T.price ?? '')}" inputmode="decimal"></label>
      <label>Cash (M) ${src('cash')}<input class="qv-t" data-t="cash" value="${esc(T.cash != null ? (T.cash / 1e6).toFixed(1) : '')}" inputmode="decimal"></label>
      <label>Debt (M) ${src(K.debt_total ? 'debt_total' : 'debt_lt')}<input class="qv-t" data-t="debt" value="${esc(T.debt != null ? (T.debt / 1e6).toFixed(1) : '')}" inputmode="decimal"></label>
      <label>Diluted shares (M) <input class="qv-t" data-t="shares" value="${esc(T.shares != null ? (T.shares / 1e6).toFixed(1) : '')}" inputmode="decimal"></label>
      <span>Market cap <b class="mono">${M(mcap)}</b></span><span>EV <b class="mono">${M(ev)}</b></span>
      <span>Today on FY${String(Y0 + 1).slice(2)}E: <b class="mono">${X(mSeed.pe)}</b> P/E · <b class="mono">${X(mSeed.pfcf)}</b> P/FCF · <b class="mono">${X(mSeed.evs)}</b> EV/sales</span>
      <label><input type="checkbox" class="qv-seg" ${V.segMode ? 'checked' : ''}> Build revenue from segments</label>
      <button type="button" class="btn" data-qv="reset">Reset to consensus</button></div>`;
    h += `<div class="tbl-wrap"><table class="dt qr-t qv-t"><thead><tr><th>Scenario · ${esc(cfg.va_ticker || '')}</th>${cols.map(c => `<th class="n${c.id === 'U' ? ' qv-up' : c.id === 'D' ? ' qv-dn' : ''}">${c.h}</th>`).join('')}</tr></thead><tbody>`;
    h += `<tr class="qv-sec"><td colspan="6">Revenue</td></tr>`;
    segs.forEach(sg => { h += inRow(esc((sg.label || sg.name).trim()) + ' y/y', 'seg' + sg.kpi_id, a => { const b = v(sg.kpi_id, Y0 - 1); return a.seg[sg.kpi_id] != null && b ? P(a.seg[sg.kpi_id] / b - 1) : ''; }, '%');
      h += row('<span class="sub">' + esc((sg.label || sg.name).trim()) + '</span>', o => M(o.seg[sg.kpi_id]), 'qr-sub'); });
    h += inRow('Total revenue y/y' + (V.segMode ? ' <span class="sub">(other, when building from segments)</span>' : ''), 'rev_g', a => { const b = v(rev.kpi_id, Y0 - 1); return a.rev && b ? P(a.rev / b - 1) : ''; }, '%');
    h += row('<b>Revenue</b>', o => `<b>${M(o.rev)}</b>`, 'qr-main');
    h += `<tr class="qv-sec"><td colspan="6">P&amp;L</td></tr>`;
    h += inRow('Gross margin', 'gm', a => P(a.gp != null && a.rev ? a.gp / a.rev : null), '%');
    h += row('Gross profit', o => M(o.gp), 'qr-sub');
    h += inRow('Opex y/y', 'opex_g', a => { const g0 = gp && v(gp.kpi_id, Y0 - 1), o0 = oi && v(oi.kpi_id, Y0 - 1); return a.opex != null && g0 != null && o0 != null ? P(a.opex / (g0 - o0) - 1) : ''; }, '%');
    h += row('Opex', o => M(o.opex), 'qr-sub');
    h += inRow('EBIT margin', 'ebitm', a => P(a.ebit != null && a.rev ? a.ebit / a.rev : null), '% · blank = GP − opex');
    h += row('<b>EBIT</b>', o => `<b>${M(o.ebit)}</b>`, 'qr-main');
    h += inRow('Interest &amp; other below the line ' + src('pretax'), 'below', a => M(a.pretax != null && a.ebit != null ? a.pretax - a.ebit : null), 'M');
    h += row('Pre-tax income', o => M(o.pretax), 'qr-sub');
    h += inRow('Tax rate ' + src('tax'), 'tax', a => P(a.pretax && kv('tax', Y0) != null ? A(kv('tax', Y0)) / a.pretax : null), '%');
    h += row('Net income', o => M(o.ni), 'qr-sub');
    h += inRow('Diluted shares ' + src('shares'), 'shares', a => a.shares != null ? (a.shares / 1e6).toFixed(1) : '', 'M');
    h += row('<b>EPS</b>', o => `<b>${$(o.eps)}</b>`, 'qr-main');
    h += `<tr class="qv-sec"><td colspan="6">Cash flow</td></tr>`;
    h += inRow('CFO margin ' + src('cfo'), 'cfo_m', a => P(a.cfo != null && a.rev ? a.cfo / a.rev : null), '%');
    h += inRow('Capex / sales ' + src('capex'), 'capex_s', a => P(a.capex != null && a.rev ? a.capex / a.rev : null), '%');
    h += row('FCF margin', o => P(o.fcf != null && o.rev ? o.fcf / o.rev : null), 'qr-sub');
    h += row('FCF', o => M(o.fcf), 'qr-sub');
    h += row('<b>FCF / share</b>', o => `<b>${$(o.fcfps != null ? o.fcfps : o.fcf != null && o.shares ? o.fcf / o.shares : null)}</b>`, 'qr-main');
    h += `<tr class="qv-sec"><td colspan="6">Value</td></tr>`;
    h += inRow('P/E multiple', 'pe', () => '', 'x');
    h += row('Price on P/E', o => o.px_pe != null ? `<b>${$(o.px_pe)}</b>${up(o.px_pe)}` : '', 'qr-main');
    h += inRow('P/FCF multiple', 'pfcf', () => '', 'x');
    h += row('Price on FCF / share', o => o.px_fcf != null ? `<b>${$(o.px_fcf)}</b>${up(o.px_fcf)}` : '', 'qr-main');
    h += inRow('EV / sales multiple', 'evs', () => '', 'x');
    h += row('Implied EV', o => M(o.ev), 'qr-sub');
    h += row('Price on EV / sales', o => o.px_evs != null ? `<b>${$(o.px_evs)}</b>${up(o.px_evs)}` : '', 'qr-main');
    h += `</tbody></table></div><p class="sub qr-foot">Grey numbers in the boxes are consensus (Visible Alpha); type a number to override it and everything below and to the right recalculates. FY+2 builds on the FY+1 column, so changes there flow into the base, upside and downside. Amounts in millions in reporting currency; percents as 12.5. Price defaults to Master comps; cash and debt to the last reported fiscal year. ⓘ shows which Visible Alpha line was used. Save rows &amp; view to keep the scenario.</p>`;
    return h;
  }
  // Mount a live QR into `host` for company `co` ({t, bbg, name}); used by the Stocks tab and the Earnings cards.
  function qrMount(host, co) {
    if (!host || host.__qr) return; host.__qr = true;
    const st = { edit: false, yy: true, qq: true, mix: false, beat: false, mode: 'q', val: true, fresh: false, cfg: null, dq: null, dfy: null, msg: '', busy: false, viewSet: false };
    const bar = () => `<div class="ctl qr-bar" role="group" aria-label="Quarterly review controls">
      <button type="button" class="btn" data-qb="update" ${st.busy ? 'disabled' : ''}>${st.busy ? 'Loading…' : 'Update'}</button>
      <button type="button" class="btn" data-qb="edit" aria-pressed="${st.edit}">${st.edit ? 'Done editing' : 'Edit rows'}</button>
      <div class="seg"><button type="button" data-qb="m-q" aria-pressed="${st.mode === 'q'}">Quarters</button><button type="button" data-qb="m-fy" aria-pressed="${st.mode === 'fy'}">Fiscal years</button><button type="button" data-qb="m-both" aria-pressed="${st.mode === 'both'}">Both</button></div>
      <label><input type="checkbox" data-qo="yy" ${st.yy ? 'checked' : ''}> y/y</label>${st.mode === 'fy' ? '' : `<label><input type="checkbox" data-qo="qq" ${st.qq ? 'checked' : ''}> q/q</label>`}
      <label><input type="checkbox" data-qo="mix" ${st.mix ? 'checked' : ''}> % of revenue</label><label><input type="checkbox" data-qo="beat" ${st.beat ? 'checked' : ''}> vs consensus</label>
      ${st.mode === 'fy' ? '' : `<label>Quarters <select data-qo="nq">${[8, 12, 16].map(n => `<option${(st.cfg && st.cfg.nq || 12) === n ? ' selected' : ''}>${n}</option>`).join('')}</select></label>`}
      <button type="button" class="btn" data-qb="val" aria-pressed="${st.val}">${st.val ? 'Hide valuation' : 'Show upside / downside valuation'}</button>${st.val ? '<button type="button" class="btn" data-qb="jump">↓ Jump to valuation</button>' : ''}
      <span class="muted qr-msg">${esc(st.msg)}</span></div>`;
    const addUi = () => st.edit ? `<div class="qr-add"><label>Add a Visible Alpha KPI <input type="search" class="qr-kw" placeholder="e.g. gross margin, data center, bits, ASP"></label><button type="button" class="btn" data-qb="search">Search</button>
      ${st.cfg && st.cfg.rows.length > 1 ? `<label>or a ratio <select class="qr-num">${st.cfg.rows.filter(r => r.kind === 'kpi').map(r => `<option value="${r.kpi_id}">${esc(r.label || r.name)}</option>`).join('')}</select> ÷ <select class="qr-den">${st.cfg.rows.filter(r => r.kind === 'kpi').map(r => `<option value="${r.kpi_id}"${r.role === 'rev' ? ' selected' : ''}>${esc(r.label || r.name)}</option>`).join('')}</select></label><button type="button" class="btn" data-qb="ratio">Add ratio</button>` : ''}
      <button type="button" class="btn" data-qb="reset" title="Go back to the default rows from Visible Alpha">Reset to default</button><div class="qr-cands"></div></div>` : '';
    const sets = () => st.mode === 'q' ? (st.dq ? [{ data: st.dq, fy: false }] : null) : st.mode === 'fy' ? (st.dfy ? [{ data: st.dfy, fy: true }] : null) : (st.dq && st.dfy ? [{ data: st.dq, fy: false }, { data: st.dfy, fy: true }] : null);
    const valHtml = () => !st.val ? '' : `<section class="qv"><div class="panel-h"><h3>Upside / downside valuation · 5 columns: FY actual, FY+1, FY+2, Upside, Downside</h3><span class="muted">defaults to Visible Alpha consensus · type in a blue box to override</span></div><div class="qv-body">${(() => { if (st.verr) return `<p class="sub c-neg">Valuation could not load: ${esc(st.verr)}</p>`; if (!(st.dfy && st.cfg.valk)) return `<p class="sub">${esc(st.vstep || 'Loading consensus for the valuation…')}</p>`; try { return qrValModel(co, st.cfg, st.dfy, st); } catch (e) { console.error(e); return `<p class="sub c-neg">Valuation error: ${esc(e && e.message || e)} — tell Claude this message.</p>`; } })()}</div></section>`;
    const paint = () => {
      const S = st.cfg && sets();
      const body = !st.cfg ? `<p class="sub">${esc(st.msg || 'Loading Visible Alpha…')}</p>` : !S ? '<p class="sub">Loading Visible Alpha…</p>' : qrTable(co, st.cfg, S, st);
      host.innerHTML = bar() + addUi() + body + valHtml() + `<p class="sub qr-foot">Live from Visible Alpha through your SRS MCP connector: reported actuals in bold type, consensus in italics (E). Hover a number for reported vs consensus. <button type="button" class="btn" data-qb="save" title="Saves the rows, labels, notes, view choices and the valuation scenario, for everyone">Save rows, view &amp; scenario</button> ${st.cfg && st.cfg.updated ? 'Saved ' + esc(String(st.cfg.updated).slice(0, 10)) + '.' : ''}</p>`;
    };
    const paintVal = () => { const b = host.querySelector('.qv-body'); if (b && st.dfy && st.cfg.valk) { const f = document.activeElement, fk = f && f.dataset ? (f.dataset.c || '') + '|' + (f.dataset.k || f.dataset.t || '') : ''; try { b.innerHTML = qrValModel(co, st.cfg, st.dfy, st); } catch (e) { b.innerHTML = `<p class="sub c-neg">Valuation error: ${esc(e && e.message || e)}</p>`; return; } if (fk !== '|') { const n = b.querySelector(`[data-c="${(fk.split('|')[0])}"][data-k="${fk.split('|')[1]}"], [data-t="${fk.split('|')[1]}"]`); if (n) { n.focus(); try { n.setSelectionRange(n.value.length, n.value.length); } catch (e) {} } } } };
    const load = async () => {
      st.busy = true; st.msg = ''; paint();
      try {
        await QR.ready;
        if (!QR.mcp) { st.msg = 'Live Visible Alpha data needs the page open on claude.ai with the SRS MCP connector.'; st.busy = false; paint(); return; }
        if (!st.cfg) st.cfg = await qrLoadCfg(co);
        if (!st.viewSet) { st.viewSet = true; const v = st.cfg.view || {}; ['yy', 'qq', 'mix', 'beat', 'val'].forEach(k => { if (typeof v[k] === 'boolean') st[k] = v[k]; }); if (v.mode) st.mode = v.mode; }
        const needQ = st.mode !== 'fy' && (!st.dq || st.fresh), needF = (st.mode !== 'q' || st.val) && (!st.dfy || st.fresh);
        st.verr = '';
        if (st.val || st.mode !== 'q') { st.vstep = 'Finding the Visible Alpha line items (tax, shares, cash flow, cash, debt)…'; paint(); try { await qrValKpis(st.cfg); } catch (e) { st.verr = 'line-item search failed: ' + vaErr(e); } }
        st.vstep = 'Loading fiscal-year consensus…'; if (st.val) paint();
        const extra = Object.values(st.cfg.valk || {}).map(x => x.id);
        const [q, f] = await Promise.all([needQ ? qrData(st.cfg, st.fresh, false) : null, needF ? qrData(st.cfg, st.fresh, true, extra) : null]);
        if (q) st.dq = q; if (f) st.dfy = f;
        const errs = [].concat(q ? q.errs : [], f ? f.errs : []);
        st.msg = errs.length ? `${errs.length} line${errs.length > 1 ? 's' : ''} failed: ${vaErr(errs[0])}` : (st.fresh ? 'Updated from Visible Alpha just now.' : '');
      } catch (e) { st.msg = e && e.code === 'no_va' ? `${co.t} is not in Visible Alpha (${e.message}).` : vaErr(e); }
      st.busy = false; st.fresh = false; paint();
    };
    const readInputs = () => { host.querySelectorAll('.qr-lbl').forEach(x => { st.cfg.rows[+x.dataset.i].label = x.value; }); host.querySelectorAll('.qr-note').forEach(x => { st.cfg.rows[+x.dataset.i].note = x.value.trim(); }); };
    host.addEventListener('click', async e => {
      const b = e.target.closest('[data-qb],[data-qa],[data-qk],[data-qv]'); if (!b) return;
      if (b.dataset.qv === 'reset') { if (st.cfg.val) { st.cfg.val.inp = {}; st.cfg.val.top = {}; } paintVal(); return; }
      if (b.dataset.qa) { readInputs(); const i = +b.dataset.i, R = st.cfg.rows; if (b.dataset.qa === 'rm') R.splice(i, 1); else { const j = b.dataset.qa === 'up' ? i - 1 : i + 1; if (j >= 0 && j < R.length) [R[i], R[j]] = [R[j], R[i]]; } paint(); return; }
      if (b.dataset.qk) { readInputs(); const k = JSON.parse(b.dataset.qk); if (!st.cfg.rows.some(r => r.kpi_id === k.kpi_id)) st.cfg.rows.push({ kind: 'kpi', kpi_id: k.kpi_id, name: k.kpi_name, label: k.kpi_name }); st.dq = st.dfy = null; paint(); load(); return; }
      const a = b.dataset.qb;
      if (a === 'update') { st.fresh = true; load(); }
      else if (a === 'edit') { if (st.edit) readInputs(); st.edit = !st.edit; paint(); }
      else if (a === 'm-q' || a === 'm-fy' || a === 'm-both') { st.mode = a.slice(2); load(); }
      else if (a === 'val') { st.val = !st.val; if (st.val) { await load(); const q = host.querySelector('.qv'); if (q) q.scrollIntoView({ block: 'start', behavior: 'smooth' }); } else paint(); }
      else if (a === 'jump') { const q = host.querySelector('.qv'); if (q) q.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
      else if (a === 'search') {
        const kw = (host.querySelector('.qr-kw') || {}).value || '', box = host.querySelector('.qr-cands'); if (!kw.trim() || !box) return;
        box.innerHTML = '<span class="sub">Searching…</span>';
        try { const x = await vaCall({ action: 'list_kpis', va_company_id: st.cfg.va_company_id, search: [kw.trim()], period_type: st.mode === 'fy' ? 'FY' : 'QTR' }); const cs = arr(x.candidates || (x.selection ? [x.selection] : []));
          box.innerHTML = cs.length ? cs.slice(0, 40).map(c => `<button type="button" class="chip out" data-qk="${esc(JSON.stringify({ kpi_id: c.kpi_id, kpi_name: c.kpi_name }))}">+ ${esc(c.kpi_name)} <span class="sub">${esc(c.period_count || '')}</span></button>`).join(' ') : `<span class="sub">${esc(x.display_message || 'No KPIs match.')}</span>`;
        } catch (err) { box.innerHTML = `<span class="sub">${esc(vaErr(err))}</span>`; }
      }
      else if (a === 'ratio') { readInputs(); const num = +host.querySelector('.qr-num').value, den = +host.querySelector('.qr-den').value; const nm = r => (st.cfg.rows.find(x => x.kpi_id === r) || {}).label || ''; st.cfg.rows.push({ kind: 'ratio', num, den, label: `${nm(num).trim()} / ${nm(den).trim()}` }); paint(); load(); }
      else if (a === 'save') { if (st.edit) readInputs(); st.cfg.view = { yy: st.yy, qq: st.qq, mix: st.mix, beat: st.beat, mode: st.mode, val: st.val }; try { await qrSave(co, st.cfg); st.cfg.auto = false; st.cfg.updated = new Date().toISOString(); st.msg = 'Saved.'; } catch (err) { st.msg = 'Not saved: ' + ((err && (err.code || err.message)) || 'error'); } paint(); }
      else if (a === 'reset') { if (!confirm('Go back to the default Visible Alpha rows for ' + co.t + '? Your saved rows, notes and scenario for this company are removed.')) return; try { if (QR.db) await QR.db.collection('qr').doc(qrId(co.t)).delete(); } catch (err) {} QR.cfg.delete(qrId(co.t)); st.cfg = null; st.dq = st.dfy = null; load(); }
    });
    // valuation inputs: percents typed as 12.5, amounts in millions, multiples as 18
    host.addEventListener('change', e => {
      const t = e.target;
      if (t.classList.contains('qv-seg')) { st.cfg.val = st.cfg.val || { inp: {}, top: {} }; st.cfg.val.segMode = t.checked; paintVal(); return; }
      if (t.classList.contains('qv-in') || t.classList.contains('qv-t')) return;
      const o = t.dataset.qo; if (!o) return; if (o === 'nq') { if (st.edit) readInputs(); st.cfg.nq = +t.value; } else st[o] = t.checked; paint();
    });
    host.addEventListener('input', e => {
      const t = e.target; if (!t.classList.contains('qv-in') && !t.classList.contains('qv-t')) return;
      clearTimeout(host.__qvT); host.__qvT = setTimeout(() => {
        const V = st.cfg.val = st.cfg.val || { inp: {}, top: {}, segMode: false }; V.inp = V.inp || {}; V.top = V.top || {};
        const raw = t.value.trim().replace(/,/g, ''), num = raw === '' ? null : +raw.replace(/[%x$]/g, '');
        if (raw !== '' && !isFinite(num)) return;
        if (t.classList.contains('qv-t')) { const k = t.dataset.t; if (num == null) delete V.top[k]; else V.top[k] = k === 'price' ? num : num * 1e6; }
        else { const c = t.dataset.c, k = t.dataset.k; V.inp[c] = V.inp[c] || {};
          V.inp[c][k] = num == null ? null : (['pe', 'pfcf', 'evs'].includes(k) ? num : ['below', 'shares'].includes(k) ? num * 1e6 : num / 100); }
        paintVal();
      }, 450);
    });
    load();
  }
  // ---- top scrollbar on every wide table: a thin scroller above the table, synced with the table's own ----
  function topScroll(wrap) {
    if (!wrap || wrap.__ts) return;
    const t = wrap.querySelector('table'); if (!t) return;
    wrap.__ts = true;
    const bar = document.createElement('div'); bar.className = 'tbl-top'; bar.setAttribute('aria-hidden', 'true');
    const inner = document.createElement('div'); bar.appendChild(inner); wrap.parentNode.insertBefore(bar, wrap);
    const size = () => { inner.style.width = wrap.scrollWidth + 'px'; bar.style.display = wrap.scrollWidth > wrap.clientWidth + 2 ? '' : 'none'; };
    let lock = false;
    bar.addEventListener('scroll', () => { if (lock) return; lock = true; wrap.scrollLeft = bar.scrollLeft; lock = false; });
    wrap.addEventListener('scroll', () => { if (lock) return; lock = true; bar.scrollLeft = wrap.scrollLeft; lock = false; });
    size(); if (window.ResizeObserver) new ResizeObserver(size).observe(t); window.addEventListener('resize', size);
  }
  const tsScan = () => document.querySelectorAll('.tbl-wrap').forEach(topScroll);
  new MutationObserver(() => { clearTimeout(tsScan.t); tsScan.t = setTimeout(tsScan, 60); }).observe(document.body, { childList: true, subtree: true });
  window.__qrMount = qrMount;
  window.__qrFind = t => { const ST = arr((D.stocks || {}).companies), k = ntKey(t); return ST.find(c => ntKey(c.t) === k || ntKey(c.bbg) === k || ntKey(c.t).split(' ')[0] === k) || null; };

  // ================= ROUTINES: one page per scheduled routine =================
  window.__onFull = () => { const h = location.hash || ''; if (h.startsWith('#routines')) renderRoutines(); else if (h.startsWith('#stocks/') && !/\/(thesis|qr|datapoints|earnings|management)$/.test(h)) renderStocks(); };
  function renderRoutines() {
    const RT = D.routines || {}, list = arr(RT.routines);
    const host = document.getElementById('v-routines');
    const key = ((location.hash || '').split('/')[1] || (list[0] && list[0].key) || '');
    const cur = list.find(r => r.key === key) || list[0];
    const dotCls = st => st === 'ok' ? 'fresh' : st === 'missed' ? 'stale' : 'aging';
    const sent = s => s === 'positive' ? 'pos' : s === 'negative' ? 'neg' : 'mix';
    const nav = `<nav class="rt-nav" aria-label="Routines">${list.map(r => `<a href="#routines/${esc(r.key)}"${cur && r.key === cur.key ? ' aria-current="page"' : ''}><i class="dot ${dotCls(r.status)}"></i><span><b>${esc(r.name)}</b><span class="sub">${esc(r.schedule || '')}</span></span></a>`).join('')}</nav>`;
    let body = none('No routine output collected yet.');
    if (cur) {
      const runs = lim(arr(cur.runs).filter(r => inWin(r.date, null)), 14);
      const runIx = Math.min(+((location.hash || '').split('/')[2] || 0), Math.max(0, runs.length - 1));
      const sel = runs[runIx];
      const FULL = window.__FULL || {}, fp = sel && FULL[String(sel.url || '').split('?')[0]];
      const fullHtml = !sel ? '' : fp ? `<section class="panel rt-full"><div class="panel-h"><h2>${esc(fp.title || sel.title)}</h2>${link(sel.url, 'Notion')}</div>${fp.sections.map((x, i) =>
          `<details class="fr-sec"${i < 3 ? ' open' : ''}><summary>${x.title}</summary>${x.subs ? `<div class="fr-body">${x.subs.map(u => `<details class="fr-sec fr-sub" open><summary>${u.title}</summary><div class="fr-html">${u.html}</div></details>`).join('')}</div>` : `<div class="fr-html">${x.html}</div>`}</details>`).join('')}</section>`
        : (window.__FULL ? `<section class="panel">${none('The full page for this run is not in this build yet.')}${link(sel.url, 'Open in Notion')}</section>` : `<section class="panel"><p class="sub">Loading the full page…</p></section>`);
      const runPick = runs.length > 1 ? `<div class="rt-runs" role="tablist" aria-label="Runs">${runs.map((r, i) => `<a role="tab" href="#routines/${esc(cur.key)}/${i}"${i === runIx ? ' aria-selected="true"' : ''}>${esc(fmtD(r.date))}${r.created ? ' <span class="sub">' + esc(String(r.created).slice(11, 16)) + '</span>' : ''}</a>`).join('')}</div>` : '';
      const li = x => `<div class="li"><span class="stripe ${sent(x.sentiment)}"></span><div class="body">${x.ticker ? tk(x.ticker) + ' ' : ''}${attr(x.text || '')}${x.sb_id ? ` <span class="sub mono">SB #${esc(x.sb_id)}</span>` : ''}</div></div>`;
      const secs = Object.entries(cur.by_sector || {});
      body = `<section class="panel"><div class="panel-h"><h2>${esc(cur.name)}</h2><span class="muted"><i class="dot ${dotCls(cur.status)}"></i> ${esc(cur.status || '')}${cur.last_run ? ' · last run ' + esc(cur.last_run) : ''}</span></div>` +
        `<p class="sub" style="margin:0 0 8px">${esc(cur.schedule || '')}${cur.note ? ' · ' + attr(cur.note) : ''}</p>` +
        (sel ? `<p style="margin:0">${sel.window ? esc(sel.window) : ''}${sel.supabase_line ? ' · ' + esc(sel.supabase_line) : ''}</p>` : '') + runPick + `</section>` +
        (fp ? fullHtml : fullHtml + 
        (arr(cur.callouts).length ? `<section class="panel"><h2>Call-outs</h2><div class="list">${lim(cur.callouts).map(li).join('')}</div></section>` : '') +
        (arr(cur.themes).length ? `<section class="panel"><h2>Themes</h2>${arr(cur.themes).map(t => `<div class="theme"><h3>${esc(t.theme || '')}</h3><p>${attr(t.whats_changing || '')}</p>${(arr(t.winners).length || arr(t.losers).length) ? `<div class="wl">${arr(t.winners).length ? `<span>Benefits</span>${arr(t.winners).map(x => tk(x, 'up')).join(' ')}` : ''}${arr(t.losers).length ? `<span>Hurt</span>${arr(t.losers).map(x => tk(x, 'down')).join(' ')}` : ''}</div>` : ''}</div>`).join('')}</section>` : '') +
        (arr(cur.revisions).length ? `<section class="panel"><h2>Revisions</h2><div class="list">${arr(cur.revisions).map(x => li({ ticker: x.ticker, text: [x.metric, x.change, x.text].filter(Boolean).join(' · '), sentiment: x.sentiment || (String(x.change || '').trim().startsWith('-') ? 'negative' : 'positive') })).join('')}</div></section>` : '') +
        (arr(cur.ideas).length ? `<section class="panel"><h2>Ideas</h2><div class="list">${arr(cur.ideas).map(x => li({ ticker: x.ticker, text: (x.bucket ? '<b>' + esc(x.bucket) + '</b> · ' : '') + esc(x.thesis || x.text || ''), sentiment: /short/i.test(x.bucket || '') ? 'negative' : 'positive' })).join('')}</div></section>` : '') +
        (secs.length ? `<section class="panel"><h2>Datapoints by sector</h2>${secs.map(([g, xs]) => `<details class="rt-sec"><summary><b>${esc(g)}</b> <span class="sub">${arr(xs).length}</span></summary><div class="list">${arr(xs).map(li).join('')}</div></details>`).join('')}</section>` : '') +
        '') +
        (runs.length ? `<section class="panel"><h2>Recent runs</h2><table class="dt"><thead><tr><th>Run</th><th>Window</th><th class="n">Datapoints</th><th>Supabase</th></tr></thead><tbody>${runs.map((r, i) => `<tr><td><a href="#routines/${esc(cur.key)}/${i}">${esc(r.title || r.date)}</a> ${link(r.url, '')}</td><td class="sub">${esc(r.window || '')}</td><td class="n">${esc(r.datapoint_count ?? '')}</td><td class="sub">${esc(r.supabase_line || '')}</td></tr>`).join('')}</tbody></table></section>` : '');
    }
    host.innerHTML = head('Routines' + (RT.as_of ? ' · ' + esc(RT.as_of) : ''), 'Your scheduled research routines', 'One page per routine: its latest call-outs, themes and datapoints, whether it ran on schedule, and its recent runs. The Daily moves reasons are drawn from these first.') +
      `<div class="rt-wrap">${nav}<div class="rt-body">${body}</div></div>`;
  }

  // ================= PIPELINE: every long and short being tracked =================
  function renderPipeline() {
    const P = D.pipeline || {}, items = arr(P.items), host = document.getElementById('pl-host'); if (!host) return;
    const moves = new Map(arr(DLY.moves).map(m => [String(m.t).toUpperCase(), m]));
    const pctTxt = v => v == null || !isFinite(v) ? '' : (v > 0 ? '+' : '') + Math.round(v * 100) + '%';
    const upOf = it => { const u = it.upside; if (!u) return null; const lo = u.pct_low, hi = u.pct_high; const v = hi != null ? hi : lo; return v == null ? null : v; };
    const secs = [...new Set(items.map(i => i.sector).filter(Boolean))].sort();
    const st = { dir: '', status: '', sec: '', q: '', sort: 'status' };
    host.innerHTML = `<section class="panel"><div class="panel-h"><h2>Pipeline · longs &amp; shorts we are tracking</h2><span class="muted">${P.as_of ? 'as of ' + esc(P.as_of) : ''}</span></div><p class="sub" style="margin:0">Every name on the Pipeline/Active/Ideas page, the Shorts database, recent Idea Generator runs and thesis pages: the elevator pitch, and the upside or downside where a target has been written down.</p></section>` +
      (arr(P.themes).length ? `<section class="panel"><h2>Themes</h2><div class="pl-themes">${arr(P.themes).map(t => `<div class="theme"><div class="panel-h"><h3>${esc(t.name)}</h3>${t.status ? `<span class="chip out">${esc(t.status)}</span>` : ''}</div><p>${attr(t.pitch || '')}</p>${arr(t.names).length ? `<div class="wl">${arr(t.names).map(x => tk(x)).join(' ')}</div>` : ''}</div>`).join('')}</div></section>` : '') +
      `<div class="ctl" role="group" aria-label="Pipeline filters">
        <label for="pl-q">Search <input type="search" id="pl-q" placeholder="Ticker, company or word"></label>
        <div class="seg" id="pl-dir"><button type="button" data-v="" aria-pressed="true">Longs & shorts</button><button type="button" data-v="long" aria-pressed="false">Longs</button><button type="button" data-v="short" aria-pressed="false">Shorts</button></div>
        <div class="seg" id="pl-st"><button type="button" data-v="" aria-pressed="true">Any status</button><button type="button" data-v="active" aria-pressed="false">Active</button><button type="button" data-v="tracking" aria-pressed="false">Tracking</button><button type="button" data-v="idea" aria-pressed="false">Ideas</button></div>
        <label for="pl-sec">Sector <select id="pl-sec"><option value="">All</option>${secs.map(s => `<option>${esc(s)}</option>`).join('')}</select></label>
        <label for="pl-sort">Sort <select id="pl-sort"><option value="status">Status</option><option value="up">Upside / downside</option><option value="recent">Most recent</option><option value="az">Ticker A–Z</option></select></label>
        <span class="count" id="pl-count"></span></div>
      <div id="pl-list" class="pl-list"></div>`;
    const $ = id => document.getElementById(id);
    function card(it) {
      const u = it.upside, m = moves.get(String(it.ticker || '').toUpperCase());
      const lo = u && u.pct_low, hi = u && u.pct_high;
      const upTxt = u ? (lo != null && hi != null && Math.abs(hi - lo) > 0.005 ? `${pctTxt(lo)} to ${pctTxt(hi)}` : lo != null || hi != null ? pctTxt(hi != null ? hi : lo) : (u.as_written_pct || '')) : '';
      const good = v => it.direction === 'short' ? v < 0 : v > 0;
      const upV = upOf(it);
      return `<article class="pl-card ${it.direction === 'short' ? 'short' : 'long'}">
        <div class="pl-h">${tk(it.ticker)} <b>${esc(it.company || '')}</b>
          <span class="chip ${it.direction === 'short' ? 'dn' : 'up'}">${esc(it.direction || '')}</span>
          ${it.status ? `<span class="chip out">${esc(it.status)}</span>` : ''}${it.conviction ? `<span class="chip out">${esc(it.conviction)}</span>` : ''}
          ${noteUI('pipe:' + ntKey(it.ticker), it.ticker, (it.company || it.ticker) + ' (' + (it.direction || '') + ')')}
          <span class="pl-up">${upTxt ? `<span class="mono ${upV == null ? '' : good(upV) ? 'c-pos' : 'c-neg'}" title="${esc(u.basis || '')}">${esc(upTxt)}</span><span class="sub"> ${it.direction === 'short' ? 'to target' : 'to target'}</span>` : '<span class="sub">no target written</span>'}</span></div>
        <p class="pl-pitch">${attr(it.pitch || '')}</p>
        <div class="pl-meta sub">${[it.sector, it.theme].filter(Boolean).map(esc).join(' · ')}${it.price != null ? ` · px ${esc(it.price)}` : ''}${m ? ` · today <span class="mono ${+m.c >= 0 ? 'c-pos' : 'c-neg'}">${(+m.c > 0 ? '+' : '') + (+m.c).toFixed(1)}%</span>` : ''}${it.added ? ` · added ${esc(it.added)}` : ''}${it.updated && it.updated !== it.added ? ` · updated ${esc(it.updated)}` : ''}</div>
        ${u && u.basis ? `<div class="pl-basis sub">Target basis: ${esc(u.basis)}</div>` : ''}
        ${arr(it.catalysts).length || it.key_risk ? `<div class="pl-cr">${arr(it.catalysts).length ? `<span><b>Catalysts</b> ${arr(it.catalysts).map(esc).join(' · ')}</span>` : ''}${it.key_risk ? `<span><b>Risk</b> ${esc(it.key_risk)}</span>` : ''}</div>` : ''}
        ${arr(it.sources).length ? `<div class="pl-src">${arr(it.sources).map(s => s.url ? link(s.url, s.label || 'Source') : `<span class="sub">${esc(s.label || '')}</span>`).join(' ')}</div>` : ''}
      </article>`;
    }
    const SO = { active: 0, tracking: 1, idea: 2 };
    function draw() {
      let list = items.filter(it => inWin(it.updated || it.added, null) && (!st.dir || it.direction === st.dir) && (!st.status || it.status === st.status) && (!st.sec || it.sector === st.sec) &&
        (!st.q || `${it.ticker} ${it.company} ${it.pitch} ${it.theme}`.toLowerCase().includes(st.q)));
      if (st.sort === 'up') list = list.slice().sort((a, b) => { const x = upOf(a), y = upOf(b); const fx = x == null ? -9 : (a.direction === 'short' ? -x : x), fy = y == null ? -9 : (b.direction === 'short' ? -y : y); return fy - fx; });
      else if (st.sort === 'recent') list = list.slice().sort((a, b) => String(b.updated || b.added || '').localeCompare(String(a.updated || a.added || '')));
      else if (st.sort === 'az') list = list.slice().sort((a, b) => String(a.ticker).localeCompare(String(b.ticker)));
      else list = list.slice().sort((a, b) => (SO[a.status] ?? 3) - (SO[b.status] ?? 3) || (a.direction === 'short') - (b.direction === 'short'));
      const tot = list.length; list = lim(list);
      const nl = list.filter(i => i.direction === 'long').length;
      $('pl-count').textContent = `${tot > list.length ? 'showing ' + list.length + ' of ' + tot : list.length} names · ${nl} long / ${list.length - nl} short`;
      $('pl-list').innerHTML = list.length ? list.map(card).join('') : none('Nothing matches these filters.');
    }
    const seg = (id, key) => host.querySelectorAll('#' + id + ' button').forEach(b => b.addEventListener('click', () => { st[key] = b.dataset.v; host.querySelectorAll('#' + id + ' button').forEach(x => x.setAttribute('aria-pressed', String(x === b))); draw(); }));
    seg('pl-dir', 'dir'); seg('pl-st', 'status');
    $('pl-q').addEventListener('input', e => { st.q = e.target.value.trim().toLowerCase(); draw(); });
    $('pl-sec').addEventListener('change', e => { st.sec = e.target.value; draw(); });
    $('pl-sort').addEventListener('change', e => { st.sort = e.target.value; draw(); });
    if (!items.length) { $('pl-list').innerHTML = none('No pipeline in this build yet.'); return; }
    draw();
  }

  // ================= NOTES: Bobby's own notes on any card, saved in the page's database (survive every rebuild) =================
  // a note: notes/<id> {target, ticker, label, text, created, updated}; target ids: earn:<TICKER>|<date>, stock:<key>,
  // pipe:<TICKER>, idea:<TICKER>|<date>, move:<TICKER>|<date>, page:<view>
  const NOTES = { db: null, list: [], ready: false, err: '' };
  const ntKey = t => String(t || '').toUpperCase().replace(/\s+EQUITY$/, '').replace(/\s+(US|UW|UN|UQ)$/, '').replace(/\s+JT$/, ' JP').trim();
  window.__noteUI = (target, ticker, label) => `<span class="nt" data-nt="${esc(target)}" data-tk="${esc(ntKey(ticker))}" data-lb="${esc(label || '')}"></span>`;
  const noteUI = window.__noteUI;
  function paintTickerNotes() {
    const box = document.getElementById('sk-tnotes'); if (!box) return;
    const ks = new Set([box.dataset.tk, box.dataset.tk2, String(box.dataset.tk || '').split(' ')[0]].filter(Boolean));
    const xs = NOTES.list.filter(n => ks.has(ntKey(n.ticker)) || ks.has(ntKey(n.ticker).split(' ')[0]));
    const kind = t => ({ earn: 'Earnings', stock: 'Stock', pipe: 'Pipeline', idea: 'Idea', move: 'Move' })[String(t).split(':')[0]] || 'Note';
    box.innerHTML = xs.length ? `<div class="sk-tn">${xs.map(n => `<div class="sk-tni"><span class="chip out">${kind(n.target)}</span> <span class="sub">${esc(new Date(n.updated || n.created).toLocaleDateString([], { month: 'short', day: 'numeric' }))}${n.label ? ' · ' + esc(n.label) : ''}</span><div style="white-space:pre-wrap">${esc(n.text)}</div></div>`).join('')}</div>` : '';
  }
  function paintNotes(root) {
    paintTickerNotes();
    (root || document).querySelectorAll('.nt').forEach(el => {
      const mine = NOTES.list.filter(n => n.target === el.dataset.nt);
      const open = el.dataset.open === '1';
      el.innerHTML = `<button type="button" class="nt-btn${mine.length ? ' has' : ''}" aria-expanded="${open}" title="${NOTES.db ? 'Add or read notes' : 'Notes are not available in this view'}">📝${mine.length ? ' ' + mine.length : ''}</button>` +
        (open ? `<div class="nt-pop">${mine.map(n => `<div class="nt-item" data-id="${esc(n.id)}"><div class="nt-meta sub">${esc(new Date(n.updated || n.created).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }))}</div><div class="nt-text">${esc(n.text)}</div><button type="button" class="nt-del sub" aria-label="Delete note">Delete</button></div>`).join('')}
          ${NOTES.db ? `<textarea class="nt-in" rows="3" placeholder="Your note on ${esc(el.dataset.lb || el.dataset.tk || 'this')}…"></textarea><div class="nt-act"><button type="button" class="btn nt-save">Save note</button></div>` : `<p class="sub">${esc(NOTES.err || 'Notes need the page open on claude.ai.')}</p>`}</div>` : '');
    });
  }
  document.addEventListener('click', async e => {
    const host = e.target.closest('.nt'); if (!host) return;
    if (e.target.closest('.nt-btn')) { host.dataset.open = host.dataset.open === '1' ? '0' : '1'; paintNotes(host.parentNode); if (host.dataset.open === '1') { const t = host.querySelector('.nt-in'); if (t) t.focus(); } return; }
    if (e.target.closest('.nt-save') && NOTES.db) {
      const ta = host.querySelector('.nt-in'), text = (ta && ta.value || '').trim(); if (!text) return;
      const b = e.target.closest('.nt-save'); b.disabled = true; b.textContent = 'Saving…';
      try { const now = new Date().toISOString(); await NOTES.db.collection('notes').doc().set({ target: host.dataset.nt, ticker: host.dataset.tk, label: host.dataset.lb, text, created: now, updated: now }); }
      catch (x) { b.disabled = false; b.textContent = 'Save note'; alert('Could not save the note: ' + ((x && x.message) || 'error')); }
      return;
    }
    if (e.target.closest('.nt-del') && NOTES.db) { const id = e.target.closest('.nt-item').dataset.id; if (confirm('Delete this note?')) { try { await NOTES.db.collection('notes').doc(id).delete(); } catch (x) { alert('Could not delete: ' + ((x && x.message) || 'error')); } } }
  });
  new MutationObserver(ms => { if (ms.some(m => [...m.addedNodes].some(n => n.nodeType === 1 && (n.matches && n.matches('.nt') || n.querySelector && n.querySelector('.nt:empty'))))) paintNotes(); })
    .observe(document.body, { childList: true, subtree: true });
  if (window.claude && typeof window.claude.use === 'function') {
    window.claude.use('db').then(db => {
      if (!db) { NOTES.err = 'Notes are not available in this view (sign in on claude.ai).'; paintNotes(); return; }
      NOTES.db = db;
      db.collection('notes').onSnapshot(snap => {
        NOTES.list = snap.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => String(b.updated || b.created).localeCompare(String(a.updated || a.created)));
        NOTES.ready = true; paintNotes(); if ((location.hash || '').startsWith('#notes')) renderNotes();
        const c = document.getElementById('nt-count'); if (c) c.textContent = NOTES.list.length ? NOTES.list.length : '';
      }, err => { NOTES.err = 'Notes could not load: ' + ((err && err.code) || 'error'); paintNotes(); });
    }).catch(() => { NOTES.err = 'Notes are not available in this view.'; });
  } else NOTES.err = 'Notes need the page open on claude.ai.';
  function renderNotes() {
    const host = document.getElementById('v-notes'); if (!host) return;
    const q = (host.__q || '').toLowerCase();
    const xs = NOTES.list.filter(n => !q || `${n.ticker} ${n.label} ${n.text}`.toLowerCase().includes(q));
    const where = t => { const [k, v] = String(t).split(':'); const tk = String(v || '').split('|')[0];
      return k === 'earn' ? `#earnings` : k === 'stock' ? `#stocks/${encodeURIComponent(v)}/debate` : k === 'pipe' ? '#ideas' : k === 'idea' ? '#ideas' : k === 'move' ? '#daily' : '#' + (v || 'today'); };
    const kind = t => ({ earn: 'Earnings', stock: 'Stock', pipe: 'Pipeline', idea: 'Idea', move: 'Daily move', page: 'Page' })[String(t).split(':')[0]] || 'Note';
    host.innerHTML = head('Notes', 'Your notes', 'Every note you have left on a card, newest first. Notes live in this page’s own database, so rebuilds never erase them.') +
      `<div class="ctl"><label for="nt-q">Search <input type="search" id="nt-q" value="${esc(host.__q || '')}" placeholder="Ticker or word"></label><span class="count">${xs.length} notes</span></div>` +
      (NOTES.db ? '' : `<p class="sub">${esc(NOTES.err || 'Loading…')}</p>`) +
      `<div class="list">${xs.map(n => `<div class="li"><div class="body">${n.ticker ? tk(n.ticker) + ' ' : ''}<span class="chip out">${kind(n.target)}</span> <b>${esc(n.label || '')}</b> <a href="${where(n.target)}" class="sub">open →</a><div style="white-space:pre-wrap">${esc(n.text)}</div><div class="sub">${esc(new Date(n.updated || n.created).toLocaleString())}</div></div></div>`).join('') || none('No notes yet. Click 📝 on any earnings print, stock, pipeline card, idea or mover.')}</div>`;
    const qi = document.getElementById('nt-q'); qi.addEventListener('input', e => { host.__q = e.target.value; const p = e.target.selectionStart; renderNotes(); const n = document.getElementById('nt-q'); n.focus(); n.setSelectionRange(p, p); });
  }

  // ================= X / TWITTER (live from the X List Monitor pages in Notion) =================
  const XT = { mcp: null, pages: null, sel: null, cache: new Map(), seen: new Map(), err: '', busy: false };
  const XN = 'Notion';
  const xCall = (tool, input, fresh) => XT.mcp.callTool(XN, tool, input, { cache: fresh ? { refresh: true, staleTime: 10 * 60e3, gcTime: 864e5 } : { staleTime: 10 * 60e3, gcTime: 864e5 } }).then(r => r.payload);
  const xId = u => (String(u || '').match(/([0-9a-f]{32})/i) || [])[1] || String(u || '').replace(/-/g, '');
  // Notion markdown -> safe HTML (escape everything, then rebuild a small allow-list)
  function xInline(s) {
    let h = esc(s);
    h = h.replace(/&lt;(\/?)(b|strong|i|em|code|u)&gt;/g, '<$1$2>').replace(/&lt;br\s*\/?&gt;/g, '<br>');
    h = h.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
    h = h.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (m, t, u) => `<a href="${u.replace(/&amp;/g, '&').replace(/"/g, '%22')}" target="_blank" rel="noopener">${t}</a>`);
    h = h.replace(/\\([$~_*\[\]()#>-])/g, '$1');
    return h;
  }
  function xParse(md) {
    // returns a tree of blocks: {t:'h'|'p'|'li'|'table'|'callout'|'toggle', ...}
    const lines = String(md || '').split('\n'); let i = 0;
    function block(stop) {
      const out = [];
      while (i < lines.length) {
        const raw = lines[i], l = raw.trim();
        if (stop && stop.test(l)) { i++; return out; }
        let m;
        if (!l) { i++; continue; }
        if ((m = l.match(/^<callout(?:\s+icon="([^"]*)")?(?:\s+color="([^"]*)")?[^>]*>(.*)$/))) { i++; const kids = block(/^<\/callout>/); out.push({ t: 'callout', icon: m[1] || '', color: m[2] || '', kids }); continue; }
        if (/^<details>|^<toggle>/.test(l)) { i++; let title = ''; while (i < lines.length && !lines[i].trim()) i++; if (i < lines.length) { title = lines[i].trim().replace(/^<summary>|<\/summary>$/g, ''); i++; } const kids = block(/^<\/toggle>|^<\/details>/); out.push({ t: 'toggle', title, kids }); continue; }
        if ((m = l.match(/^(#{1,4})\s+(.*)$/))) { i++; out.push({ t: 'h', lvl: m[1].length, text: m[2] }); continue; }
        if (/^\|/.test(l)) { const rows = []; while (i < lines.length && /^\|/.test(lines[i].trim())) { const r = lines[i].trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()); if (!r.every(c => /^:?-{2,}:?$/.test(c))) rows.push(r); i++; } out.push({ t: 'table', rows }); continue; }
        if ((m = l.match(/^(?:[-*]|\d+\.)\s+(.*)$/))) { i++; out.push({ t: 'li', text: m[1], depth: (raw.match(/^\s*/)[0].replace(/\t/g, '    ').length / 2) | 0 }); continue; }
        if (/^<\/?(page|content|ancestor|properties|iconMetadata)/.test(l)) { i++; continue; }
        i++; out.push({ t: 'p', text: l });
      }
      return out;
    }
    return block(null);
  }
  const xText = b => b.text != null ? b.text : b.title != null ? b.title : '';
  const xPlain = s => String(s || '').replace(/<[^>]+>/g, '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\\(.)/g, '$1').replace(/\*\*/g, '').trim();
  const xSig = s => /🟢🟢/.test(s) ? 'vp' : /🔴🔴/.test(s) ? 'vn' : /🟢/.test(s) ? 'p' : /🔴/.test(s) ? 'n' : /🔵/.test(s) ? 'w' : /🟠|🟡/.test(s) ? 'm' : '';
  // a run time the agent wrote on a bullet: "🕐 11:05", "🆕 11:05 ET", "[11:05 ET]", "(added 11:05 ET)"
  const XAT = /\s*(?:🕐|🆕|⏱️?)\s*(\d{1,2}:\d{2})\s*(AM|PM|am|pm)?\s*(?:ET)?\s*|\s*[\[(](?:added\s+|new\s+)?(\d{1,2}:\d{2})\s*(AM|PM|am|pm)?\s*ET[\])]\s*/;
  const xAt = s => { const m = String(s || '').match(XAT); if (!m) return ''; let [h, mi] = (m[1] || m[3]).split(':').map(Number); const ap = (m[2] || m[4] || '').toLowerCase(); if (ap === 'pm' && h < 12) h += 12; if (ap === 'am' && h === 12) h = 0; return String(h).padStart(2, '0') + ':' + String(mi).padStart(2, '0'); };
  const xNoAt = s => String(s || '').replace(XAT, ' ').trim();
  const XSIGL = { vp: '🟢🟢 Very positive', p: '🟢 Positive', vn: '🔴🔴 Very negative', n: '🔴 Negative', w: '🔵 Watch', m: '🟠 Mixed', '': '' };
  const xSrcs = s => [...String(s || '').matchAll(/\[(@[^\]]+)\]\((https?:\/\/[^)\s]+)\)/g)].map(m => ({ h: m[1].replace(/\\_/g, '_'), u: m[2] }));
  function xTickers(s) {
    const txt = xPlain(s), out = new Set();
    (txt.match(/\b[A-Z][A-Z0-9.]{1,5}\b/g) || []).forEach(t => { if (NAMES.has(nk(t)) || NAMES.has(nk(t + ' US'))) out.add(t); });
    return [...out];
  }
  function xHtml(bs) {
    let h = '', list = [];
    const flush = () => { if (list.length) { h += '<ul>' + list.map(x => `<li style="margin-left:${x.depth * 14}px">${xInline(x.text)}</li>`).join('') + '</ul>'; list = []; } };
    bs.forEach(b => {
      if (b.t === 'li') { list.push(b); return; } flush();
      if (b.t === 'h') h += `<h${Math.min(6, b.lvl + 2)}>${xInline(b.text)}</h${Math.min(6, b.lvl + 2)}>`;
      else if (b.t === 'p') h += `<p>${xInline(b.text)}</p>`;
      else if (b.t === 'table') h += `<div class="tbl-wrap"><table>${b.rows.map((r, k) => `<tr>${r.map(c => k ? `<td>${xInline(c)}</td>` : `<th>${xInline(c)}</th>`).join('')}</tr>`).join('')}</table></div>`;
      else if (b.t === 'callout') h += `<div class="fr-callout">${b.icon ? esc(b.icon) + ' ' : ''}${xHtml(b.kids)}</div>`;
      else if (b.t === 'toggle') h += `<details class="fr-sec"><summary>${xInline(b.title)}</summary>${xHtml(b.kids)}</details>`;
    });
    flush(); return h;
  }
  // structure one run's page into callouts / hot topics / datapoints / scorecards / housekeeping
  function xModel(md) {
    const tree = xParse(md); const M = { callouts: [], topics: [], dps: [], scores: [], notes: [], foot: [] };
    let list = 'Feed', inScore = false;
    tree.forEach(b => {
      if (b.t === 'h') { const t = xPlain(b.text); inScore = /scorecard/i.test(t); if (!inScore) list = t.replace(/^List [A-Z]:\s*/i, ''); return; }
      if (b.t === 'callout') {
        const head = b.kids.find(k => k.t === 'p'), lis = b.kids.filter(k => k.t === 'li');
        if (lis.length) M.callouts.push({ icon: b.icon, title: head ? head.text : '', items: lis.map(x => ({ text: xNoAt(x.text), at: xAt(x.text), key: 'c:' + xPlain(xNoAt(x.text)).slice(0, 80).toLowerCase() })) });
        else M.notes.push({ icon: b.icon, text: b.kids.map(xText).join(' ') });
        return;
      }
      if (b.t === 'toggle') {
        if (inScore) { M.scores.push(b); return; }
        const lis = b.kids.filter(k => k.t === 'li');
        const tp = { title: b.title, list, sig: xSig(b.title), n: lis.length, tick: new Set(), srcs: new Set() };
        const tTks = xTickers(b.title); tTks.forEach(t => tp.tick.add(t)); const mine = [];
        lis.forEach(x => { const s = xSig(x.text) || tp.sig; const src = xSrcs(x.text); src.forEach(z => tp.srcs.add(z.h));
          if (/^\s*(?:<b>)?Sources?:/i.test(x.text) || !xPlain(x.text.replace(/\[@[^\]]+\]\([^)]+\)/g, '')).replace(/[\s,.;:()]/g, '')) { mine.filter(d => !d.src.length).forEach(d => d.src = src); tp.n--; return; }
          const tks = [...new Set(xTickers(x.text).concat(tTks))]; tks.forEach(t => tp.tick.add(t));
          mine.push(M.dps[M.dps.push({ topic: xPlain(b.title).replace(/[🟢🔴🔵🟠🟡]/gu, '').trim(), list, sig: s, text: xNoAt(x.text), at: xAt(x.text), src, tks, key: xPlain(xNoAt(x.text)).slice(0, 80).toLowerCase() }) - 1]); });
        M.topics.push(tp); return;
      }
      if (b.t === 'p') M.foot.push(b.text);
    });
    return M;
  }
  async function xLoadList(fresh) {
    const r = await xCall('notion-search', { query: 'X List Monitor', page_size: 25, max_highlight_length: 0 }, fresh);
    const res = arr((r && r.results) || (typeof r === 'string' ? [] : []));
    const pages = res.filter(p => /X List Monitor/i.test(p.title || '') && (p.type || 'page') === 'page')
      .map(p => ({ id: xId(p.url || p.id), url: p.url, title: p.title, ts: p.timestamp || '', d: ((p.title || '').match(/\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2})?/) || [''])[0] }))
      .sort((a, b) => (b.d + b.ts).localeCompare(a.d + a.ts));
    const seen = new Set(); return pages.filter(p => !seen.has(p.id) && seen.add(p.id));
  }
  async function xLoadPage(p, fresh) {
    if (!fresh && XT.cache.has(p.id)) return XT.cache.get(p.id);
    const r = await xCall('notion-fetch', { id: p.id }, fresh);
    let txt = typeof r === 'string' ? r : (r && (r.text || r.content || r.markdown)) || JSON.stringify(r || '');
    const m = txt.match(/<content>([\s\S]*?)<\/content>/); if (m) txt = m[1];
    const edited = (r && r.page_last_edited_at) || ((typeof r === 'string' ? r : '').match(/as of ([0-9T:.\-Z]+)/) || [])[1] || p.ts;
    const out = { md: txt, edited, model: xModel(txt) }; XT.cache.set(p.id, out); return out;
  }
  // first-seen record per X page (db "xseen", one doc per Notion page): key -> when it first showed up here
  async function xSeen(pg, data) {
    let db = null; try { db = window.claude && window.claude.use ? await window.claude.use('db') : null; } catch (e) {}
    const keys = data.model.dps.map(d => d.key).concat(...data.model.callouts.map(c => c.items.map(i => i.key)));
    let first = {}; const ref = db ? db.collection('xseen').doc(pg.id) : null;
    try { if (ref) { const sn = await ref.get(); if (sn.exists) first = JSON.parse(JSON.stringify(sn.data().first || {})); } } catch (e) {}
    if (!first.__init) Object.assign(first, { __init: data.edited || new Date().toISOString() });
    const t = data.edited || new Date().toISOString(); let changed = false;
    keys.forEach(k => { if (!first[k]) { first[k] = t; changed = true; } });
    XT.seen.set(pg.id, { first });
    if (ref && changed) { try { await ref.set({ first, page: pg.title || '', updated: new Date().toISOString() }); } catch (e) {} }
  }
  function renderX(fresh) {
    const host = document.getElementById('v-x'); if (!host) return;
    const st = XT.st || (XT.st = { list: '', sig: '', q: '', newOnly: false });
    const top = head('𝕏 Feed', 'Twitter / X', 'Only what your X List Monitor agent pulls from your curated X lists, read live from its Notion pages each time you open this tab. Refreshes as the agent runs (up to four times a day).');
    const paint = () => {
      const pg = XT.sel, data = pg && XT.cache.get(pg.id), prev = XT.pages && XT.pages[XT.pages.indexOf(pg) + 1], pdata = prev && XT.cache.get(prev.id);
      let h = top + twDigest() + `<section class="panel"><div class="ctl">` +
        `<label for="x-run">Run <select id="x-run">${arr(XT.pages).slice(0, 20).map(p => `<option value="${esc(p.id)}"${pg && p.id === pg.id ? ' selected' : ''}>${esc((p.title || '').replace(/^📡\s*/, ''))}</option>`).join('')}</select></label>` +
        `<button type="button" id="x-ref" class="btn">↻ Refresh</button>` +
        (pg ? `<a href="${esc(pg.url)}" target="_blank" rel="noopener" class="sub">Open in Notion →</a>` : '') +
        `<span class="count">${XT.busy ? 'Loading…' : data ? 'Page last edited ' + esc(new Date(data.edited).toLocaleString()) : ''}</span></div>` +
        (XT.err ? `<p class="sub c-neg">${esc(XT.err)}</p>` : '') + `</section>`;
      if (!data) { host.innerHTML = h + (XT.busy || !XT.err ? `<section class="panel"><p class="sub">Loading the latest X run from Notion…</p></section>` : ''); wire(); return; }
      const M = data.model, prevKeys = new Set(pdata ? pdata.model.dps.map(d => d.key) : []), seen = (XT.seen.get(pg.id) || {}).first || {};
      const pageDay = (String(pg.d || '').slice(0, 10)) || String(data.edited || '').slice(0, 10);
      // when each item got in: the agent's own run time if it wrote one, else when this page first showed it here
      const addedOf = it => it.at ? { iso: pageDay ? new Date(pageDay + 'T' + it.at + ':00-05:00').toISOString() : '', src: 'agent' } : seen[it.key] ? { iso: seen[it.key], src: 'seen' } : { iso: data.edited || '', src: 'page' };
      const items = M.dps.concat(...M.callouts.map(c => c.items));
      items.forEach(it => { const a = addedOf(it); it.added = a.iso; it.addedSrc = a.src; });
      const times = [...new Set(items.map(it => it.added).filter(Boolean))].sort();
      const latest = times[times.length - 1] || '';
      items.forEach(it => it.isNew = times.length > 1 ? it.added === latest : (pdata ? !prevKeys.has(it.key) : false));
      M.callouts.forEach(c => c.items.forEach(it => { if (times.length <= 1) it.isNew = false; }));
      const nNew = M.dps.filter(d => d.isNew).length;
      const tFmt = iso => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); };
      const dFmt = iso => { const d = new Date(iso); if (isNaN(d)) return ''; const today = new Date().toDateString() === d.toDateString(); return (today ? '' : d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ') + tFmt(iso); };
      M.dps.forEach((d, i) => d.ord = i);
      // 0) what's new strip
      const byT = times.map(t => ({ t, n: M.dps.filter(d => d.added === t).length })).filter(x => x.n);
      h += `<section class="panel x-new"><span class="eyebrow">🆕 What's new</span>` +
        (times.length > 1 ? `<h2>${nNew} new datapoint${nNew === 1 ? '' : 's'} in the ${esc(tFmt(latest))} update</h2>` : pdata ? `<h2>${nNew} datapoint${nNew === 1 ? '' : 's'} not in the previous run</h2>` : `<h2>First update of this page</h2>`) +
        `<div class="x-upd">Updates on this page: ${byT.map(x => `<button type="button" class="x-ut${st.at === x.t ? ' on' : ''}" data-at="${esc(x.t)}">${esc(dFmt(x.t))} <span class="sub">${x.n}</span></button>`).join('')}</div>` +
        `<p class="sub">Each datapoint shows when it got in: the run time the agent stamped on it, or else the first time this page saw it after a refresh. New items are highlighted and listed first.</p></section>`;
      // 1) callouts
      h += M.callouts.map(c => `<section class="panel x-call"><span class="eyebrow">${esc(c.icon || '📣')} Callouts</span><h2>${xInline(xPlain(c.title) || 'Top ideas')}</h2><ul class="x-cl">${c.items.map(t => `<li class="x-s-${xSig(t.text)}${t.isNew ? ' x-isnew' : ''}">${t.isNew ? '<span class="chip x-nchip">New</span> ' : ''}${xInline(t.text)} <span class="sub x-at">${esc(dFmt(t.added))}</span></li>`).join('')}</ul></section>`).join('');
      // 2) hot topics
      const hot = M.topics.slice().sort((a, b) => (/vp|vn/.test(b.sig) - /vp|vn/.test(a.sig)) || (b.n - a.n));
      h += `<section class="panel"><span class="eyebrow">🔥 Hot topics of the day</span><div class="x-hot">${hot.map(t => `<button type="button" class="x-topic x-s-${t.sig}" data-topic="${esc(xPlain(t.title).replace(/[🟢🔴🔵🟠🟡]/gu, '').trim())}"><b>${xInline(xPlain(t.title))}</b><span class="sub">${t.n} datapoints${(() => { const k = M.dps.filter(d => d.isNew && d.topic === xPlain(t.title).replace(/[🟢🔴🔵🟠🟡]/gu, '').trim()).length; return k ? ` · <b class="x-ncount">${k} new</b>` : ''; })()} · ${t.srcs.size} handles · ${esc(t.list)}</span>${t.tick.size ? `<span class="x-tks">${[...t.tick].slice(0, 8).map(x => tk(x)).join(' ')}</span>` : ''}</button>`).join('') || none('No topics in this run.')}</div></section>`;
      // 3) tickers in the feed (recommended)
      const tc = new Map(); M.dps.forEach(d => d.tks.forEach(t => { const o = tc.get(t) || { t, n: 0, p: 0, ng: 0 }; o.n++; if (/p/.test(d.sig) && !/n/.test(d.sig)) o.p++; if (/n/.test(d.sig)) o.ng++; tc.set(t, o); }));
      const tl = [...tc.values()].sort((a, b) => b.n - a.n);
      if (tl.length) h += `<section class="panel"><span class="eyebrow">🏷️ Tickers in the feed</span><p class="sub">Covered names mentioned in this run. Click one to filter the datapoints; 🟢/🔴 count the tone of its datapoints.</p><div class="x-tklist">${tl.map(o => `<button type="button" class="x-tkb" data-tk="${esc(o.t)}">${tk(o.t)} <span class="sub">${o.n}${o.p ? ' · 🟢' + o.p : ''}${o.ng ? ' · 🔴' + o.ng : ''}</span></button>`).join('')}</div></section>`;
      // 4) datapoints
      const lists = [...new Set(M.dps.map(d => d.list))];
      let rows = M.dps.filter(d => (!st.list || d.list === st.list) && (!st.sig || (st.sig === 'pos' ? /p/.test(d.sig) && !/n/.test(d.sig) : st.sig === 'neg' ? /n/.test(d.sig) : d.sig === 'w')) && (!st.newOnly || d.isNew) && (!st.at || d.added === st.at) && (!st.topic || d.topic === st.topic) && (!st.tk || d.tks.includes(st.tk)) && (!st.q || xPlain(d.text + ' ' + d.topic).toLowerCase().includes(st.q.toLowerCase())));
      h += `<section class="panel"><span class="eyebrow">📌 Datapoints</span><div class="ctl">` +
        `<label for="x-q">Search <input type="search" id="x-q" value="${esc(st.q)}" placeholder="Ticker or word"></label>` +
        `<label for="x-l">List <select id="x-l"><option value="">All</option>${lists.map(l => `<option${st.list === l ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select></label>` +
        `<label for="x-s">Tone <select id="x-s"><option value="">All</option><option value="pos"${st.sig === 'pos' ? ' selected' : ''}>🟢 Positive</option><option value="neg"${st.sig === 'neg' ? ' selected' : ''}>🔴 Negative</option><option value="w"${st.sig === 'w' ? ' selected' : ''}>🔵 Watch</option></select></label>` +
        ((times.length > 1 || pdata) ? `<label><input type="checkbox" id="x-new"${st.newOnly ? ' checked' : ''}> New in the latest update only</label>` : '') +
        (st.at ? `<button type="button" class="btn" id="x-atclr">Update ${esc(dFmt(st.at))} ✕</button>` : '') +
        (st.topic || st.tk ? `<button type="button" class="btn" id="x-clr">Clear ${esc(st.topic || st.tk)} ✕</button>` : '') +
        `<span class="count">${rows.length} of ${M.dps.length}</span></div>` +
        `<div class="tbl-wrap"><table class="x-dp"><thead><tr><th>Topic</th><th>Added</th><th>Tone</th><th>Datapoint</th><th>Source</th></tr></thead><tbody>${rows.slice().sort((a, b) => (b.isNew - a.isNew) || String(b.added).localeCompare(String(a.added)) || (a.ord - b.ord)).map(d => `<tr class="${d.isNew ? 'x-isnew' : ''}"><td>${esc(d.topic)}<div class="sub">${esc(d.list)}</div></td><td class="x-at" style="white-space:nowrap" title="${d.addedSrc === 'agent' ? 'Run time stamped by the agent' : d.addedSrc === 'seen' ? 'First seen on this page' : 'Page edit time (no earlier record)'}">${esc(dFmt(d.added))}${d.isNew ? '<br><span class="chip x-nchip">New</span>' : ''}</td><td class="x-s-${d.sig}" style="white-space:nowrap">${esc((XSIGL[d.sig] || '').split(' ')[0])}</td><td class="ev-wrap">${xInline(d.text.replace(/\s*(?:Sources?:\s*)?\(?\[@[^\]]+\]\([^)]+\)\)?[,.\s]*/g, ' ').replace(/[🟢🔴🔵🟠🟡]/gu, '').trim())}</td><td class="ev-src">${d.src.map(z => `<a href="${esc(z.u)}" target="_blank" rel="noopener">${esc(z.h)}</a>`).join('<br>')}</td></tr>`).join('') || `<tr><td colspan="5">${none('No datapoints match.')}</td></tr>`}</tbody></table></div></section>`;
      // 5) handle scorecards + housekeeping (recommended)
      if (M.scores.length) h += `<section class="panel"><span class="eyebrow">📊 Handle scorecards</span><p class="sub">Which accounts produce usable datapoints. Use it to prune or add to your lists.</p>${M.scores.map(b => `<details class="fr-sec"><summary>${xInline(b.title)}</summary>${xHtml(b.kids)}</details>`).join('')}</section>`;
      if (M.notes.length || M.foot.length) h += `<section class="panel"><span class="eyebrow">🧹 What the agent read and cut</span>${M.notes.map(n => `<p class="sub">${esc(n.icon)} ${xInline(n.text)}</p>`).join('')}${M.foot.map(t => `<p class="sub">${xInline(t)}</p>`).join('')}</section>`;
      h += `<section class="panel"><details class="fr"><summary>Full page as written</summary><div class="fr-html">${xHtml(xParse(data.md))}</div></details></section>`;
      host.innerHTML = h; wire(); dedupeNames(host); paintUpd('x');
    };
    function wire() {
      const $ = id => document.getElementById(id);
      $('x-ref') && $('x-ref').addEventListener('click', () => { XT.cache.clear(); go(true); });
      $('x-run') && $('x-run').addEventListener('change', e => { XT.sel = XT.pages.find(p => p.id === e.target.value); loadSel(false); });
      $('x-q') && $('x-q').addEventListener('input', e => { st.q = e.target.value; const p = e.target.selectionStart; paint(); const n = $('x-q'); n.focus(); n.setSelectionRange(p, p); });
      $('x-l') && $('x-l').addEventListener('change', e => { st.list = e.target.value; paint(); });
      $('x-s') && $('x-s').addEventListener('change', e => { st.sig = e.target.value; paint(); });
      $('x-new') && $('x-new').addEventListener('change', e => { st.newOnly = e.target.checked; paint(); });
      $('x-atclr') && $('x-atclr').addEventListener('click', () => { st.at = ''; paint(); });
      host.querySelectorAll('.x-ut').forEach(b => b.addEventListener('click', () => { st.at = st.at === b.dataset.at ? '' : b.dataset.at; paint(); document.querySelector('.x-dp') && document.querySelector('.x-dp').scrollIntoView({ block: 'start' }); }));
      $('x-clr') && $('x-clr').addEventListener('click', () => { st.topic = ''; st.tk = ''; paint(); });
      host.querySelectorAll('.x-topic').forEach(b => b.addEventListener('click', () => { st.topic = st.topic === b.dataset.topic ? '' : b.dataset.topic; st.tk = ''; paint(); document.querySelector('.x-dp') && document.querySelector('.x-dp').scrollIntoView({ block: 'start' }); }));
      host.querySelectorAll('.x-tkb').forEach(b => b.addEventListener('click', () => { st.tk = st.tk === b.dataset.tk ? '' : b.dataset.tk; st.topic = ''; paint(); }));
    }
    function loadSel(fresh) {
      const pg = XT.sel; if (!pg) { XT.busy = false; paint(); return; }
      XT.busy = true; paint();
      const prev = XT.pages[XT.pages.indexOf(pg) + 1];
      Promise.all([xLoadPage(pg, fresh), prev ? xLoadPage(prev, false).catch(() => null) : null])
        .then(([data]) => xSeen(pg, data)).then(() => { XT.busy = false; XT.err = ''; paint(); })
        .catch(e => { XT.busy = false; XT.err = 'Could not read the page from Notion: ' + (e && (e.message || e.code) || e); paint(); });
    }
    function go(fresh) {
      XT.busy = true; paint();
      xLoadList(fresh).then(ps => { XT.pages = ps; if (!ps.length) { XT.busy = false; XT.err = 'No "X List Monitor" pages found in Notion yet.'; paint(); return; }
        XT.sel = fresh || !XT.sel ? ps[0] : (ps.find(p => p.id === XT.sel.id) || ps[0]); loadSel(fresh); })
        .catch(e => { XT.busy = false; XT.err = e && e.code === 'not_granted' ? 'Allow this page to use your Notion connector (artifact Permissions menu) to see the X feed.' : 'Could not search Notion: ' + (e && (e.message || e.code) || e); paint(); });
    }
    if (XT.pages && !fresh) { paint(); return; }
    const ready = XT.mcp ? Promise.resolve(XT.mcp) : (window.claude && typeof window.claude.use === 'function' ? window.claude.use('mcp').catch(() => null) : Promise.resolve(null));
    paint();
    ready.then(m => { XT.mcp = m; if (!m) { XT.err = 'The live X feed needs this page open on claude.ai with your Notion connector.'; paint(); return; } go(!!fresh); });
  }


  // ---- "Updated" line at the top of every tab: when its data was last refreshed, and when the page was rebuilt ----
  const updMax = xs => xs.filter(Boolean).map(String).sort().pop() || '';
  const runMax = rs => updMax(arr(rs).map(r => r && r.date));
  const updFmt = t => { if (!t) return ''; const s = String(t); const d = new Date(/T|\d:\d/.test(s) ? s.replace(' ', 'T') : s + 'T12:00:00');
    if (isNaN(d)) return esc(s); return /T|\d:\d/.test(s) ? d.toLocaleString([], { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }); };
  const UPD = {
    today: () => ({ t: (D.today || {}).as_of, src: 'latest digest pages' }),
    x: () => ({ live: 'Live: read from the X List Monitor pages in Notion when you open the tab (the agent runs up to four times a day)', t: XT.sel && XT.cache.get(XT.sel.id) ? XT.cache.get(XT.sel.id).edited : '', src: 'latest X run' }),
    daily: () => ({ t: (DLY || D.daily || {}).as_of, src: 'market close' }),
    routines: () => ({ t: (D.routines || {}).as_of, src: 'routine runs' }),
    stocks: () => ({ t: updMax([runMax((D.ideas || {}).runs), (D.dp_index || {}).as_of]), src: 'thesis pages and datapoints', live: 'Quarterly review numbers are live from Visible Alpha' }),
    earnings: () => ({ t: updMax(arr(D.bobby).concat(arr(D.rebecca)).map(r => r.report_date)), src: 'latest print reviewed' }),
    datapoints: () => ({ t: (D.dp_index || {}).as_of, src: 'Supabase research_evidence' }),
    screens: () => ({ t: updMax([runMax((D.screens || {}).runs), (D.comps || {}).as_of]), src: 'revisions and comps' }),
    ideas: () => ({ t: updMax([(D.ideas || {}).generated, (D.pipeline || {}).as_of, runMax((D.ideas || {}).runs)]), src: 'ideas, pipeline and theses' }),
    prep: () => ({ t: runMax((D.prep || {}).runs), src: 'latest prep page' }),
    health: () => ({ t: D.built_at, src: 'skill outputs' }),
    sources: () => ({ t: (D.sources || {}).built, src: 'Tech Coverage Monitor' }),
    thesis: () => ({ t: (TH.doc || {}).updated_at, src: 'SRS AI Update, Oct 2026, plus flagged datapoints', live: 'Live: the thesis and flags read from this page’s database' }),
    ai: () => ({ t: (D.dp_index || {}).as_of, src: 'datapoints' + (AI_DC.asof ? '; state GW as of ' + AI_DC.asof : ''), live: 'ALAB quarterly numbers are live from Visible Alpha' }),
    mgmt: () => ({ t: updMax([((D.mgmt || {}).questions || {}).as_of, ((D.mgmt || {}).insiders || {}).as_of]), src: 'Canary super analysts, Insider Score' }),
    dcrisk: () => ({ t: (DCR.doc || {}).as_of, src: 'snapshot of the research doc; the doc itself may have later edits' }),
    notes: () => ({ live: 'Live: notes save to this page’s database as you write them' }),
    method: () => ({})
  };
  function paintUpd(v) {
    const el = document.getElementById('v-' + v) || document.querySelector(`.view[data-view="${v}"]`); if (!el) return;
    let bar = el.querySelector(':scope > .upd'); if (!bar) { bar = document.createElement('div'); bar.className = 'upd'; el.prepend(bar); }
    let u = {}; try { u = (UPD[v] || (() => ({})))() || {}; } catch (e) {}
    const parts = [];
    if (u.t) parts.push(`<b>Updated ${updFmt(u.t)}</b>${u.src ? ` <span>(${esc(u.src)})</span>` : ''}`);
    if (u.live) parts.push(`<span class="upd-live">● ${esc(u.live)}</span>`);
    if (D.built_at) parts.push(`<span>Page rebuilt ${updFmt(D.built_at)}</span>`);
    bar.innerHTML = parts.join('<span class="upd-sep">·</span>');
  }
  window.__paintUpd = paintUpd;
  // tabs that redraw themselves (Stocks, Notes, X) would drop the line; put it back when that happens
  document.querySelectorAll('.view').forEach(el => new MutationObserver(() => { if (!el.querySelector(':scope > .upd')) paintUpd(el.dataset.view); }).observe(el, { childList: true }));

  // ================= AI: data center politics x GW, ALAB revenue, compute supply/demand =================
  // State GW by stage and political tier: kept in this page's database (collection "ai", doc "dc_states": {source, asof, img, note, rows:[[state, tier, active, construction, announced]]}), not in the code
  const AI_DC = { source: '', asof: '', img: '', note: '', rows: [] };
  const AI_TIER = { 1: 'Tier 1 · welcoming', 2: 'Tier 2', 3: 'Tier 3', 4: 'Tier 4', 5: 'Tier 5 · full moratorium' };
  const AI_RE = {
    policy: /moratori|ballot|zoning|governor|legislat|permit|data ?cent(er|re)s? (ban|pause|opposition|tax|subsid|bill|backlash)|local opposition|ratepayer|interconnect(ion)? queue|puc\b|public utilit|community opposition|abbott|hinojosa/i,
    alabRev: /revenue|sales|\$\s?[0-9.]+\s?(m|b|bn|mm)\b|guid|content|attach|ramp|units|scorpio|aries|taurus|leo|trainium|backlog|run-?rate|share|design win|customer|asic|switch/i,
    compute: /compute (shortage|constrain|capacity|demand|supply)|gpu (shortage|supply|demand|constrain|allocation)|supply[- ]constrain|sold out|capacity constrain|cannot meet demand|can't meet demand|demand (exceeds|outstrip|ahead of supply)|ahead of supply|shortage|cowos|lead times? (extend|stretch|out|\d)|tokens?\b.*(demand|growth|processed|per)|inference demand|compute demand|undersuppl|oversuppl|overbuil|digestion|allocation|push[- ]?outs?|fulfil?ment/i,
    tight: /shortage|constrain|sold out|tight|cannot meet|can't meet|exceed|outstrip|ahead of supply|allocation|lead times?|undersuppl|backlog|fulfil?ment (still|only|\d)/i,
    loose: /oversuppl|overbuil|digestion|glut|push[- ]?outs?|slip|cancel|excess inventor|soften|slowdown|pause/i
  };
  const AI_BUCKETS = [['GPUs & accelerators', /gpu|accelerat|asic|tpu|trainium|blackwell|rubin|mi[345]\d\d|xpu|nvidia|nvda|amd\b/i], ['Memory & HBM', /hbm|dram|nand|memory|ssd|hdd/i], ['Packaging & foundry', /cowos|packag|foundry|wafer|n[235]\b|2nm|3nm|substrate|tsmc/i],
    ['Power & data center build', /power|gw\b|gigawatt|data ?cent|grid|turbine|transformer|electric|site/i], ['Networking & optics', /optic|switch|network|ethernet|nvlink|scale[- ]up|scale[- ]out|transceiver|cpo/i], ['Tokens & inference demand', /token|inference|usage|api|agent|workload|capex/i]];
  const AI = { st: { dcSort: 'ann', tier: '', bucket: '', tone: '', q: '', days: 180, alabQ: '', gpuBasis: 'all', gpuFam: '' }, rows: null, err: '' };
  // ---- AI › GPU rental prices: $/GPU-hour points parsed from your datapoints (refreshes with every rebuild) ----
  const GPU_FAM = g => /a100/i.test(g) ? 'A100' : /h100/i.test(g) ? 'H100' : /h200/i.test(g) ? 'H200' : /b200/i.test(g) ? 'B200/GB200' : /b300/i.test(g) ? 'B300/GB300' : 'Rubin';
  const GPU_COL = { A100: '#9aa3b2', H100: '#2f6fd6', H200: '#16a3a3', 'B200/GB200': '#d9822b', 'B300/GB300': '#c7414b', Rubin: '#7b4fc9' };
  const gpuBasis = s => /forecast|tco|model|expect/i.test(s) ? 'forecast' : /spot|preempt/i.test(s) ? 'spot' : /on-?demand|list|median/i.test(s) ? 'on-demand' : /contract|year|yr|reserv|term|deal|lease|agreement|renew|sign/i.test(s) ? 'contract' : 'quoted';
  const GPU_NAME = /\b(H100|H200|A100|B200|B300|GB200|GB300|VR NVL72|Vera Rubin|Rubin)\b/gi;
  const GPU_PRICE = /\$\s?(\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*\$?(\d+(?:\.\d+)?))?\s*(?:\/|per)\s*(?:GPU[-\s/]*)?(?:hr|hour|h)\b/gi;
  function gpuPoints(rows) {
    const out = [], seen = new Set();
    rows.forEach(r => {
      const t = String(r[9] || ''); if (!/\$\s?\d/.test(t) || !/(hr|hour)/i.test(t)) return;
      const names = [...t.matchAll(GPU_NAME)].map(m => ({ i: m.index, e: m.index + m[0].length, g: m[1] }));
      if (!names.length) return;
      [...t.matchAll(GPU_PRICE)].forEach(m => {
        const pre = t.slice(Math.max(0, m.index - 22), m.index), fromTo = /from\s*(about|~|roughly|around)?\s*~?\s*$/i.test(pre) && m[2] && /to/i.test(m[0]);
        let lo = +m[1], hi = m[2] ? +m[2] : null; if (fromTo) { lo = hi; hi = null; } const v = hi ? (lo + hi) / 2 : lo; if (!(v > 0.2 && v < 40)) return;
        const ps = m.index, pe = ps + m[0].length;
        // the GPU this price belongs to: a name right after the price ("$2.70/GPU-hour H100"), else the nearest name before it with no other price in between
        if (!fromTo && /(from|vs\.?|versus|earlier|was|in 20\d\d)\s*(about|~|roughly|around)?\s*~?\s*$/i.test(t.slice(Math.max(0, ps - 22), ps)) || /^\s*(in|during)\s+20\d\d/i.test(t.slice(pe, pe + 10))) return; // an earlier/comparison price, not today's
        let nm = names.find(n => n.i >= pe && /^\s{1,2}$/.test(t.slice(pe, n.i)));
        if (!nm) { const before = names.filter(n => n.e <= ps && ps - n.e <= 70 && !/\$\s?\d/.test(t.slice(n.e, ps))); nm = before[before.length - 1]; }
        if (!nm) return;
        const ctx = t.slice(Math.max(0, Math.min(nm.i, ps) - 16), Math.min(nm.i, ps)) + ' ' + (nm.i < ps ? t.slice(nm.e, ps) : t.slice(pe, nm.e)) + ' ' + t.slice(Math.max(pe, nm.e), Math.max(pe, nm.e) + 12).split(/[,;]|\$|\band\b/)[0];
        const after = t.slice(pe, pe + 14).split(/[,;]|\$|\band\b/)[0], gap = nm.i < ps ? t.slice(nm.e, ps) : t.slice(pe, nm.e), bef = t.slice(Math.max(0, Math.min(nm.i, ps) - 16), Math.min(nm.i, ps));
        const b0 = [after, gap, bef].map(gpuBasis).find(b => b !== 'quoted') || 'quoted', fam = GPU_FAM(nm.g), basis = /\b(forecast|TCO)\b/i.test(t) && b0 !== 'spot' && b0 !== 'on-demand' ? 'forecast' : b0;
        const k = r[2] + fam + v.toFixed(2); if (seen.has(k)) return; seen.add(k);
        out.push({ d: r[2], fam, v, lo, hi, basis, t, r });
      });
    });
    return out.sort((a, b) => a.d.localeCompare(b.d));
  }
  const gpuFilter = (pts, st) => pts.filter(p => (st.gpuBasis === 'all' ? p.basis !== 'forecast' : p.basis === st.gpuBasis) && (!st.gpuFam || p.fam === st.gpuFam));
  function gpuChartHtml(show) {
    if (!show.length) return none('No GPU rental prices match.');
    const W = 860, H = 300, L = 44, R = 12, T = 12, B = 30;
    const ds = show.map(p => +new Date(p.d)), x0 = Math.min(...ds), x1 = Math.max(...ds), ymax = Math.ceil(Math.max(...show.map(p => p.v)) + 0.5);
    const X = d => L + (W - L - R) * ((+new Date(d) - x0) / Math.max(1, x1 - x0)), Y = v => T + (H - T - B) * (1 - v / ymax);
    const fams = [...new Set(show.map(p => p.fam))];
    let g = '';
    const step = ymax > 12 ? 4 : 2;
    for (let v = 0; v <= ymax; v += step) g += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--rule)"/><text x="${L - 6}" y="${Y(v) + 3}" text-anchor="end">$${v}</text>`;
    const d0 = new Date(x0); for (let d = new Date(d0.getFullYear(), d0.getMonth() + 1, 1); +d <= x1; d = new Date(d.getFullYear(), d.getMonth() + 1, 1)) g += `<text x="${X(d.toISOString().slice(0, 10))}" y="${H - 8}" text-anchor="middle">${d.toLocaleDateString('en-US', { month: 'short' })}</text>`;
    fams.forEach(f => ['contract', 'on-demand', 'spot'].forEach(bs => { const ps = show.filter(p => p.fam === f && p.basis === bs); if (ps.length > 1) g += `<polyline fill="none" stroke="${GPU_COL[f]}" stroke-width="1.5" stroke-opacity=".55"${bs === 'contract' ? '' : ' stroke-dasharray="4 3"'} points="${ps.map(p => X(p.d) + ',' + Y(p.v)).join(' ')}"/>`; }));
    show.forEach(p => {
      const x = X(p.d), y = Y(p.v), tip = `<title>${esc(p.d)} · ${esc(p.fam)} · $${p.v.toFixed(2)}/hr (${esc(p.basis)})${p.hi ? ` range $${p.lo}–$${p.hi}` : ''} — ${esc(p.t.slice(0, 200))}</title>`, a = `fill="${GPU_COL[p.fam]}" stroke="var(--surface)" stroke-width="1"`;
      g += p.basis === 'spot' ? `<rect x="${x - 4}" y="${y - 4}" width="8" height="8" ${a}>${tip}</rect>` : p.basis === 'on-demand' ? `<path d="M${x},${y - 5}L${x + 5},${y + 4}L${x - 5},${y + 4}Z" ${a}>${tip}</path>` : `<circle cx="${x}" cy="${y}" r="4.5" ${a}>${tip}</circle>`;
    });
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="GPU rental prices in dollars per GPU-hour by date">${g}</svg>` +
      `<div class="legend">${fams.map(f => `<span><i style="background:${GPU_COL[f]}"></i>${esc(f)}</span>`).join('')}<span>● contract (solid line) / quoted</span><span>▲ on-demand (dashed)</span><span>■ spot (dashed)</span></div>`;
  }
  function gpuSectionHtml(pts, st) {
    const fams = [...new Set(pts.map(p => p.fam))], show = gpuFilter(pts, st);
    const latest = fams.map(f => { const ps = pts.filter(p => p.fam === f && p.basis !== 'forecast'); return ps.length ? ps[ps.length - 1] : null; }).filter(Boolean);
    const opts = [['all', 'All (excl. forecasts)'], ['contract', 'Contract'], ['on-demand', 'On-demand'], ['spot', 'Spot'], ['quoted', 'Quoted, type unclear'], ['forecast', 'Forecasts / TCO']];
    return `<div class="summary">${latest.map(p => `<div class="stat"><span class="v" style="color:${GPU_COL[p.fam]}">$${p.v.toFixed(2)}</span><span class="l">Latest ${esc(p.fam)} · ${esc(p.basis)} · ${esc(fmtD(p.d))}</span></div>`).join('')}</div>` +
      `<div class="ctl"><label for="gpu-b">Price type <select id="gpu-b">${opts.map(([v, l]) => `<option value="${v}"${st.gpuBasis === v ? ' selected' : ''}>${l}</option>`).join('')}</select></label>` +
      `<label for="gpu-f">GPU <select id="gpu-f"><option value="">All</option>${fams.map(f => `<option${st.gpuFam === f ? ' selected' : ''}>${esc(f)}</option>`).join('')}</select></label><span class="count">${show.length} prices</span></div>` +
      gpuChartHtml(show) +
      `<p class="sub">Every $/GPU-hour price quoted in your Supabase datapoints, placed on the datapoint's date. Price types and providers differ (spot, on-demand list, 1–6 year contracts), so compare like with like using the filter; ranges are plotted at their midpoint. Hover a point for its source. Canary's own GPU Rentals Tracker isn't available through its tools; its latest figures (week of Oct 26: neocloud on-demand index $8.10, H100 $4.01, GB300 $12.55) appear only in Canary's super-analyst notes.</p>` +
      `<details class="fr"><summary>All ${show.length} prices with sources</summary><div class="tbl-wrap"><table class="dt"><thead><tr><th>Date</th><th>GPU</th><th class="n">$/hr</th><th>Type</th><th>Datapoint</th><th>Source</th></tr></thead><tbody>${show.slice().reverse().map(p => `<tr><td class="nowrap">${esc(p.d)}</td><td style="color:${GPU_COL[p.fam]}"><b>${esc(p.fam)}</b></td><td class="n">${p.hi ? `${p.lo}–${p.hi}` : p.v.toFixed(2)}</td><td>${esc(p.basis)}</td><td class="ev-wrap">${esc(p.t)}</td><td class="ev-src">${esc((AI.SRC || [])[p.r[7]] || '')}</td></tr>`).join('')}</tbody></table></div></details>`;
  }
  // ================= AI › SRS models: the team's AI industry models (AI Master Model, AI Economics Master, AI Financings) =================
  // The numbers live in this page's database, collection "ai_models" (docs meta, capex, revisions, compute, econ, labs, fin, supply),
  // written by store/build_ai_models.py from the workbooks. Rebuilds never touch them; a new model version is loaded by re-running that script.
  const AIM = { docs: null, err: '', loaded: false, view: 'capex', cmp: 'gw', cmpMode: 'share', revCo: 'Total', cfg: {}, tips: {}, ro: null, w: 0 };
  try { const v0 = localStorage.getItem('td-aim-view'); if (v0) AIM.view = v0; } catch (e) {}
  const AIM_VIEWS = [['capex', 'Capex & capacity'], ['revisions', 'Street capex revisions'], ['compute', 'Accelerator share'], ['econ', 'AI economics'], ['labs', 'OpenAI & Anthropic'], ['fin', 'Financing'], ['supply', 'Semis supply chain']];
  const AIM_C = [1, 2, 3, 4, 5, 6].map(i => `var(--mv${i})`);
  const aimDoc = k => (AIM.docs || {})[k] || {};
  const aimT = (k, id) => arr(aimDoc(k).tables).find(t => t.id === id) || null;
  const aimR = (t, re) => t ? arr(t.rows).find(r => re.test(r.l)) || null : null;
  const aimN = v => typeof v === 'number' && isFinite(v) ? v : null;
  const aimEst = t => !t || t.est_from == null ? -1 : arr(t.cols).findIndex(c => parseInt(c, 10) >= +t.est_from);
  const aimCats = t => { const e = aimEst(t); return arr(t.cols).map((c, i) => e >= 0 && i >= e ? c + 'E' : String(c)); };
  const aimAt = (t, re, year) => { const r = aimR(t, re), i = t ? arr(t.cols).indexOf(String(year)) : -1; return r && i >= 0 ? aimN(r.v[i]) : null; };
  const aimISO = s => { const m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(String(s || '')); return m ? `${m[3]}-${m[1].padStart(2, '0')}-${m[2].padStart(2, '0')}` : String(s == null ? '' : s); };
  function aimF(v, f) {
    if (v == null || v === '') return '';
    if (typeof v !== 'number') return String(v);
    if (!isFinite(v)) return '';
    const a = Math.abs(v), g = (x, d) => x.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
    let s;
    if (f === 'pct') { const p = a * 100; s = g(p, p >= 100 ? 0 : 1) + '%'; }
    else if (f === 'int') s = g(a, 0);
    else if (f === 'num1') s = g(a, 1);
    else if (f === 'num2') s = g(a, 2);
    else if (f === 'usd2') s = '$' + g(a, 2);
    else if (f === 'x') s = g(a, 2) + 'x';
    else s = g(a, a >= 100 ? 0 : a >= 1 ? 1 : 2); // bn, gw, num
    return (v < 0 && /[1-9]/.test(s) ? '−' : '') + s;
  }
  const aimAx = (v, f) => f === 'share' ? v + '%' : f === 'pct' ? +(v * 100).toFixed(1) + '%' : Math.abs(v) >= 1000 ? v.toLocaleString('en-US') : String(+v.toFixed(2));
  function aimTicks(lo, hi, n) {
    if (!(hi > lo)) hi = lo + 1;
    const raw = (hi - lo) / (n || 4), mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
    const step = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * mag, out = [];
    for (let v = Math.floor(lo / step) * step; v <= Math.ceil(hi / step) * step + step / 2; v += step) out.push(+v.toFixed(10));
    return out;
  }
  const aimPath = pts => { let d = '', pen = false; pts.forEach(p => { if (!p) { pen = false; return; } d += (pen ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1); pen = true; }); return d; };
  // a column from its baseline side (y0) to its data end (y1); only the data end is rounded
  function aimBar(x, y0, y1, w, r) {
    const h = Math.abs(y0 - y1); r = Math.min(r, h, w / 2); const s = y1 < y0 ? 1 : -1, f = n => n.toFixed(1);
    return `M${f(x)},${f(y0)}V${f(y1 + s * r)}Q${f(x)},${f(y1)} ${f(x + r)},${f(y1)}H${f(x + w - r)}Q${f(x + w)},${f(y1)} ${f(x + w)},${f(y1 + s * r)}V${f(y0)}Z`;
  }
  // stacked (or single-series) columns, optional 100% share mode and an overlay line on the same axis
  function aimCols(cfg, W) {
    const H = cfg.h || 240, L = 46, R = 10, T = 22, B = 24, S = cfg.series, n = cfg.cats.length;
    const pos = i => S.reduce((a, s) => a + Math.max(0, aimN(s.v[i]) || 0), 0);
    const val = (s, i) => { const v = aimN(s.v[i]) || 0; if (!cfg.share) return v; const t = pos(i); return t ? 100 * Math.max(0, v) / t : 0; };
    let hi = 0, lo = 0;
    for (let i = 0; i < n; i++) {
      if (S.length === 1) { const v = val(S[0], i); hi = Math.max(hi, v); lo = Math.min(lo, v); } else hi = Math.max(hi, cfg.share ? 100 : pos(i));
      if (cfg.line) { const v = aimN(cfg.line.v[i]); if (v != null) { hi = Math.max(hi, v); lo = Math.min(lo, v); } }
    }
    if (lo < 0) lo *= 1.15;
    const tk = cfg.share ? [0, 25, 50, 75, 100] : aimTicks(lo, hi, 4), y0 = tk[0], y1 = tk[tk.length - 1];
    const Y = v => T + (H - T - B) * (1 - (v - y0) / (y1 - y0)), band = (W - L - R) / n, bw = Math.max(6, Math.min(24, band * 0.6)), X = i => L + band * (i + 0.5);
    let g = '';
    if (cfg.est > 0 && cfg.est < n) g += `<rect class="aim-estb" x="${(L + band * cfg.est).toFixed(1)}" y="${T - 20}" width="${(band * (n - cfg.est)).toFixed(1)}" height="${H - B - T + 20}"/><text class="aim-estl" x="${(L + band * cfg.est + 5).toFixed(1)}" y="${T - 9}">Estimates</text>`;
    tk.forEach(v => { const y = Y(v); g += `<line class="aim-grid${v === 0 ? ' z' : ''}" x1="${L}" x2="${W - R}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}"/><text x="${L - 6}" y="${(y + 3.5).toFixed(1)}" text-anchor="end">${esc(aimAx(v, cfg.share ? 'share' : cfg.ax))}</text>`; });
    const every = Math.max(1, Math.ceil(44 / band));
    cfg.cats.forEach((c, i) => { if ((n - 1 - i) % every === 0) g += `<text x="${X(i).toFixed(1)}" y="${H - 7}" text-anchor="middle">${esc(c)}</text>`; });
    const tips = AIM.tips[cfg.name] = [];
    for (let i = 0; i < n; i++) {
      let m = '', up = 0, dn = 0;
      const vs = S.map((s, k) => [k, val(s, i)]), top = (vs.filter(o => o[1] > 0).pop() || [])[0], x = X(i) - bw / 2;
      vs.forEach(([k, v]) => {
        if (!v) return;
        if (v > 0) { const yb = Y(up) - (up > 0 ? 2 : 0), yt = Y(up + v); up += v; if (yb - yt < 0.75) return; m += `<path d="${k === top ? aimBar(x, yb, yt, bw, 4) : `M${x.toFixed(1)},${yb.toFixed(1)}V${yt.toFixed(1)}h${bw.toFixed(1)}V${yb.toFixed(1)}Z`}" style="fill:${S[k].c}"/>`; }
        else { const yb = Y(dn) + (dn < 0 ? 2 : 0), yt = Y(dn + v); dn += v; if (yt - yb < 0.75) return; m += `<path d="${aimBar(x, yb, yt, bw, 4)}" style="fill:${S[k].c}"/>`; }
      });
      const tip = { h: cfg.tipH ? cfg.tipH[i] : cfg.cats[i], rows: [] };
      S.forEach(s => { const v = aimN(s.v[i]); if (v != null) tip.rows.push({ c: s.c, n: s.n, v: cfg.share ? `${Math.round(val(s, i))}% · ${aimF(v, cfg.f)}` : aimF(v, cfg.f) }); });
      if (S.length > 1) { const t = cfg.tot ? aimN(cfg.tot[i]) : pos(i); if (t != null) tip.rows.push({ n: cfg.totName || 'Total', v: aimF(t, cfg.f), b: 1 }); }
      if (cfg.line && aimN(cfg.line.v[i]) != null) tip.rows.push({ c: cfg.line.c || 'var(--ink)', n: cfg.line.n, v: aimF(cfg.line.v[i], cfg.f), b: 1 });
      arr(cfg.extra).forEach(xr => { const v = aimN(xr.v[i]); if (v != null) tip.rows.push({ n: xr.n, v: aimF(v, xr.f || cfg.f) }); });
      tips.push(tip);
      g += `<g class="aim-h" data-tip="${cfg.name}:${i}" tabindex="0" aria-label="${esc(tip.h + ': ' + tip.rows.map(r => r.n + ' ' + r.v).join(', '))}"><rect class="aim-hr" x="${(L + band * i).toFixed(1)}" y="${T - 4}" width="${band.toFixed(1)}" height="${H - B - T + 4}"/>${m}</g>`;
    }
    if (!cfg.share) {
      let labs = arr(cfg.labels).filter((i, k, a) => i >= 0 && i < n && a.indexOf(i) === k);
      if (band < 34 && labs.length > 2) labs = [labs[0], labs[labs.length - 1]];
      labs.forEach(i => {
        const t = S.length > 1 ? (cfg.tot ? aimN(cfg.tot[i]) : pos(i)) : aimN(S[0].v[i]); if (t == null) return;
        const y = S.length === 1 && t < 0 ? Y(t) + 13 : Y(S.length > 1 ? pos(i) : t) - 6;
        g += `<text class="aim-vl" x="${X(i).toFixed(1)}" y="${y.toFixed(1)}" text-anchor="middle">${esc(aimF(t, cfg.f))}</text>`;
      });
    }
    if (cfg.line) { const pts = cfg.line.v.map((v, i) => aimN(v) == null ? null : [X(i), Y(v)]), c = cfg.line.c || 'var(--ink)'; g += `<path class="aim-ln" d="${aimPath(pts)}" style="stroke:${c}"/>` + pts.map(p => p ? `<circle class="aim-dot" cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="4" style="fill:${c}"/>` : '').join(''); }
    return `<svg class="aim-svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="group" aria-label="${esc(cfg.aria || '')}">${g}</svg>`;
  }
  // lines over categories with a snapping crosshair; optional dashed tail (model path) and point marks
  function aimLines(cfg, W) {
    const H = cfg.h || 240, S = cfg.series, n = cfg.cats.length, ends = W >= 520 && cfg.ends !== false;
    const L = 46, R = ends ? (cfg.endW || 100) : 16, T = 14, B = 24;
    let lo = Infinity, hi = -Infinity;
    S.forEach(s => s.v.forEach(v => { if (aimN(v) != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }));
    arr(cfg.marks).forEach(m => { lo = Math.min(lo, m.v); hi = Math.max(hi, m.v); });
    if (!isFinite(lo)) return none('No data to chart.');
    if (cfg.zero !== false) lo = Math.min(0, lo);
    const tk = aimTicks(lo, hi, 4), y0 = tk[0], y1 = tk[tk.length - 1], step = (W - L - R) / Math.max(1, n - 1);
    const Y = v => T + (H - T - B) * (1 - (v - y0) / (y1 - y0)), X = i => L + (n > 1 ? step * i : (W - L - R) / 2);
    let g = '';
    tk.forEach(v => { const y = Y(v); g += `<line class="aim-grid${v === 0 ? ' z' : ''}" x1="${L}" x2="${W - R}" y1="${y.toFixed(1)}" y2="${y.toFixed(1)}"/><text x="${L - 6}" y="${(y + 3.5).toFixed(1)}" text-anchor="end">${esc(aimAx(v, cfg.ax))}</text>`; });
    const every = Math.max(1, Math.ceil((ends ? 52 : 62) / step));
    cfg.cats.forEach((c, i) => { if ((n - 1 - i) % every === 0) g += `<text x="${X(i).toFixed(1)}" y="${H - 7}" text-anchor="${i === n - 1 && !ends ? 'end' : i === 0 ? 'start' : 'middle'}">${esc(c)}</text>`; });
    const tips = AIM.tips[cfg.name] = [], half = n > 1 ? step / 2 : (W - L - R) / 2;
    for (let i = 0; i < n; i++) {
      const tip = { h: cfg.tipH ? cfg.tipH[i] : cfg.cats[i], rows: [] };
      S.forEach(s => { const v = aimN(s.v[i]); if (v != null) tip.rows.push({ c: s.c, n: s.n + (s.dash != null && i >= s.dash ? ' (model path)' : ''), v: aimF(v, cfg.f) }); });
      arr(cfg.marks).filter(m => m.i === i).forEach(m => tip.rows.push({ c: m.c, n: m.n, v: aimF(m.v, cfg.f), b: 1 }));
      tips.push(tip);
      const x = X(i);
      g += `<g class="aim-h" data-tip="${cfg.name}:${i}" tabindex="0" aria-label="${esc(tip.h + ': ' + tip.rows.map(r => r.n + ' ' + r.v).join(', '))}"><rect class="aim-hr" x="${(x - half).toFixed(1)}" y="${T}" width="${(2 * half).toFixed(1)}" height="${H - B - T}"/><line class="aim-xh" x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${T}" y2="${H - B}"/></g>`;
    }
    S.forEach(s => {
      const pts = s.v.map((v, i) => aimN(v) == null ? null : [X(i), Y(v)]);
      if (s.dash != null && s.dash > 0 && s.dash < n) g += `<path class="aim-ln" d="${aimPath(pts.map((p, i) => i < s.dash ? p : null))}" style="stroke:${s.c}"/><path class="aim-ln dash" d="${aimPath(pts.map((p, i) => i >= s.dash - 1 ? p : null))}" style="stroke:${s.c}"/>`;
      else g += `<path class="aim-ln" d="${aimPath(pts)}" style="stroke:${s.c}"/>`;
      const li = pts.map((p, i) => p ? i : -1).filter(i => i >= 0).pop();
      if (li != null) g += `<circle class="aim-dot" cx="${pts[li][0].toFixed(1)}" cy="${pts[li][1].toFixed(1)}" r="4" style="fill:${s.c}"/>`;
    });
    arr(cfg.marks).forEach(m => { const x = X(m.i), y = Y(m.v); g += `<path class="aim-dot" d="M${x.toFixed(1)},${(y - 6).toFixed(1)}l6,6l-6,6l-6,-6Z" style="fill:${m.c}"/>`; });
    if (ends) {
      const lab = [], kept = [];
      S.forEach(s => { const v = aimN(s.v[n - 1]); if (v != null) lab.push({ y: Y(v), t: `${s.short || s.n} ${aimF(v, cfg.f)}` }); });
      arr(cfg.marks).forEach(m => { if (m.l) lab.push({ y: Y(m.v), t: m.l }); });
      lab.forEach(o => { if (kept.every(k => Math.abs(k.y - o.y) >= 11)) kept.push(o); });
      kept.forEach(o => { g += `<text class="aim-el" x="${(W - R + 10).toFixed(1)}" y="${(o.y + 3.5).toFixed(1)}">${esc(o.t)}</text>`; });
    }
    return `<svg class="aim-svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="group" aria-label="${esc(cfg.aria || '')}">${g}</svg>`;
  }
  // a stored model table (id, title, cols, rows [{l, v, f, b, ind}], src, unit, note, est_from); open = shown, otherwise collapsed under its title
  function aimTable(t, open) {
    if (!t || !arr(t.rows).length) return '';
    const e = aimEst(t), cols = arr(t.cols), ec = i => e >= 0 && i >= e ? ' aim-e' : '';
    const tbl = `<div class="tbl-wrap"><table class="dt aim-t"><thead><tr><th>${esc(t.unit || '')}</th>${cols.map((c, i) => `<th class="n${ec(i)}">${esc(c)}${ec(i) ? 'E' : ''}</th>`).join('')}</tr></thead><tbody>` +
      t.rows.map(r => `<tr class="${r.b ? 'aim-b' : ''}${r.ind ? ' aim-i' : ''}"><td>${esc(r.l)}${r.note ? ` <span class="sub">${esc(r.note)}</span>` : ''}</td>${cols.map((c, i) => `<td class="n${ec(i)}">${esc(aimF(arr(r.v)[i], r.f))}</td>`).join('')}</tr>`).join('') +
      `</tbody></table></div>${t.note ? `<p class="sub">${esc(t.note)}</p>` : ''}<p class="aim-src">${esc(t.src || '')}</p>`;
    return open ? `<div class="aim-tb"><h3>${esc(t.title)}</h3>${tbl}</div>` : `<details class="aim-more"><summary>${esc(t.title)}</summary>${tbl}</details>`;
  }
  // a list of records; cols: [key, header, format] where format is an aimF format, 'd' (date), 'w' (wrapping text) or '' (text)
  function aimList(title, src, cols, rows, open, note, bold) {
    if (!arr(rows).length) return '';
    const num = f => f && f !== 'd' && f !== 'w';
    const tbl = `<div class="tbl-wrap"><table class="dt aim-t"><thead><tr>${cols.map(([, h, f]) => `<th${num(f) ? ' class="n"' : ''}>${esc(h)}</th>`).join('')}</tr></thead><tbody>` +
      rows.map(r => `<tr${bold && bold(r) ? ' class="aim-b"' : ''}>${cols.map(([k, , f], j) => { const v = r[k]; return f === 'w' ? `<td class="aim-w">${esc(v)}</td>` : f === 'd' ? `<td class="nowrap">${esc(aimISO(v))}</td>` : num(f) ? `<td class="n">${esc(aimF(v, f))}</td>` : `<td${j === 0 && String(v == null ? '' : v).length <= 28 ? ' class="aim-k"' : ''}>${esc(v)}</td>`; }).join('')}</tr>`).join('') +
      `</tbody></table></div>${note ? `<p class="sub">${esc(note)}</p>` : ''}<p class="aim-src">${esc(src || '')}</p>`;
    return open ? `<div class="aim-tb"><h3>${esc(title)}</h3>${tbl}</div>` : `<details class="aim-more"><summary>${esc(title)}</summary>${tbl}</details>`;
  }
  const aimByDate = xs => arr(xs).slice().sort((a, b) => aimISO(b.date).localeCompare(aimISO(a.date)));
  const aimLeg = (S, line) => (S.length > 1 || line) ? `<div class="legend">${S.map(s => `<span><i style="background:${s.c}"></i>${esc(s.n)}</span>`).join('')}${line ? `<span><i class="aim-lk" style="background:${line.c || 'var(--ink)'}"></i>${esc(line.n)}</span>` : ''}</div>` : '';
  const aimLegL = (S, extra) => `<div class="legend">${S.map(s => `<span><i class="aim-lk" style="background:${s.c}"></i>${esc(s.n)}</span>`).join('')}${extra || ''}</div>`;
  const aimSeg = (label, key, opts, cur) => `<div class="seg" role="group" aria-label="${esc(label)}">${opts.map(([v, l]) => `<button type="button" data-aim="${key}:${esc(v)}" aria-pressed="${cur === v}">${esc(l)}</button>`).join('')}</div>`;
  function aimFig(name, title, sub, cfg, legend) {
    AIM.cfg[name] = Object.assign({ name }, cfg);
    return `<figure class="aim-fig"><figcaption><b>${esc(title)}</b>${sub ? ` <span class="sub">${esc(sub)}</span>` : ''}</figcaption><div class="aim-chart" data-ch="${name}" style="height:${cfg.h || 240}px"></div>${legend || ''}</figure>`;
  }
  const AIM_V = {
    capex() {
      const t = aimT('capex', 'capex_build'); if (!t) return none('The capex build is not in the stored model data.');
      const e = aimEst(t), cats = aimCats(t), last = cats.length - 1, i1 = Math.min(e + 1, last);
      const S = [[/^Merchant GPUs/, 'Merchant GPUs'], [/^ASICs/, 'ASICs'], [/^HBM bought direct/, 'HBM bought direct'], [/^Networking/, 'Networking'], [/^Other IT/, 'Other IT'], [/^Data center/, 'Data center']]
        .map(([re, nm], k) => { const r = aimR(t, re); return r && { n: nm, v: r.v, c: AIM_C[k] }; }).filter(Boolean);
      const tot = aimR(t, /^Total AI capex/), yy = aimR(t, /^y\/y/), comp = aimR(t, /^Compute$/);
      let h = tot && e > 0 ? `<p class="aim-lede">SRS models total AI capex of <b>$${aimF(tot.v[i1], 'bn')}bn in ${esc(cats[i1])}</b>${yy && aimN(yy.v[i1]) != null ? ` (${aimF(yy.v[i1], 'pct')} y/y)` : ''}, up from $${aimF(tot.v[e - 1], 'bn')}bn in ${esc(cats[e - 1])}${comp && tot.v[i1] ? `. Compute (merchant GPUs and ASICs) is ${aimF(comp.v[i1] / tot.v[i1], 'pct')} of it` : ''}.</p>` : '';
      h += `<div class="aim-g2">` + aimFig('capex', 'AI capex by component', '$bn', { cats, est: e, series: S, f: 'bn', ax: 'bn', tot: tot && tot.v, totName: 'Total AI capex', labels: [e - 1, e, i1, last], aria: 'AI capex by component in $bn by year' }, aimLeg(S));
      const cap = aimT('capex', 'capacity'), inc = aimR(cap, /^Incremental GW/), cum = aimR(cap, /^Cumulative GW \(SRS/), sa = aimR(cap, /SemiAnalysis/);
      if (inc) { const ce = aimEst(cap), cc = aimCats(cap); h += aimFig('gw', 'AI compute deployed each year', 'GW of critical IT', { cats: cc, est: ce, series: [{ n: 'GW deployed', v: inc.v, c: AIM_C[0] }], f: 'gw', ax: 'num', labels: [ce - 1, ce, Math.min(ce + 1, cc.length - 1), cc.length - 1], extra: [cum && { n: 'Cumulative GW (SRS)', v: cum.v }, sa && { n: 'Cumulative GW (SemiAnalysis)', v: sa.v }].filter(Boolean), aria: 'GW of AI compute deployed each year' }); }
      h += `</div>`;
      return h + aimTable(t, true) + aimTable(aimT('capex', 'spenders'), true) + ['capacity', 'capex_per_mw', 'hs_chip_share', 'hs_capex_gw', 'lab_gw'].map(id => aimTable(aimT('capex', id))).join('') + aimTable(aimHosts());
    },
    revisions() {
      const d = aimDoc('revisions'), snaps = arr(d.snapshots), ser = arr(d.series); if (!snaps.length || !ser.length) return none('The capex revision history is not in the stored model data.');
      const cos = Object.keys(ser[0].cos || {}), co = cos.includes(AIM.revCo) ? AIM.revCo : 'Total', use = ser.slice(-4);
      // the latest fiscal year gets the first (strongest) color
      const S = use.map((s, k) => ({ n: s.fy, short: s.fy.replace('CY20', "CY'"), v: arr((s.cos || {})[co]), c: AIM_C[use.length - 1 - k] }));
      const sv = aimT('revisions', 'srs_vs_street'), srs = aimR(sv, /^SRS Big-5 capex/), se = aimEst(sv), il = snaps.length - 1;
      const marks = co !== 'Total' || !srs ? [] : use.map((s, k) => { const ci = arr(sv.cols).indexOf(s.fy.replace(/\D/g, '')), v = ci >= 0 && ci >= se ? aimN(srs.v[ci]) : null; return v == null ? null : { i: il, v, c: S[k].c, n: 'SRS estimate, ' + s.fy, l: `SRS '${s.fy.slice(-2)} ${aimF(v, 'bn')}` }; }).filter(Boolean);
      const lt = S[S.length - 1], lv = aimN(lt.v[il]), i4 = il - 4, pv = i4 >= 0 ? aimN(lt.v[i4]) : null, sm = marks.find(m => m.n.endsWith(lt.n));
      let h = lv != null ? `<p class="aim-lede">Street consensus for ${esc(lt.n)} capex${co === 'Total' ? ' at the Big-5' : ' at ' + esc(co)} is <b>$${aimF(lv, 'bn')}bn</b>${pv ? `, up ${aimF(lv / pv - 1, 'pct')} in four quarters (from $${aimF(pv, 'bn')}bn at ${esc(snaps[i4])})` : ''}${sm ? `. SRS is at $${aimF(sm.v, 'bn')}bn, <b>${aimF(sm.v / lv - 1, 'pct')} vs Street</b>` : ''}.</p>` : '';
      h += `<div class="aim-ctl">${aimSeg('Company', 'co', ['Total', 'MSFT', 'GOOGL', 'AMZN', 'META', 'ORCL'].filter(c => cos.includes(c)).map(c => [c, c === 'Total' ? 'Big-5 total' : c]), co)}</div>`;
      h += aimFig('rev', 'Street capex estimate for each year, as it stood at each quarter-end', '$bn · ' + (co === 'Total' ? 'MSFT + GOOGL + AMZN + META + ORCL' : co), { kind: 'lines', h: 270, cats: snaps, tipH: snaps.map((s, i) => `${s} · ${fmtD(arr(d.dates)[i])}, ${String(arr(d.dates)[i] || '').slice(0, 4)}`), series: S, marks, f: 'bn', ax: 'bn', endW: 104, aria: 'Street consensus capex by fiscal year at each quarter-end' }, aimLegL(S, marks.length ? '<span><i class="aim-dk"></i>SRS estimate for that year</span>' : ''));
      const twin = { id: 'rev_twin', title: `Street capex estimates at each quarter-end (${co === 'Total' ? 'Big-5 total' : co})`, cols: snaps, rows: ser.map(s => ({ l: s.fy, v: arr((s.cos || {})[co]), f: 'bn' })), src: d.src, unit: '$bn' };
      return h + aimTable(sv, true) + aimTable(twin) + aimTable(aimT('revisions', 'street_by_co'));
    },
    compute() {
      const M = { gw: ['xpu_gw', 'GW deployed', 'gw', 'GW'], rev: ['xpu_rev', 'Revenue', 'bn', '$bn'], units: ['xpu_units', 'Units shipped', 'num2', 'mm units'] }, m = M[AIM.cmp] || M.gw, t = aimT('compute', m[0]);
      if (!t) return none('The accelerator model is not in the stored model data.');
      const e = aimEst(t), cats = aimCats(t), last = cats.length - 1, share = AIM.cmpMode === 'share';
      const S = ['NVDA', 'AMD', 'Google TPU', 'AWS Trainium', 'OpenAI ASIC', 'Other ASICs'].map((nm, k) => { const r = arr(t.rows).find(x => x.l === nm); return r && { n: nm, v: r.v, c: AIM_C[k] }; }).filter(Boolean);
      const tot = aimR(t, /^Total/), g = aimT('compute', 'xpu_gw'), as = aimR(g, /^ASIC share/), ms = aimR(g, /^Merchant/), ge = aimEst(g), g2 = g ? Math.min(ge + 2, g.cols.length - 1) : -1;
      let h = as && ge >= 0 ? `<p class="aim-lede">ASICs go from <b>${aimF(as.v[ge], 'pct')} of GW deployed in ${esc(aimCats(g)[ge])} to ${aimF(as.v[g2], 'pct')} in ${esc(aimCats(g)[g2])}</b>${ms ? `; NVIDIA and AMD fall from ${aimF(ms.v[ge], 'pct')} to ${aimF(ms.v[g2], 'pct')}` : ''}. Merchant GPUs earn far more revenue per GW than ASICs, so their revenue share stays higher than their GW share.</p>` : '';
      h += `<div class="aim-ctl">${aimSeg('Measure', 'cmp', [['gw', 'GW deployed'], ['rev', 'Revenue'], ['units', 'Units']], AIM.cmp)}${aimSeg('Scale', 'mode', [['share', 'Share of total'], ['abs', 'Absolute']], AIM.cmpMode)}</div>`;
      h += aimFig('xpu', `${m[1]} by accelerator`, share ? 'share of total' : m[3], { cats, est: e, series: S, share, f: m[2], ax: 'num', tot: tot && tot.v, labels: share ? [] : [e - 1, e, Math.min(e + 1, last), last], aria: `${m[1]} by accelerator vendor` }, aimLeg(S));
      return h + aimTable(t, true) + ['xpu_gw', 'xpu_rev', 'xpu_units', 'xpu_rpg'].filter(id => id !== m[0]).map(id => aimTable(aimT('compute', id))).join('');
    },
    econ() {
      const ar = aimT('econ', 'ai_revenue'), by = aimT('econ', 'econ_buyer');
      let h = '', figs = '';
      if (ar) {
        const pick = re => aimR(ar, re), oth = [pick(/^Coding apps/), pick(/^Other model hosts/)].filter(Boolean);
        let S = [[/^OpenAI$/, 'OpenAI'], [/^Anthropic$/, 'Anthropic'], [/^AWS Bedrock/, 'AWS Bedrock'], [/^Google/, 'Google'], [/^Microsoft Foundry/, 'Microsoft Foundry']].map(([re, nm], k) => { const r = pick(re); return r && { n: nm, v: r.v, c: AIM_C[k] }; }).filter(Boolean);
        if (oth.length) S.push({ n: 'Coding apps & other hosts', v: ar.cols.map((c, i) => oth.reduce((a, r) => aimN(r.v[i]) == null ? a : (a || 0) + r.v[i], null)), c: AIM_C[5] });
        let cats = aimCats(ar), e = aimEst(ar), tot = aimR(ar, /^Total$/), k0 = 0;
        while (k0 < cats.length - 1 && S.every(s => aimN(s.v[k0]) == null)) k0++;
        if (k0) { cats = cats.slice(k0); e -= k0; S = S.map(s => Object.assign({}, s, { v: s.v.slice(k0) })); }
        const tv = tot ? tot.v.slice(k0) : null, i1 = Math.min(e + 1, cats.length - 1), lab = S.slice(0, 2).reduce((a, s) => a + (aimN(s.v[i1]) || 0), 0);
        if (tv && aimN(tv[i1])) h += `<p class="aim-lede">AI revenue (model and platform layer, no double counting) reaches <b>$${aimF(tv[i1], 'bn')}bn in ${esc(cats[i1])}</b>, with OpenAI and Anthropic ${aimF(lab / tv[i1], 'pct')} of it.`;
        figs += aimFig('airev', 'AI revenue by company', '$bn', { cats, est: e, series: S, f: 'bn', ax: 'bn', tot: tv, labels: [e - 1, e, i1, cats.length - 1], aria: 'AI revenue by company in $bn' }, aimLeg(S));
      }
      const irr = aimR(by, /^Unlevered IRR/);
      if (irr) {
        const e = aimEst(by), cats = aimCats(by), vs = irr.v.map(aimN), mn = vs.indexOf(Math.min(...vs.filter(v => v != null)));
        if (h && e >= 0) h += ` A GPU bought in ${esc(cats[e])} earns an unlevered IRR of <b>${aimF(vs[e], 'pct')}</b>, against ${aimF(vs[0], 'pct')} for the ${esc(cats[0])} vintage.`;
        figs += aimFig('irr', 'GPU rental: unlevered IRR by vintage', 'each column is the year the GPUs were bought', { cats, est: e, series: [{ n: 'Unlevered IRR', v: irr.v, c: AIM_C[0] }], f: 'pct', ax: 'pct', labels: [0, e, mn, cats.length - 1], aria: 'GPU rental unlevered IRR by vintage' });
      }
      if (h) h += '</p>';
      h += `<div class="aim-g2">${figs}</div>`;
      const dl = aimByDate(aimDoc('econ').deals);
      h += aimList('Compute rental deals: what the contracts imply', aimDoc('econ').deals_src, [['deal', 'Deal', ''], ['date', 'Announced', 'd'], ['value_bn', '$bn', 'bn'], ['years', 'Years', 'num1'], ['annual_bn', '$bn / yr', 'num2'], ['chip', 'Chip', ''], ['mw', 'MW', 'int'], ['gpus', 'GPUs', 'int'], ['rev_mw', '$mm rev / MW', 'num1'], ['gpu_hr', '$ / GPU-hr', 'usd2'], ['prepay', 'Prepay', 'pct'], ['irr', 'IRR', 'pct'], ['ebitda', 'EBITDA margin', 'pct']], dl, true, 'Revenue per MW, $/GPU-hour, IRR and EBITDA margin are the model’s estimates for each contract.');
      return h + aimTable(by, true) + ['rental_pricing', 'econ_hw', 'econ_provider', 'econ_user', 'ai_revenue', 'hyperscaler_ai_rev', 'fleet_return'].map(id => aimTable(aimT('econ', id))).join('');
    },
    labs() {
      const d = aimDoc('labs'), A = d.arr || {}, keys = Object.keys(A);
      let h = '';
      if (keys.length) {
        const mk = s => String(s).slice(0, 7), months = [...new Set(keys.flatMap(k => arr(A[k]).map(p => mk(p[0]))))].filter(m => m >= '2025-01').sort();
        const now = new Date().toISOString().slice(0, 7), dash = months.findIndex(m => m >= now);
        const S = keys.map((k, j) => { const mp = new Map(arr(A[k]).map(p => [mk(p[0]), aimN(p[1])])); return { n: k, v: months.map(m => mp.has(m) ? mp.get(m) : null), c: AIM_C[j], dash: dash > 0 ? dash : null }; });
        const lbl = m => new Date(m + '-15T12:00:00').toLocaleDateString('en-US', { month: 'short', year: '2-digit' }), lblL = m => new Date(m + '-15T12:00:00').toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        const o = S.find(s => s.n === 'OpenAI'), a = S.find(s => s.n === 'Anthropic');
        const x = o && a ? months.findIndex((m, i) => aimN(a.v[i]) != null && aimN(o.v[i]) != null && a.v[i] > o.v[i]) : -1;
        const lastBoth = o && a ? months.map((m, i) => aimN(a.v[i]) != null && aimN(o.v[i]) != null ? i : -1).filter(i => i >= 0).pop() : null;
        if (x >= 0) h += `<p class="aim-lede">In the model, Anthropic’s run-rate revenue passed OpenAI’s in <b>${esc(lblL(months[x]))}</b>${lastBoth != null ? `; by ${esc(lblL(months[lastBoth]))} it was $${aimF(a.v[lastBoth], 'bn')}bn against $${aimF(o.v[lastBoth], 'bn')}bn` : ''}.</p>`;
        h += aimFig('arr', 'Annualized revenue run-rate, by month', '$bn · later months are the model’s path, not reported; the dashed segment starts at the current month', { kind: 'lines', h: 250, cats: months.map(lbl), tipH: months.map(lblL), series: S, f: 'bn', ax: 'bn', endW: 100, aria: 'OpenAI and Anthropic annualized revenue run-rate by month' }, aimLegL(S, dash > 0 ? '<span><i class="aim-lk dash"></i>Model path</span>' : ''));
      }
      const ar = d.anth_rev;
      if (ar && arr(ar.rows).length) h += aimTable({ title: 'Anthropic revenue forecasts, by version of the model', cols: arr(ar.dates).map(x => 'Model of ' + fmtD(x) + ', ' + String(x).slice(0, 4)), rows: ar.rows.map(r => ({ l: String(r[0]), v: r.slice(1), f: 'bn' })), src: ar.src, unit: '$bn' }, true);
      h += aimTable(aimT('labs', 'oai_pl'), true) + aimTable(aimT('labs', 'anth_pl'), true);
      const cm = d.commitments, og = d.oai_gw;
      const yrsT = (o, f, title, src) => o && arr(o.rows).length ? { title, cols: arr(o.years).map(String).concat('Total'), rows: o.rows.map(r => ({ l: `${r.who} · ${r.how}`, v: arr(r.y).concat(r.total), f })).concat([{ l: 'Total', b: 1, f, v: arr(o.years).map((y, i) => o.rows.reduce((s, r) => s + (aimN(arr(r.y)[i]) || 0), 0)).concat(o.rows.reduce((s, r) => s + (aimN(r.total) || 0), 0)) }]), src: src || o.src, unit: f === 'gw' ? 'GW' : '$bn' } : null;
      h += aimTable(yrsT(cm, 'bn', 'OpenAI compute commitments, by counterparty and year')) + aimTable(yrsT(og, 'gw', 'OpenAI compute commitments in GW', cm && cm.src));
      const su = d.sources_uses;
      if (su) h += aimList('OpenAI sources of capital', su.src, [['item', 'Source', ''], ['date', 'Date', 'd'], ['bn', '$bn', 'bn'], ['val', 'Valuation ($bn)', 'int'], ['who', 'From', 'w']], aimByDate(su.sources)) +
        aimList('OpenAI uses of capital', su.src, [['item', 'Use', ''], ['bn', '$bn', 'bn']], arr(su.uses), false, aimN(su.gap) != null ? `The model’s funding gap (sources less uses): −$${aimF(Math.abs(su.gap), 'bn')}bn.` : '', r => /commitments$/i.test(r.item));
      return h + ['oai_projections', 'oai_cash', 'anth_gw'].map(id => aimTable(aimT('labs', id))).join('');
    },
    fin() {
      const ms = aimT('fin', 'market_su'), sp = aimT('fin', 'spreads'), ig = aimT('fin', 'ig_share'), f = aimDoc('fin');
      let h = '', figs = '';
      if (ms) {
        const e = aimEst(ms), cats = aimCats(ms);
        const S = [[/^Hyperscaler cash flow/, 'Hyperscaler cash flow'], [/^AI-related public credit/, 'Public credit (IG + HY)'], [/^Equity/, 'Equity, converts, preferred'], [/^Project financing/, 'Project financing'], [/^Private credit/, 'Private credit']].map(([re, nm], k) => { const r = aimR(ms, re); return r && { n: nm, v: r.v, c: AIM_C[k] }; }).filter(Boolean);
        const use = aimR(ms, /^Total AI capex \(uses\)/), gap = aimR(ms, /^Sources minus uses/), tot = aimR(ms, /^Total sources/);
        const gi = gap ? gap.v.findIndex((v, i) => i >= e && aimN(v) != null && v < 0) : -1;
        if (gi >= 0) h += `<p class="aim-lede">Funding covers AI capex until ${esc(cats[gi - 1] || '')}; in <b>${esc(cats[gi])} the model shows a gap of −$${aimF(Math.abs(gap.v[gi]), 'bn')}bn</b>${gap.v[gi + 1] != null ? `, widening to −$${aimF(Math.abs(gap.v[gi + 1]), 'bn')}bn in ${esc(cats[gi + 1])}` : ''}.`;
        figs += aimFig('su', 'Sources of AI funding vs AI capex', '$bn · columns = sources, line = capex', { cats, est: e, series: S, f: 'bn', ax: 'bn', tot: tot && tot.v, totName: 'Total sources', line: use && { n: 'Total AI capex (uses)', v: use.v }, aria: 'Sources of AI funding against AI capex' }, aimLeg(S, use && { n: 'AI capex (uses)' }));
      }
      const igs = aimR(ig, /^Hyperscaler share of IG/);
      if (h && igs) h += ` Hyperscalers were <b>${aimF(igs.v[igs.v.length - 1], 'pct')} of investment-grade issuance in ${esc(ig.cols[ig.cols.length - 1])}</b>, from ${aimF(igs.v[igs.v.length - 2], 'pct')} in ${esc(ig.cols[ig.cols.length - 2])}.`;
      if (sp) {
        const hs = aimR(sp, /^Hyperscaler average/), im = aimR(sp, /^IG market$/), df = aimR(sp, /^IG market minus/), n = sp.cols.length;
        if (h && df && aimN(df.v[n - 1]) != null) h += ` Their 10-year spreads now sit ${df.v[n - 1] < 0 ? `<b>${aimF(-df.v[n - 1], 'int')}bp wide of</b>` : `<b>${aimF(df.v[n - 1], 'int')}bp inside</b>`} the IG market${aimN(df.v[n - 2]) != null ? ` (${df.v[n - 2] < 0 ? aimF(-df.v[n - 2], 'int') + 'bp wide' : aimF(df.v[n - 2], 'int') + 'bp inside'} at the end of ${esc(sp.cols[n - 2])})` : ''}.`;
        if (hs && im) { const S2 = [{ n: 'Hyperscaler average', short: 'Hyperscalers', v: hs.v, c: AIM_C[0] }, { n: 'IG market', short: 'IG market', v: im.v, c: AIM_C[1] }]; figs += aimFig('spr', '10-year Z-spread: hyperscalers vs the IG market', 'bp · year-end, latest year to date', { kind: 'lines', cats: sp.cols.map(String), series: S2, f: 'int', ax: 'num', zero: false, endW: 112, aria: '10-year Z-spreads of hyperscalers and the IG market' }, aimLegL(S2)); }
      }
      if (h) h += '</p>';
      h += `<div class="aim-g2">${figs}</div>` + aimTable(ms, true) + aimTable(aimT('fin', 'hyper_su'), true);
      h += aimList('30-year hyperscaler bonds: new-issue concession', f.bonds_src, [['bond', 'Bond', ''], ['date', 'Priced', 'd'], ['size_bn', '$bn', 'bn'], ['z', 'New-issue Z (bp)', 'int'], ['pre', 'Curve before (bp)', 'int'], ['nic', 'Concession (bp)', 'num1']], aimByDate(f.bonds), true);
      const c = f.circular || {};
      h += aimList('Circular financing: who funds whom', c.src, [['from', 'From', ''], ['to', 'To', ''], ['eco', 'Ecosystem', ''], ['date', 'Date', 'd'], ['type', 'Type', ''], ['bn', '$bn', 'bn'], ['deal', 'Deal', 'w']], aimByDate(c.mega), false, arr(c.sources).length ? 'Funders: ' + arr(c.sources).filter(x => aimN(x.bn)).map(x => `${x.who} $${aimF(x.bn, 'bn')}bn`).join(', ') + '. Recipients: ' + arr(c.uses).filter(x => aimN(x.bn)).map(x => `${x.who} $${aimF(x.bn, 'bn')}bn`).join(', ') + '.' : '');
      h += aimList('Supply-chain investments by the chip vendors', c.src, [['from', 'From', ''], ['to', 'To', ''], ['eco', 'Area', ''], ['date', 'Date', 'd'], ['type', 'Type', ''], ['bn', '$bn', 'bn'], ['deal', 'Deal', 'w']], aimByDate(c.supply_chain));
      h += aimList('Project financing deals', f.project_src, [['who', 'Borrower', ''], ['what', 'Structure', ''], ['bn', '$bn', 'bn'], ['date', 'Year', 'd'], ['detail', 'Detail', 'w']], arr(f.project));
      h += aimList('Private debt financings', f.debt_src, [['who', 'Borrower', ''], ['investors', 'Lenders', 'w'], ['date', 'Date', 'd'], ['bn', '$bn', 'bn'], ['pricing', 'Pricing', ''], ['structure', 'Structure', ''], ['notes', 'Notes', 'w']], aimByDate(f.debt));
      return h + ['ai_capex_co', 'leverage', 'ig_share', 'spreads', 'ai_wfe'].map(id => aimTable(aimT('fin', id))).join('');
    },
    supply() {
      const t = aimT('supply', 'wfe'); let h = '';
      if (t) {
        const e = aimEst(t), cats = aimCats(t), last = cats.length - 1, i1 = Math.min(e + 1, last);
        const S = [[/^Foundry/, 'Foundry / logic'], [/^DRAM/, 'DRAM'], [/^NAND/, 'NAND']].map(([re, nm], k) => { const r = aimR(t, re); return r && { n: nm, v: r.v, c: AIM_C[k] }; }).filter(Boolean);
        const tot = aimR(t, /^SRS base-case WFE/), st = aimR(t, /^Street$/), sa = aimR(t, /^SemiAnalysis/);
        if (tot && e >= 0) h += `<p class="aim-lede">SRS’s base case has wafer fab equipment at <b>$${aimF(tot.v[e], 'bn')}bn in ${esc(cats[e])} and $${aimF(tot.v[i1], 'bn')}bn in ${esc(cats[i1])}</b>${st && aimN(st.v[e]) != null ? `, against the Street at $${aimF(st.v[e], 'bn')}bn for ${esc(cats[e])}` : ''}${sa && aimN(sa.v[i1]) != null ? ` and SemiAnalysis at $${aimF(sa.v[i1], 'bn')}bn for ${esc(cats[i1])}` : ''}.</p>`;
        h += aimFig('wfe', 'Wafer fab equipment, SRS base case', '$bn', { cats, est: e, series: S, f: 'bn', ax: 'bn', tot: tot && tot.v, totName: 'SRS base-case WFE', labels: [e - 1, e, i1, last], aria: 'Wafer fab equipment by segment in $bn' }, aimLeg(S));
      }
      h += aimTable(t, true);
      const sc = arr(aimDoc('supply').semicap);
      h += aimList('Semicap at the SRS WFE numbers: implied EPS and share prices', aimDoc('supply').semicap_src, [['t', 'Ticker', ''], ['year', 'Year', 'd'], ['wfe', 'WFE assumed ($bn)', 'int'], ['px', 'Price in the model', 'usd2'], ['eps_st', 'Street EPS', 'usd2'], ['eps_srs', 'SRS EPS', 'usd2'], ['vs_st', 'SRS vs Street', 'pct'], ['pe', 'P/E (x)', 'int'], ['target', 'Implied price', 'usd2'], ['updown', 'Upside', 'pct']], sc, true, 'Share prices are the ones carried in the model, not live quotes.');
      return h + ['hbm_balance', 'hbm_rev', 'cowos', 'semi_capex', 'net_tam'].map(id => aimTable(aimT('supply', id))).join('');
    }
  };
  function aimHosts() {
    const hs = aimDoc('capex').hosts; if (!hs || !arr(hs.rows).length) return null;
    const rows = [];
    hs.rows.forEach(r => { rows.push({ l: r.host, v: r.gw, f: 'gw', b: 1 }); if (arr(r.oai).length) rows.push({ l: 'OpenAI share', v: r.oai, f: 'pct', ind: 1 }); if (arr(r.anth).length) rows.push({ l: 'Anthropic share', v: r.anth, f: 'pct', ind: 1 }); });
    const cb = aimT('capex', 'capex_build');
    return { title: 'AI data center capacity by host, and the labs’ share of it', cols: arr(hs.years).map(String), rows, src: hs.src, unit: 'GW', est_from: cb ? cb.est_from : null };
  }
  function aimNotes() {
    const m = aimDoc('meta'), cb = aimT('capex', 'capex_build'), y = '2027';
    const totals = [[aimAt(cb, /^Total AI capex$/, y), 'components (AI Master Model, Overview)'], [aimAt(aimT('capex', 'spenders'), /^Total AI capex \(spender view\)/, y), 'spenders: hyperscalers, neoclouds and China (AI Master Model, Overview)'], [aimAt(aimT('econ', 'econ_hw'), /^Industry AI capex/, y), 'industry capex (AI Economics Master)'], [aimAt(aimT('fin', 'market_su'), /^Total AI capex \(uses\)/, y), 'uses of funds (AI Financings)']].filter(x => x[0] != null);
    const sv = aimT('revisions', 'srs_vs_street'), srs = aimAt(sv, /^SRS Big-5 capex/, y), st = aimAt(sv, /^Street Big-5 capex/, y), fc = aimAt(aimT('fin', 'ai_capex_co'), /^Total$/, y);
    const pl = [aimAt(aimT('labs', 'oai_pl'), /^Revenue$/, y), aimAt(aimT('labs', 'anth_pl'), /^Revenue$/, y)], ep = aimAt(aimT('econ', 'econ_provider'), /^Revenue$/, y);
    const ar = aimT('econ', 'ai_revenue'), ea = [aimAt(ar, /^OpenAI$/, y), aimAt(ar, /^Anthropic$/, y)];
    const asof = m.asof || {};
    return `<details class="fr aim-notes"><summary>Model notes and caveats</summary><ul class="b">` +
      `<li>Loaded from ${arr(m.files).map(x => esc(String(x.name || '').replace(/\.xlsx$/i, '').replace(/_/g, ' '))).join(', ')} on ${esc(fmtD(m.built_at))}.${asof.compute ? ` Accelerator data as of ${esc(asof.compute)}.` : ''}${asof.revisions ? ` Street capex history runs through ${esc(asof.revisions)}.` : ''} Values are as calculated in the workbooks.</li>` +
      (totals.length > 1 ? `<li>The models carry different totals for ${y}E AI capex: ${totals.map(([v, l]) => `$${aimF(v, 'bn')}bn from ${esc(l)}`).join('; ')}. They are built from different inputs and scopes, so compare numbers within a view rather than across views.</li>` : '') +
      (srs != null && st != null && fc != null ? `<li>Hyperscaler capex differs by model. The AI Master Model’s SRS estimate for the Big-5 in ${y}E is $${aimF(srs, 'bn')}bn, ${aimF(srs / st - 1, 'pct')} vs the Street’s $${aimF(st, 'bn')}bn. The AI Financings model’s hyperscaler AI capex case, used in the Financing view, is $${aimF(fc, 'bn')}bn.</li>` : '') +
      (pl.every(v => v != null) && ep != null && ea.every(v => v != null) ? `<li>OpenAI plus Anthropic revenue in ${y}E is $${aimF(pl[0] + pl[1], 'bn')}bn in the AI Master Model’s P&amp;Ls (built on the companies’ own projections), $${aimF(ep, 'bn')}bn in the AI Economics Master summary, and $${aimF(ea[0] + ea[1], 'bn')}bn in its AI revenue by company.</li>` : '') +
      `<li>Caveats that apply to one table (broken networking rows, the HBM supply placeholder) sit under that table. Bond sizes on the Financings model’s Issuance sheet don’t reconcile and are not used.</li>` +
      `<li>To load new model versions, run <code>store/build_ai_models.py</code> on the new files and write each output document to this page’s database collection <code>ai_models</code>.</li></ul></details>`;
  }
  function aimSectionHtml() {
    const m = aimDoc('meta'), files = arr(m.files).map(x => String(x.name || '').replace(/\.xlsx$/i, '').replace(/_/g, ' '));
    let h = `<section class="panel" id="ai-models"><div class="panel-h"><h2>SRS AI models</h2><span class="sub">${files.length ? esc(files.join(' · ')) : 'AI Master Model · AI Economics Master · AI Financings'}${m.built_at ? ' · loaded ' + esc(fmtD(m.built_at)) : ''}</span></div>`;
    if (!AIM.docs) return h + `<p class="sub${AIM.err ? ' c-neg' : ''}">${esc(AIM.err || 'Loading the SRS model data…')}</p></section>`;
    if (!AIM_V[AIM.view]) AIM.view = 'capex';
    const calls = arr(m.calls);
    if (calls.length) h += `<div class="summary aim-calls">${calls.map(c => `<div class="stat"><button type="button" data-aim="view:${esc(c.view || 'capex')}" title="Open ${esc((AIM_VIEWS.find(v => v[0] === c.view) || [, ''])[1])}"><span class="v${c.tone === 'neg' ? ' c-neg' : c.tone === 'pos' ? ' c-pos' : ''}">${esc(c.v)}</span><span class="l">${esc(c.l)}</span></button></div>`).join('')}</div>`;
    h += `<div class="seg aim-seg" role="group" aria-label="Model view">${AIM_VIEWS.map(([k, l]) => `<button type="button" data-aim="view:${k}" aria-pressed="${AIM.view === k}">${esc(l)}</button>`).join('')}</div>`;
    return h + `<div id="aim-body" class="aim-view">${aimViewHtml()}</div>${aimNotes()}<div class="aim-tip" role="presentation" hidden></div></section>`;
  }
  function aimViewHtml() {
    AIM.cfg = {}; AIM.tips = {};
    try { return AIM_V[AIM.view](); } catch (e) { return none('This view could not be built from the stored model data.'); }
  }
  function aimDraw(sec) {
    sec.querySelectorAll('.aim-chart[data-ch]').forEach(el => {
      const cfg = AIM.cfg[el.dataset.ch]; if (!cfg) return;
      const W = Math.max(260, Math.floor(el.clientWidth));
      try { el.innerHTML = cfg.kind === 'lines' ? aimLines(cfg, W) : aimCols(cfg, W); } catch (e) { el.innerHTML = none('This chart could not be drawn.'); }
    });
  }
  function aimMount() {
    const sec = document.getElementById('ai-models'); if (!sec || !AIM.docs) return;
    sec.addEventListener('click', e => {
      const b = e.target.closest && e.target.closest('[data-aim]'); if (!b || !sec.contains(b)) return;
      const [k, v] = b.dataset.aim.split(':');
      if (k === 'view') { AIM.view = v; try { localStorage.setItem('td-aim-view', v); } catch (x) {} } else if (k === 'co') AIM.revCo = v; else if (k === 'cmp') AIM.cmp = v; else if (k === 'mode') AIM.cmpMode = v;
      const body = sec.querySelector('#aim-body'); if (!body) return;
      body.innerHTML = aimViewHtml();
      sec.querySelectorAll('.aim-seg [data-aim]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.aim === 'view:' + AIM.view)));
      aimDraw(sec);
      if (k === 'view' && b.closest('.aim-calls')) { const s = sec.querySelector('.aim-seg'); if (s && s.getBoundingClientRect().top < 60) s.scrollIntoView({ block: 'start' }); }
    });
    const tip = sec.querySelector('.aim-tip');
    const show = (g, x, y) => {
      const [nm, i] = String(g.dataset.tip || '').split(':'), d = (AIM.tips[nm] || [])[+i]; if (!d || !tip) return;
      tip.textContent = '';
      const hd = document.createElement('div'); hd.className = 'aim-tip-h'; hd.textContent = d.h; tip.appendChild(hd);
      d.rows.forEach(r => { const row = document.createElement('div'), k = document.createElement('i'), v = document.createElement('b'), s = document.createElement('span'); row.className = 'aim-tip-r' + (r.b ? ' tot' : ''); if (r.c) k.style.background = r.c; v.textContent = r.v; s.textContent = r.n; row.append(k, v, s); tip.appendChild(row); });
      tip.hidden = false;
      const tw = tip.offsetWidth, th = tip.offsetHeight, vw = window.innerWidth, vh = window.innerHeight;
      let lx = x + 14, ly = y + 14; if (lx + tw > vw - 8) lx = x - tw - 14; if (lx < 8) lx = 8; if (ly + th > vh - 8) ly = y - th - 14; if (ly < 8) ly = 8;
      tip.style.left = lx + 'px'; tip.style.top = ly + 'px';
    };
    const hide = () => { if (tip) tip.hidden = true; };
    const at = e => { const g = e.target.closest && e.target.closest('.aim-h'); if (g && sec.contains(g)) show(g, e.clientX, e.clientY); else hide(); };
    sec.addEventListener('pointermove', at); sec.addEventListener('pointerdown', at); sec.addEventListener('pointerleave', hide);
    sec.addEventListener('focusin', e => { const g = e.target.closest && e.target.closest('.aim-h'); if (g) { const r = g.getBoundingClientRect(); show(g, r.left + r.width / 2, r.top + 8); } });
    sec.addEventListener('focusout', hide);
    if (!AIM.sc) { AIM.sc = 1; window.addEventListener('scroll', () => { const t = document.querySelector('#ai-models .aim-tip'); if (t) t.hidden = true; }, { passive: true }); }
    aimDraw(sec);
    if (window.ResizeObserver) { if (AIM.ro) AIM.ro.disconnect(); AIM.w = sec.clientWidth; AIM.ro = new ResizeObserver(() => { const w = sec.clientWidth; if (Math.abs(w - AIM.w) > 6) { AIM.w = w; requestAnimationFrame(() => aimDraw(sec)); } }); AIM.ro.observe(sec); }
  }
  function aimLoad(done) {
    if (AIM.loaded) return; AIM.loaded = true;
    const to = setTimeout(() => { if (!AIM.docs) { AIM.err = 'The SRS model data did not load in this view.'; done(); } }, 10000);
    (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => db ? db.collection('ai_models').get() : null)
      .then(snap => { clearTimeout(to); const o = {}; (snap ? snap.docs : []).forEach(d => { if (d.exists) o[d.id] = JSON.parse(JSON.stringify(d.data())); }); if (Object.keys(o).length) { AIM.docs = o; AIM.err = ''; } else AIM.err = snap ? 'No SRS model data is stored in this page yet.' : 'The SRS model data is not available in this view.'; done(); })
      .catch(() => { clearTimeout(to); AIM.err = 'The SRS model data could not be read from this page’s database.'; done(); });
  }
  // ================= AI › Bank forecasts: banks' AI data-center GW and AI capex paths, 2024–2030 =================
  // The numbers live in this page's database, collection "ai", doc "bank_forecasts":
  //   {asof, method, years:[2024..2030], est_idx, banks:[{bank, status: ok|partial|unavailable, note,
  //     gw: {kind: installed|adds, geo, scope, v[7], fl[7], src:[{t, d, u}]} | null, capex: {scope, v[7], fl[7], src[]} | null}]}
  // Claude refreshes that document with ArtifactData; page rebuilds never touch it.
  const BF = { doc: null, err: '', loaded: false, m: 'capex', ro: null, w: 0 };
  try { const v0 = localStorage.getItem('td-bf-m'); if (v0) BF.m = v0; } catch (e) {}
  const BF_M = [['capex', 'AI capex ($bn)'], ['installed', 'GW installed base'], ['adds', 'GW added per year']];
  function bfLoad(done) {
    if (BF.loaded) return; BF.loaded = true;
    const to = setTimeout(() => { if (!BF.doc) { BF.err = 'The bank forecasts did not load in this view.'; done(); } }, 10000);
    (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => db ? db.collection('ai').doc('bank_forecasts').get() : null)
      .then(sn => { clearTimeout(to); if (sn && sn.exists) { BF.doc = JSON.parse(JSON.stringify(sn.data())); BF.err = ''; } else BF.err = sn ? 'No bank forecasts are stored in this page yet.' : 'The bank forecasts are kept in this page’s database; open the page on claude.ai to see them.'; done(); })
      .catch(() => { clearTimeout(to); BF.err = 'The bank forecasts could not be read from this page’s database.'; done(); });
  }
  const bfMed = xs => { const s = xs.filter(v => aimN(v) != null).sort((a, b) => a - b), n = s.length; return n ? (n % 2 ? s[(n - 1) / 2] : (s[n / 2 - 1] + s[n / 2]) / 2) : null; };
  const bfHas = s => !!s && arr(s.v).some(v => aimN(v) != null);
  function bfBodyHtml() {
    const d = BF.doc, Y = arr(d.years), ei = +d.est_idx || 0, B = arr(d.banks);
    const col = new Map(B.filter(b => bfHas(b.capex) || bfHas(b.gw)).map((b, i) => [b.bank, AIM_C[i % AIM_C.length]]));
    const pick = b => BF.m === 'capex' ? b.capex : (b.gw && b.gw.kind === BF.m ? b.gw : null);
    const f = BF.m === 'capex' ? 'int' : 'gw', unit = BF.m === 'capex' ? '$bn' : 'GW';
    const cats = Y.map((y, i) => i >= ei ? y + 'E' : String(y));
    const rows = B.map(b => ({ b, s: pick(b) })).filter(x => bfHas(x.s));
    const S = rows.map(x => ({ n: x.b.bank + (x.s.geo && x.s.geo !== 'Global' ? ' (' + x.s.geo + ')' : ''), short: x.b.bank, v: Y.map((_, i) => aimN(arr(x.s.v)[i])), c: col.get(x.b.bank), dash: ei }));
    const glob = S.filter((s, k) => !rows[k].s.geo || rows[k].s.geo === 'Global');
    const med = Y.map((_, i) => bfMed(glob.map(s => s.v[i]))), lo = Y.map((_, i) => { const xs = glob.map(s => s.v[i]).filter(v => v != null); return xs.length ? Math.min(...xs) : null; }), hi = Y.map((_, i) => { const xs = glob.map(s => s.v[i]).filter(v => v != null); return xs.length ? Math.max(...xs) : null; });
    const SS = glob.length > 2 ? S.concat([{ n: 'Median (global series)', short: 'Median', v: med, c: 'var(--ink)', dash: ei }]) : S;
    const label = (BF_M.find(m => m[0] === BF.m) || [])[1] || '';
    let h = '';
    if (!S.length) h += none('No bank in this set publishes a ' + esc(label) + ' series.');
    else h += aimFig('bf', label + ' by bank', 'Solid = reported (' + esc(cats.slice(0, ei).join(', ')) + '), dashed = estimates · hover for values', { kind: 'lines', cats, series: SS, f, ax: '', h: 300, endW: 120, aria: label + ' forecasts by bank, ' + Y[0] + ' to ' + Y[Y.length - 1] }, aimLegL(SS));
    const cell = (s, i) => { const v = aimN(arr(s.v)[i]), fl = arr(s.fl)[i]; return v == null ? '<td class="n sub">–</td>' : `<td class="n${i >= ei ? ' aim-e' : ''}"${fl ? ` title="${esc(fl)}"` : ''}>${esc(aimF(v, f))}${fl ? '<sup>*</sup>' : ''}</td>`; };
    const srcs = s => arr(s && s.src).map(x => `<a class="ext" href="${esc(x.u)}" target="_blank" rel="noopener">${esc(x.t)}</a> <span class="sub">${esc(x.d)}</span>`).join('<br>');
    h += `<div class="aim-tb"><h3>${esc(label)}: every bank</h3><div class="tbl-wrap"><table class="dt aim-t"><thead><tr><th>Bank</th><th>Scope</th>${cats.map((c, i) => `<th class="n${i >= ei ? ' aim-e' : ''}">${esc(c)}</th>`).join('')}<th>Source (AlphaSense)</th></tr></thead><tbody>` +
      B.map(b => { const s = pick(b); if (bfHas(s)) return `<tr><td class="aim-k"><b>${esc(b.bank)}</b>${s.geo && s.geo !== 'Global' ? ` <span class="chip">${esc(s.geo)} only</span>` : ''}</td><td class="aim-w">${esc(s.scope)}${s.note ? `<br><span class="sub">${esc(s.note)}</span>` : ''}</td>${Y.map((_, i) => cell(s, i)).join('')}<td class="aim-w">${srcs(s)}</td></tr>`;
        const why = b.status === 'unavailable' ? b.note : BF.m === 'capex' ? 'No AI capex series in the notes read.' + (b.note ? ' ' + b.note : '') : (b.gw ? `Its GW series is ${b.gw.kind === 'adds' ? 'annual additions' : 'an installed base'}: switch view.` : 'No GW series in the notes read.' + (b.note ? ' ' + b.note : ''));
        return `<tr><td class="aim-k"><b>${esc(b.bank)}</b>${b.status === 'unavailable' ? ' <span class="chip out">no access</span>' : ''}</td><td class="aim-w sub" colspan="${Y.length + 2}">${esc(why)}</td></tr>`; }).join('') +
      (glob.length > 2 ? ['Median', 'Low', 'High'].map((l, k) => `<tr class="aim-b"><td>${l}</td><td class="sub">Global series only</td>${[med, lo, hi][k].map((v, i) => `<td class="n${i >= ei ? ' aim-e' : ''}">${v == null ? '–' : esc(aimF(v, f))}</td>`).join('')}<td></td></tr>`).join('') : '') +
      `</tbody></table></div><p class="sub">${esc(unit)} · <sup>*</sup> hover the figure: derived from the bank's growth rates or cumulative targets, a range midpoint, or a narrower scope that year. Median, low and high leave out US-only series and need at least three global series.</p></div>`;
    return h;
  }
  function bfSectionHtml() {
    const top = `<section class="panel" id="ai-banks"><div class="panel-h"><h2>Bank forecasts: AI data-center GW and AI capex, 2024–2030</h2><span class="sub">${BF.doc ? 'As of ' + esc(BF.doc.asof || '') + ' · AlphaSense broker research' : ''}</span></div>`;
    if (!BF.doc) return top + `<p class="sub">${esc(BF.err || 'Loading the bank forecasts…')}</p></section>`;
    const B = arr(BF.doc.banks), ok = B.filter(b => bfHas(b.capex) || bfHas(b.gw)), cx = B.filter(b => bfHas(b.capex)).map(b => aimN(arr(b.capex.v)[6])).filter(v => v != null), m30 = bfMed(cx);
    const gi = B.filter(b => b.gw && b.gw.kind === 'installed' && b.gw.geo === 'Global').map(b => aimN(arr(b.gw.v)[6])).filter(v => v != null);
    return top + `<p class="aim-lede">${esc(BF.doc.method || '')}</p>` +
      `<div class="summary"><div class="stat"><span class="v">${ok.length} / ${B.length}</span><span class="l">banks with figures in AlphaSense</span></div>` +
      `<div class="stat"><span class="v">${m30 == null ? '–' : '$' + esc(aimF(m30, 'int')) + 'bn'}</span><span class="l">median 2030 AI capex (${cx.length} banks${cx.length ? ', $' + esc(aimF(Math.min(...cx), 'int')) + '–' + esc(aimF(Math.max(...cx), 'int')) + 'bn' : ''})</span></div>` +
      `<div class="stat"><span class="v">${gi.length ? esc(aimF(bfMed(gi), 'num1')) + ' GW' : '–'}</span><span class="l">2030 global installed base (${gi.length} bank${gi.length === 1 ? '' : 's'})</span></div></div>` +
      `<div class="seg aim-seg" role="group" aria-label="Metric">${BF_M.map(([k, l]) => `<button type="button" data-bf="${k}" aria-pressed="${BF.m === k}">${esc(l)}</button>`).join('')}</div>` +
      `<div id="bf-body" class="aim-view">${bfBodyHtml()}</div><div class="aim-tip" hidden></div></section>`;
  }
  function bfMount() {
    const sec = document.getElementById('ai-banks'); if (!sec || !BF.doc) return;
    sec.addEventListener('click', e => {
      const b = e.target.closest && e.target.closest('[data-bf]'); if (!b || !sec.contains(b)) return;
      BF.m = b.dataset.bf; try { localStorage.setItem('td-bf-m', BF.m); } catch (x) {}
      sec.querySelectorAll('[data-bf]').forEach(x => x.setAttribute('aria-pressed', String(x.dataset.bf === BF.m)));
      const body = sec.querySelector('#bf-body'); if (body) { body.innerHTML = bfBodyHtml(); aimDraw(sec); }
    });
    const tip = sec.querySelector('.aim-tip');
    const show = (g, x, y) => {
      const [nm, i] = String(g.dataset.tip || '').split(':'), d = (AIM.tips[nm] || [])[+i]; if (!d || !tip) return;
      tip.textContent = '';
      const hd = document.createElement('div'); hd.className = 'aim-tip-h'; hd.textContent = d.h; tip.appendChild(hd);
      d.rows.forEach(r => { const row = document.createElement('div'), k = document.createElement('i'), v = document.createElement('b'), s = document.createElement('span'); row.className = 'aim-tip-r' + (r.b ? ' tot' : ''); if (r.c) k.style.background = r.c; v.textContent = r.v; s.textContent = r.n; row.append(k, v, s); tip.appendChild(row); });
      tip.hidden = false;
      const tw = tip.offsetWidth, th = tip.offsetHeight, vw = window.innerWidth, vh = window.innerHeight;
      let lx = x + 14, ly = y + 14; if (lx + tw > vw - 8) lx = x - tw - 14; if (lx < 8) lx = 8; if (ly + th > vh - 8) ly = y - th - 14; if (ly < 8) ly = 8;
      tip.style.left = lx + 'px'; tip.style.top = ly + 'px';
    };
    const hide = () => { if (tip) tip.hidden = true; };
    const at = e => { const g = e.target.closest && e.target.closest('.aim-h'); if (g && sec.contains(g)) show(g, e.clientX, e.clientY); else hide(); };
    sec.addEventListener('pointermove', at); sec.addEventListener('pointerdown', at); sec.addEventListener('pointerleave', hide);
    sec.addEventListener('focusin', e => { const g = e.target.closest && e.target.closest('.aim-h'); if (g) { const r = g.getBoundingClientRect(); show(g, r.left + r.width / 2, r.top + 8); } });
    sec.addEventListener('focusout', hide);
    if (!BF.sc) { BF.sc = 1; window.addEventListener('scroll', () => { const t = document.querySelector('#ai-banks .aim-tip'); if (t) t.hidden = true; }, { passive: true }); }
    aimDraw(sec);
    if (window.ResizeObserver) { if (BF.ro) BF.ro.disconnect(); BF.w = sec.clientWidth; BF.ro = new ResizeObserver(() => { const w = sec.clientWidth; if (Math.abs(w - BF.w) > 6) { BF.w = w; requestAnimationFrame(() => aimDraw(sec)); } }); BF.ro.observe(sec); }
  }
  function renderAI() {
    const host = document.getElementById('v-ai'); if (!host) return;
    const st = AI.st, meta = new Map(arr((D.dp_index || {}).meta).map(m => [m.rid, m]));
    const f1 = v => v == null ? '–' : (+v).toFixed(1);
    const paint = () => {
      let h = head('AI', 'AI infrastructure', 'SRS’s own AI models (capex, accelerator share, economics, financing, supply chain), where the gigawatts are being built and where politics puts them at risk, everything on Astera Labs revenue, and every datapoint on compute supply versus demand.') +
        `<nav class="sk-tabs" aria-label="AI sections"><a href="#ai/models">SRS models</a><a href="#ai/banks">Bank forecasts</a><a href="#ai/dc">Data centers &amp; politics</a><a href="#ai/alab">ALAB revenue</a><a href="#ai/compute">Compute supply &amp; demand</a><a href="#ai/gpu">GPU rental prices</a></nav>`;
      // ---- 0) SRS AI models (page database, collection "ai_models") ----
      h += aimSectionHtml();
      // ---- 0b) bank forecasts (page database, collection "ai", doc "bank_forecasts") ----
      h += bfSectionHtml();
      // ---- 1) data centers by state ----
      if (!AI_DC.rows.length) h += `<section class="panel" id="ai-dc"><h2>Data centers: gigawatts by state and political risk</h2><p class="sub">${esc(AI.dcErr || 'Loading the state figures…')}</p><h3>Policy and political datapoints</h3><div id="ai-pol">${aiRowsHtml('policy')}</div></section>`;
      else {
      const R = AI_DC.rows.map(([s, t, a, c, n]) => ({ s, t, a: a || 0, c: c || 0, n: n || 0, ra: a, rc: c, rn: n, tot: (a || 0) + (c || 0) + (n || 0) }));
      const byTier = [1, 2, 3, 4, 5, null].map(t => { const xs = R.filter(r => r.t === t); return { t, a: xs.reduce((x, r) => x + r.a, 0), c: xs.reduce((x, r) => x + r.c, 0), n: xs.reduce((x, r) => x + r.n, 0), k: xs.length }; }).filter(x => x.k);
      const T = byTier.reduce((x, r) => ({ a: x.a + r.a, c: x.c + r.c, n: x.n + r.n }), { a: 0, c: 0, n: 0 });
      const risk = byTier.filter(x => x.t >= 4).reduce((x, r) => ({ a: x.a + r.a, c: x.c + r.c, n: x.n + r.n }), { a: 0, c: 0, n: 0 });
      const pc = (x, y) => y ? Math.round(100 * x / y) + '%' : '–';
      const key = st.dcSort; let rows = R.filter(r => !st.tier || String(r.t) === st.tier);
      rows.sort((x, y) => key === 's' ? x.s.localeCompare(y.s) : key === 't' ? ((y.t || 0) - (x.t || 0)) || (y.n - x.n) : key === 'a' ? y.a - x.a : key === 'c' ? y.c - x.c : key === 'tot' ? y.tot - x.tot : y.n - x.n);
      const mx = Math.max(...R.map(r => r.tot));
      h += `<section class="panel" id="ai-dc"><div class="panel-h"><h2>Data centers: gigawatts by state and political risk</h2><span class="sub">Critical IT GW · ${esc(AI_DC.source)}</span></div>` +
        `<div class="summary">` +
        `<div class="stat"><span class="v">${f1(T.a)}</span><span class="l">GW active (operating today)</span></div>` +
        `<div class="stat"><span class="v">${f1(T.c)}</span><span class="l">GW under construction</span></div>` +
        `<div class="stat"><span class="v">${f1(T.n)}</span><span class="l">GW announced, not yet under construction</span></div>` +
        `<div class="stat"><span class="v c-neg">${f1(risk.c + risk.n)}</span><span class="l">GW building or announced in Tier 4–5 states (${pc(risk.c + risk.n, T.c + T.n)} of the pipeline)</span></div>` +
        `<div class="stat"><span class="v c-neg">${f1(((R.find(r => r.s === 'TX') || {}).c || 0) + ((R.find(r => r.s === 'TX') || {}).n || 0))}</span><span class="l">GW of that in Texas alone (now Tier 4)</span></div></div>` +
        `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Political risk tier</th><th class="n">States</th><th class="n">Active</th><th class="n">Construction</th><th class="n">Announced</th><th class="n">Pipeline share</th></tr></thead><tbody>${byTier.map(x => `<tr class="ai-t${x.t || 0}"><td>${esc(x.t ? AI_TIER[x.t] : 'Not tiered on the map')}</td><td class="n">${x.k}</td><td class="n">${f1(x.a)}</td><td class="n">${f1(x.c)}</td><td class="n">${f1(x.n)}</td><td class="n">${pc(x.c + x.n, T.c + T.n)}</td></tr>`).join('')}</tbody></table></div>` +
        `<p class="sub">At risk = Tier 4 (${R.filter(r => r.t === 4).map(r => r.s).join(', ')}) and Tier 5 (${R.filter(r => r.t === 5).map(r => r.s).join(', ')}, full moratorium). Tier 3 is the watch list. Pipeline = under construction + announced.</p>` +
        `<div class="ctl"><label for="ai-tier">Tier <select id="ai-tier"><option value="">All</option>${[5, 4, 3, 2, 1].map(t => `<option value="${t}"${st.tier === String(t) ? ' selected' : ''}>${esc(AI_TIER[t])}</option>`).join('')}</select></label>` +
        `<label for="ai-sort">Sort <select id="ai-sort">${[['ann', 'Announced GW'], ['tot', 'Total GW'], ['c', 'Under construction'], ['a', 'Active'], ['t', 'Highest risk first'], ['s', 'State A–Z']].map(([v, l]) => `<option value="${v}"${key === v ? ' selected' : ''}>${l}</option>`).join('')}</select></label><span class="count">${rows.length} states</span></div>` +
        `<div class="tbl-wrap"><table class="dt"><thead><tr><th>State</th><th>Tier</th><th class="n">Active</th><th class="n">Construction</th><th class="n">Announced</th><th class="n">Total</th><th style="min-width:220px">Mix</th></tr></thead><tbody>${rows.map(r => `<tr class="ai-t${r.t || 0}"><td><b>${r.s}</b></td><td><span class="chip ai-tc${r.t || 0}">${r.t ? 'Tier ' + r.t : '–'}</span>${r.t >= 4 ? ' <span class="c-neg">at risk</span>' : ''}</td><td class="n">${f1(r.ra)}</td><td class="n">${f1(r.rc)}</td><td class="n">${f1(r.rn)}</td><td class="n"><b>${f1(r.tot)}</b></td><td><div class="ai-bar" title="Active ${f1(r.ra)} · construction ${f1(r.rc)} · announced ${f1(r.rn)} GW"><i class="a" style="width:${100 * r.a / mx}%"></i><i class="c" style="width:${100 * r.c / mx}%"></i><i class="n" style="width:${100 * r.n / mx}%"></i></div></td></tr>`).join('')}</tbody></table></div>` +
        `<div class="legend"><span><i style="background:var(--ink)"></i>Active</span><span><i style="background:var(--accent)"></i>Under construction</span><span><i style="background:#8a4fc7"></i>Announced</span></div>` +
        `<details class="fr"><summary>Source exhibit (stored with this page)</summary><img src="${esc(AI_DC.img)}" alt="Source map of critical IT GW by state and stage, colored by political risk tier" style="max-width:100%;height:auto;border:1px solid var(--rule);border-radius:6px;margin-top:8px" loading="lazy"><p class="sub">${esc(AI_DC.note || '')}</p></details>` +
        `<h3>Policy and political datapoints</h3><div id="ai-pol">${aiRowsHtml('policy')}</div></section>`;
      }
      // ---- 2) ALAB revenue ----
      const alabRev = arr(D.bobby).concat(arr(D.rebecca)).filter(r => /^ALAB/i.test(r.ticker || '')).sort((a, b) => String(b.report_date).localeCompare(String(a.report_date)));
      h += `<section class="panel" id="ai-alab"><div class="panel-h"><h2>Astera Labs (ALAB): revenue</h2><a href="#stocks/ALAB/qr">Open ALAB on Stocks →</a></div>` +
        `<h3>Quarterly revenue, segments and consensus (live from Visible Alpha)</h3><div class="qr" id="ai-qr"><p class="sub">Loading Visible Alpha…</p></div>` +
        `<h3>Earnings prints</h3>${alabRev.map(r => `<details class="fr-sec"><summary>${esc(r.quarter || '')} · ${esc(r.report_date || '')} · ${esc(r.source === 'rebecca' ? 'Rebecca recap' : 'Earnings review')}</summary><p>${xInline(r.headline || '')}</p><ul class="b">${arr(r.summary).filter(s => AI_RE.alabRev.test(s)).map(s => `<li>${esc(s)}</li>`).join('')}</ul>${r.url && /^https?:/.test(r.url) ? `<a class="ext" href="${esc(r.url)}" target="_blank" rel="noopener">Open the full page →</a>` : ''}</details>`).join('') || none('No ALAB earnings pages in this build.')}` +
        `<h3>Every revenue datapoint on ALAB</h3><div class="ctl"><label for="ai-aq">Search <input type="search" id="ai-aq" value="${esc(st.alabQ)}" placeholder="Scorpio, Trainium, guide…"></label></div><div id="ai-alabdp">${aiRowsHtml('alab')}</div></section>`;
      // ---- GPU rental prices ----
      h += `<section class="panel" id="ai-gpu"><div class="panel-h"><h2>GPU rental prices ($ per GPU-hour)</h2><span class="sub">From your datapoints</span></div>${AI.rows ? gpuSectionHtml(gpuPoints(AI.rows), st) : '<p class="sub">Loading datapoints…</p>'}</section>`;
      // ---- 3) compute supply / demand ----
      h += `<section class="panel" id="ai-compute"><div class="panel-h"><h2>Compute supply versus demand</h2><span class="sub">Every datapoint in Supabase that speaks to compute being tight or loose, all companies</span></div>` +
        `<div id="ai-cmp-sum"></div>` +
        `<div class="ctl"><label for="ai-b">Area <select id="ai-b"><option value="">All</option>${AI_BUCKETS.map(([b]) => `<option${st.bucket === b ? ' selected' : ''}>${esc(b)}</option>`).join('')}<option${st.bucket === 'Other' ? ' selected' : ''}>Other</option></select></label>` +
        `<label for="ai-tone">Read <select id="ai-tone"><option value="">All</option><option value="tight"${st.tone === 'tight' ? ' selected' : ''}>Supply tight / demand ahead</option><option value="loose"${st.tone === 'loose' ? ' selected' : ''}>Loosening / digestion</option></select></label>` +
        `<label for="ai-days">Window <select id="ai-days">${[[30, '1 month'], [90, '3 months'], [180, '6 months'], [100000, 'All']].map(([v, l]) => `<option value="${v}"${+st.days === v ? ' selected' : ''}>${l}</option>`).join('')}</select></label>` +
        `<label for="ai-q">Search <input type="search" id="ai-q" value="${esc(st.q)}" placeholder="Ticker or word"></label></div><div id="ai-cmp">${aiRowsHtml('compute')}</div></section>`;
      host.innerHTML = h; wire(); aimMount(); bfMount();
      const sub = (location.hash.split('/')[1] || ''); host.querySelectorAll('.sk-tabs a').forEach(a => a.toggleAttribute('aria-current', a.getAttribute('href') === '#ai/' + sub));
      if (sub) { const el = document.getElementById('ai-' + (sub === 'dc' ? 'dc' : sub)); if (el) setTimeout(() => el.scrollIntoView({ block: 'start' }), 0); }
      const qh = document.getElementById('ai-qr'); if (qh && window.__qrMount) { const co = (window.__qrFind && window.__qrFind('ALAB')) || { t: 'ALAB', bbg: 'ALAB US', name: 'Astera Labs' }; try { window.__qrMount(qh, co); } catch (e) { qh.innerHTML = none('The Visible Alpha table could not load here.'); } }
      dedupeNames(host);
    };
    function aiPick(kind) {
      if (!AI.rows) return null;
      const cut = new Date(Date.now() - (+st.days || 100000) * 864e5).toISOString().slice(0, 10);
      if (kind === 'policy') return AI.rows.filter(r => AI_RE.policy.test(r[9]) && /data ?cent|power|grid|gw\b|gigawatt|utility|site/i.test(r[9]));
      if (kind === 'alab') return AI.rows.filter(r => { const m = meta.get(r[1]); return m && /^ALAB/i.test(m.t || '') && AI_RE.alabRev.test(r[9]) && (!st.alabQ || r[9].toLowerCase().includes(st.alabQ.toLowerCase())); });
      return AI.rows.filter(r => r[2] >= cut && AI_RE.compute.test(r[9])).map(r => { r.__b = (AI_BUCKETS.find(([, re]) => re.test(r[9])) || ['Other'])[0]; r.__t = AI_RE.loose.test(r[9]) && !AI_RE.tight.test(r[9]) ? 'loose' : AI_RE.tight.test(r[9]) ? 'tight' : ''; return r; })
        .filter(r => (!st.bucket || r.__b === st.bucket) && (!st.tone || r.__t === st.tone) && (!st.q || (r[9] + ' ' + ((meta.get(r[1]) || {}).t || '')).toLowerCase().includes(st.q.toLowerCase())));
    }
    function aiRowsHtml(kind) {
      if (AI.err) return `<p class="sub c-neg">${esc(AI.err)}</p>`;
      const xs = aiPick(kind); if (!xs) return `<p class="sub">Loading datapoints…</p>`;
      const rows = xs.slice().sort((a, b) => String(b[2]).localeCompare(String(a[2])));
      const lim = G.n || (kind === 'policy' ? 40 : 200);
      return `<p class="sub">${rows.length} datapoints${rows.length > lim ? `, newest ${lim} shown (raise "Show" at the top for more)` : ''}.</p><div class="tbl-wrap"><table class="dt"><thead><tr><th>Date</th><th>Company</th>${kind === 'compute' ? '<th>Area</th><th>Read</th>' : ''}<th>Impact</th><th>Datapoint</th><th>Source</th></tr></thead><tbody>${rows.slice(0, lim).map(r => { const m = meta.get(r[1]) || {}; return `<tr><td class="nowrap">${esc(r[2])}</td><td>${m.t ? tk(m.t) : ''}</td>${kind === 'compute' ? `<td class="sub">${esc(r.__b)}</td><td class="nowrap">${r.__t === 'tight' ? '<span class="c-pos">Tight</span>' : r.__t === 'loose' ? '<span class="c-neg">Loosening</span>' : '<span class="sub">–</span>'}</td>` : ''}<td class="nowrap">${r[4] === 1 ? '<span class="c-pos">▲</span>' : r[4] === -1 ? '<span class="c-neg">▼</span>' : '◆'}</td><td class="ev-wrap">${esc(r[9])}</td><td class="ev-src">${esc((AI.SRC || [])[r[7]] || '')}</td></tr>`; }).join('') || `<tr><td colspan="7">${none('Nothing matches.')}</td></tr>`}</tbody></table></div>`;
    }
    function cmpSummary() {
      const el = document.getElementById('ai-cmp-sum'); if (!el || !AI.rows) return;
      const save = { bucket: st.bucket, tone: st.tone, q: st.q }; Object.assign(st, { bucket: '', tone: '', q: '' }); const all = aiPick('compute'); Object.assign(st, save);
      const g = AI_BUCKETS.map(([b]) => b).concat('Other').map(b => { const xs = all.filter(r => r.__b === b); return { b, n: xs.length, t: xs.filter(r => r.__t === 'tight').length, l: xs.filter(r => r.__t === 'loose').length }; }).filter(x => x.n);
      el.innerHTML = `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Area</th><th class="n">Datapoints</th><th class="n">Tight</th><th class="n">Loosening</th><th>Balance</th></tr></thead><tbody>${g.map(x => `<tr><td><button type="button" class="tkbtn ai-bk" data-b="${esc(x.b)}">${esc(x.b)}</button></td><td class="n">${x.n}</td><td class="n c-pos">${x.t}</td><td class="n c-neg">${x.l}</td><td><div class="ai-bal"><i class="t" style="width:${x.t + x.l ? 100 * x.t / (x.t + x.l) : 0}%"></i><i class="l" style="width:${x.t + x.l ? 100 * x.l / (x.t + x.l) : 0}%"></i></div></td></tr>`).join('')}</tbody></table></div><p class="sub">Tight = shortage, sold out, allocation, lead times or demand ahead of supply. Loosening = oversupply, overbuild, digestion, push-outs or cancellations.</p>`;
      el.querySelectorAll('.ai-bk').forEach(b => b.addEventListener('click', () => { st.bucket = st.bucket === b.dataset.b ? '' : b.dataset.b; paint(); document.getElementById('ai-compute').scrollIntoView({ block: 'start' }); }));
    }
    function wire() {
      const $ = id => document.getElementById(id), re = () => paint();
      $('ai-tier') && $('ai-tier').addEventListener('change', e => { st.tier = e.target.value; re(); });
      $('ai-sort') && $('ai-sort').addEventListener('change', e => { st.dcSort = e.target.value; re(); });
      $('ai-b') && $('ai-b').addEventListener('change', e => { st.bucket = e.target.value; re(); });
      $('ai-tone') && $('ai-tone').addEventListener('change', e => { st.tone = e.target.value; re(); });
      $('ai-days') && $('ai-days').addEventListener('change', e => { st.days = +e.target.value; re(); });
      $('gpu-b') && $('gpu-b').addEventListener('change', e => { st.gpuBasis = e.target.value; re(); });
      $('gpu-f') && $('gpu-f').addEventListener('change', e => { st.gpuFam = e.target.value; re(); });
      const live = (id, k, box, kind) => $(id) && $(id).addEventListener('input', e => { st[k] = e.target.value; const b = $(box); if (b) b.innerHTML = aiRowsHtml(kind); dedupeNames(b); });
      live('ai-q', 'q', 'ai-cmp', 'compute'); live('ai-aq', 'alabQ', 'ai-alabdp', 'alab');
      cmpSummary();
    }
    paint();
    aimLoad(paint);
    bfLoad(paint);
    if (!AI.dcLoaded) { AI.dcLoaded = true; (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => db ? db.collection('ai').doc('dc_states').get() : null)
      .then(sn => { if (sn && sn.exists) Object.assign(AI_DC, JSON.parse(JSON.stringify(sn.data()))); else AI.dcErr = 'The state data center figures are not loaded in this view.'; paint(); })
      .catch(() => { AI.dcErr = 'The state data center figures could not be read from this page’s database.'; paint(); }); }
    if (!AI.rows) getDP().then(({ SRC, ROWS }) => { AI.SRC = SRC; AI.rows = ROWS; paint(); }).catch(e => { AI.err = 'Could not load the datapoint files: ' + (e && e.message || e); paint(); });
  }

  // ================= AI THESIS: SRS AI Update (Oct 2026) baseline + what has changed since =================
  // Content lives in this page's database, not in the code, so rebuilds never touch it:
  //   collection "thesis", doc "ai"            the thesis (baseline from the deck + current status, signposts, changelog)
  //   collection "thesis_updates", one doc each datapoint flagged as strengthening / weakening / changing the thesis
  // The "AI thesis tracker" scheduled task writes both; Bobby marks flags reviewed or dismissed here.
  const TH = { doc: null, ups: [], err: '', started: false, db: null, show: 'open' };
  const TH_ST = { strengthening: ['s-positive', 'Strengthening'], intact: ['a-aligned', 'Intact'], watch: ['s-mixed', 'Watch'], weakening: ['s-negative', 'Weakening'], broken: ['s-very_negative', 'Broken'], ahead: ['s-positive', 'Ahead of deck'], on_track: ['a-aligned', 'On track'], behind: ['s-negative', 'Behind deck'], no_read: ['out', 'No new read'], new: ['a-split', 'New tenet'] };
  const TH_DIR = { strengthens: ['s-positive', 'Strengthens'], weakens: ['s-negative', 'Weakens'], changes: ['a-split', 'Changes'], neutral: ['out', 'Context'] };
  const thChip = (k, map) => { const m = (map || TH_ST)[k] || ['out', k || '–']; return `<span class="chip ${m[0]}">${esc(m[1])}</span>`; };
  const thList = xs => arr(xs).length ? `<ul class="b">${arr(xs).map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '';
  const thTable = t => !t || !arr(t.rows).length ? '' : `<div class="tbl-wrap"><table class="dt th-t"><thead><tr>${arr(t.cols).map((c, i) => `<th${i ? ' class="n"' : ''}>${esc(c)}</th>`).join('')}</tr></thead><tbody>${arr(t.rows).map(r => `<tr${String(r[0]).startsWith('**') ? ' class="th-b"' : ''}>${arr(r).map((c, i) => `<td${i ? ' class="n"' : ''}>${esc(String(c).replace(/^\*\*/, ''))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${t.note ? `<p class="sub">${esc(t.note)}</p>` : ''}`;

  /* ai-tenets v1 */
  // AI thesis › By tenet. Doc thesis/ai_tenets mirrors Supabase thesis_tenets (tenets, Bobby's view, fact checks)
  // and thesis_tenet_evidence (links to research_evidence rows, with stance supports / challenges / mixed).
  const TN_V = { confirmed: ['s-positive', 'Confirmed'], supported: ['s-positive', 'Supported'], mostly: ['a-aligned', 'Mostly right'], partly: ['s-mixed', 'Partly right'],
    reported: ['a-aligned', 'Reported'], unverified: ['out', 'Unverified'], not_supported: ['s-negative', 'Not supported'], inference: ['out', 'SRS inference'] };
  const TN_SD = { supports: ['pos', 'Supports'], challenges: ['neg', 'Challenges'], mixed: ['mix', 'Mixed'] };
  /* ai-merge v1 */
  // One AI tab: #v-aimode holds the switch, #v-ai is Models & data, #v-thesis the thesis (overview or by tenet).
  const AIMX = { m: null };
  const aiMode = () => { if (AIMX.m) return AIMX.m; try { const m = localStorage.getItem('ai-mode'); return ['overview', 'tenets', 'data'].includes(m) ? m : 'overview'; } catch (e) { return 'overview'; } };
  const aiModeSet = m => { AIMX.m = m; try { localStorage.setItem('ai-mode', m); } catch (e) {} };
  function aiShow() {
    const m = aiMode(), A = document.getElementById('v-ai'), T = document.getElementById('v-thesis'), B = document.getElementById('v-aimode');
    if (B) {
      B.innerHTML = `<div class="seg ai-mode" role="group" aria-label="AI view">${[['overview', 'Thesis'], ['tenets', 'Thesis by tenet'], ['data', 'Models &amp; data']].map(([k, l]) => `<button type="button" data-aim="${k}" aria-pressed="${m === k}">${l}</button>`).join('')}</div>`;
      B.querySelectorAll('[data-aim]').forEach(b => b.addEventListener('click', () => { aiModeSet(b.dataset.aim); if (location.hash !== '#ai') history.replaceState(null, '', '#ai'); aiShow(); window.scrollTo(0, 0); }));
    }
    if (A) A.hidden = m !== 'data'; if (T) T.hidden = m === 'data';
    const host = m === 'data' ? A : T;
    try { if (m === 'data') renderAI(); else { TH.view = m; renderThesis(); } } catch (e) { if (host) host.innerHTML = `<div class="nores">This tab could not render: ${esc(e.message)}</div>`; }
  }
  const thView = () => { if ((location.hash || '').startsWith('#thesis/tenets')) return 'tenets'; if (TH.view) return TH.view; try { return localStorage.getItem('th-view') || 'overview'; } catch (e) { return 'overview'; } };
  const thViewSeg = () => { const v = thView(); return `<div class="seg th-vs" role="group" aria-label="Thesis view"><button type="button" data-thv="overview" aria-pressed="${v === 'overview'}">Overview</button><button type="button" data-thv="tenets" aria-pressed="${v === 'tenets'}">By tenet</button></div>`; };
  function thSegBind(host) {
    host.querySelectorAll('[data-thv]').forEach(b => b.addEventListener('click', () => { TH.view = b.dataset.thv; try { localStorage.setItem('th-view', TH.view); } catch (e) {} if ((location.hash || '').startsWith('#thesis/')) history.replaceState(null, '', '#thesis'); renderThesis(); }));
    host.querySelectorAll('[data-tn]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById('tn-' + a.dataset.tn); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
  }
  /* ai-tenets v2 */
  const TNF = (() => { let f = {}; try { f = JSON.parse(localStorage.getItem('tn-filt') || '{}'); } catch (e) {} return Object.assign({ tenet: '', sent: '', days: '', n: '10' }, f); })();
  const tnSave = () => { try { localStorage.setItem('tn-filt', JSON.stringify(TNF)); } catch (e) {} };
  const tnScore = d => d.score != null ? Number(d.score) : (d.stance === 'supports' ? 1 : d.stance === 'challenges' ? -1 : 0);
  const tnDots = s => { const c = s > 0 ? 'g' : s < 0 ? 'r' : 'b', n = Math.abs(s) === 2 ? 2 : 1, lab = s === 2 ? 'Strongly supports' : s === 1 ? 'Supports' : s === 0 ? 'Neutral' : s === -1 ? 'Weakens' : 'Strongly weakens'; return `<span class="tn-dots ${c}" title="${lab} the thesis" aria-label="${lab}">${'<i></i>'.repeat(n)}</span>`; };
  const TN_SENT = [['', 'All sentiment'], ['g', 'All supportive (green)'], ['2', '●● Strongly supports'], ['1', '● Supports'], ['0', '● Neutral (blue)'], ['-1', '● Weakens'], ['-2', '●● Strongly weakens'], ['r', 'All weakening (red)']];
  const TN_DAYS = [['', 'All dates'], ['7', 'Last week'], ['14', 'Last 2 weeks'], ['30', 'Last month'], ['90', 'Last 3 months']];
  const TN_N = [['5', '5 per tenet'], ['10', '10 per tenet'], ['25', '25 per tenet'], ['', 'All']];
  function tnPass(d, asOf) {
    const s = tnScore(d), f = TNF.sent;
    if (f === 'g' && !(s > 0)) return false; if (f === 'r' && !(s < 0)) return false;
    if (f !== '' && f !== 'g' && f !== 'r' && s !== Number(f)) return false;
    if (TNF.days) { const lim = new Date(asOf); lim.setDate(lim.getDate() - Number(TNF.days)); if (new Date(d.date) < lim) return false; }
    return true;
  }
  function thTenets() {
    const D2 = TH.tenets; if (!D2) return `<section class="panel">${none('No tenet breakdown saved yet.')}</section>`;
    const TS = arr(D2.tenets).slice().sort((a, b) => (a.sort || 0) - (b.sort || 0));
    const asOf = String(D2.updated_at || new Date().toISOString()).slice(0, 10);
    const opt = (xs, v) => xs.map(([k, l]) => `<option value="${esc(k)}"${String(v) === k ? ' selected' : ''}>${esc(l)}</option>`).join('');
    const bar = `<div class="tn-bar" role="group" aria-label="Datapoint filters">` +
      `<label>Tenet <select data-tnf="tenet"><option value="">All tenets</option>${TS.map(t => `<option value="${esc(t.key)}"${TNF.tenet === t.key ? ' selected' : ''}>${esc(t.title)}</option>`).join('')}</select></label>` +
      `<label>Sentiment <select data-tnf="sent">${opt(TN_SENT, TNF.sent)}</select></label>` +
      `<label>How far back <select data-tnf="days">${opt(TN_DAYS, TNF.days)}</select></label>` +
      `<label>How many <select data-tnf="n">${opt(TN_N, TNF.n)}</select></label>` +
      `<span class="sub">Newest first</span></div>`;
    const key = `<div class="tn-key">${[[2, 'Strongly supports'], [1, 'Supports'], [0, 'Neutral or mixed'], [-1, 'Weakens'], [-2, 'Strongly weakens']].map(([s, l]) => `<span>${tnDots(s)}${esc(l)}</span>`).join('')}<span class="sub">scored against the AI bull thesis</span></div>`;
    const bal = ds => { const g = ds.filter(d => tnScore(d) > 0).length, r = ds.filter(d => tnScore(d) < 0).length, b = ds.length - g - r, n = ds.length || 1; return `<div class="tn-bal" title="${g} green · ${b} blue · ${r} red"><i class="g" style="width:${g / n * 100}%"></i><i class="b" style="width:${b / n * 100}%"></i><i class="r" style="width:${r / n * 100}%"></i></div>`; };
    const strip = `<section class="panel"><div class="panel-h"><h2>Tenets</h2><span class="muted">updated ${esc(fmtD(asOf))}</span></div>${key}` +
      `<div class="tn-strip">${TS.map(t => { const n = arr(t.dps), g = n.filter(d => tnScore(d) > 0).length, r = n.filter(d => tnScore(d) < 0).length; return `<a href="#ai" data-tn="${esc(t.key)}"><span class="chips">${thChip(t.status)}</span><b>${esc(t.title)}</b>${n.length ? bal(n) : ''}<span class="sub">${n.length} datapoints${n.length ? ` · ${g} green · ${r} red` : ''}${arr(t.checks).length ? ` · ${arr(t.checks).length} fact check${arr(t.checks).length > 1 ? 's' : ''}` : ''}</span></a>`; }).join('')}</div>` +
      (D2.storage ? `<p class="sub">${esc(D2.storage)}</p>` : '') + `</section>`;
    const src = xs => arr(xs).map(([t, u]) => u ? `<a class="ext" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t)).join('<br>');
    const lim = TNF.n ? Number(TNF.n) : Infinity;
    const body = TS.filter(t => !TNF.tenet || t.key === TNF.tenet).map(t => {
      const FC = arr(t.checks), all = arr(t.dps).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)) || (b.id || 0) - (a.id || 0));
      const pass = all.filter(d => tnPass(d, asOf)), DP = pass.slice(0, lim), G = t.gw;
      return `<section class="panel tn" id="tn-${esc(t.key)}"><div class="panel-h"><h2>${esc(t.title)}</h2><span class="chips">${thChip(t.status)}</span></div>` +
        (t.claim ? `<p class="lede">${esc(t.claim)}</p>` : '') +
        (t.srs_view ? `<p class="tn-view"><b>SRS view:</b> ${esc(t.srs_view)}</p>` : '') +
        (G && arr(G.rows).length ? `<h3>${esc(G.title || 'GW deployed')}</h3><div class="tbl-wrap"><table class="dt tn-gw"><thead><tr>${arr(G.cols).map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${arr(G.rows).map(r => `<tr>${arr(r).map((c, i) => `<td class="${i > 1 ? 'wrap' : ''}">${i === 1 ? esc(fmtD(c)) : esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${G.note ? `<p class="sub">${esc(G.note)}</p>` : ''}` : '') +
        (FC.length ? `<h3>Fact check</h3><div class="tbl-wrap"><table class="dt tn-fc"><thead><tr><th>Claim</th><th>Verdict</th><th>What we found</th><th>Sources</th></tr></thead><tbody>${FC.map(f => `<tr><td class="wrap"><b>${esc(f.claim)}</b></td><td>${thChip(f.verdict, TN_V)}</td><td class="wrap">${esc(f.text)}</td><td class="wrap">${src(f.sources)}</td></tr>`).join('')}</tbody></table></div>` : '') +
        `<h3>Datapoints <span class="muted">${DP.length} of ${pass.length}${pass.length !== all.length ? ` matching (${all.length} total)` : ''}</span></h3>` +
        (DP.length ? `<div class="list">${DP.map(d => `<div class="li">${tnDots(tnScore(d))}<div class="body"><div class="chips"><span class="tk-chip">${esc(d.t)}</span></div>${esc(d.text)}<div class="srcl"><span>Source</span>${esc(d.src || '')} · SB #${esc(d.id)}</div></div><div class="side">${esc(fmtD(d.date))}</div></div>`).join('')}</div>` : none(all.length ? 'No datapoints match these filters.' : 'No datapoints linked yet.')) +
        (arr(t.staged).length ? `<h3>Staged, not yet in Supabase</h3>${arr(t.staged).map(g => `<div class="tn-stage"><div class="chips"><span class="tk-chip">${esc(g.t)}</span><span class="sub">${esc(fmtD(g.date))}</span></div>${esc(g.text)}<div class="srcl"><span>Source</span>${esc(g.primary)}${g.secondary ? ' via ' + esc(g.secondary) : ''}</div></div>`).join('')}` : '') +
        `</section>`;
    }).join('');
    setTimeout(() => document.querySelectorAll('#v-thesis [data-tnf]').forEach(s => s.addEventListener('change', () => { TNF[s.dataset.tnf] = s.value; tnSave(); renderThesis(); })), 0);
    return strip + bar + body;
  }

  function thStart() {
    if (TH.started) return; TH.started = true;
    if (!(window.claude && typeof window.claude.use === 'function')) { TH.err = 'The thesis is kept in this page’s database; open the page on claude.ai to see it.'; return; }
    window.claude.use('db').then(db => {
      TH.db = db;
      db.collection('thesis').onSnapshot(snap => { const d = snap.docs.find(x => x.id === 'ai'); TH.doc = d ? JSON.parse(JSON.stringify(d.data())) : null; const dt = snap.docs.find(x => x.id === 'ai_tenets'); TH.tenets = dt ? JSON.parse(JSON.stringify(dt.data())) : null; if (!TH.doc) TH.err = 'No thesis saved yet.'; thPaint(); },
        e => { TH.err = 'The thesis could not load: ' + ((e && e.code) || 'error'); thPaint(); });
      db.collection('thesis_updates').onSnapshot(snap => {
        TH.ups = snap.docs.map(d => ({ id: d.id, ...JSON.parse(JSON.stringify(d.data())) })).sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')) || String(b.created || '').localeCompare(String(a.created || '')));
        const c = document.getElementById('th-count'), n = TH.ups.filter(u => (u.status || 'open') === 'open').length; if (c) c.textContent = n ? n : ''; thPaint();
      }, () => {});
    }).catch(() => { TH.err = 'The thesis is not available in this view.'; thPaint(); });
  }
  const thPaint = () => { if (/^#(ai|thesis)(\/|$)/.test(location.hash || '') && aiMode() !== 'data') renderThesis(); };
  function renderThesis() {
    const host = document.getElementById('v-thesis'); if (!host) return;
    thStart();
    const T = TH.doc;
    let h = head('AI thesis', T ? esc(T.title || 'AI thesis') : 'AI thesis', T ? esc(T.subtitle || '') : '');
    if (!T) { host.innerHTML = h + `<section class="panel">${none(esc(TH.err || 'Loading the thesis…'))}</section>`; return; }
    if (thView() === 'tenets') { host.innerHTML = h + thTenets(); thSegBind(host); return; }
    h += `<nav class="sk-tabs" aria-label="Thesis sections"><a href="#ai" data-th="th-now">Where we stand</a><a href="#ai" data-th="th-flags">Flagged datapoints</a><a href="#ai" data-th="th-sign">Signposts</a><a href="#ai" data-th="th-pil">Pillars</a><a href="#ai" data-th="th-cases">Bull / bear</a><a href="#ai" data-th="th-roi">ROI math</a><a href="#ai" data-th="th-risk">Risks</a><a href="#ai" data-th="th-next">Next steps</a><a href="#ai" data-th="th-log">Changelog</a></nav>`;
    // 1) where we stand
    const S = T.stance || {}, N = T.now || {};
    h += `<section class="panel th-now" id="th-now"><div class="panel-h"><h2>Where we stand</h2><span class="muted">Baseline: ${esc((T.deck || {}).name || '')} · last reviewed ${esc(fmtD(T.updated_at))}</span></div>` +
      `<div class="th-verdict">${thChip(N.status)}<b>${esc(S.headline || '')}</b></div>${thList(S.points)}` +
      (N.summary ? `<h3>Since the deck</h3><p class="lede">${esc(N.summary)}</p>` : '') + thList(N.points) +
      (N.recommendation_check ? `<p class="th-rec"><b>Recommendation check:</b> ${esc(N.recommendation_check)}</p>` : '') + `</section>`;
    // 2) flagged datapoints
    const open = TH.ups.filter(u => (u.status || 'open') === 'open'), shown = TH.show === 'open' ? open : TH.ups;
    h += `<section class="panel" id="th-flags"><div class="panel-h"><h2>Flagged datapoints <span class="muted">${open.length} to review</span></h2>` +
      `<div class="seg" role="group" aria-label="Show"><button type="button" data-ths="open" aria-pressed="${TH.show === 'open'}">To review</button><button type="button" data-ths="all" aria-pressed="${TH.show === 'all'}">All (${TH.ups.length})</button></div></div>` +
      `<p class="sub">Datapoints from your digests that strengthen, weaken or change a part of the thesis. Mark each one reviewed once you have read it; the tracker folds reviewed items into the signposts and changelog.</p>` +
      (shown.length ? `<div class="list">${shown.map(u => `<div class="li"><span class="stripe ${u.direction === 'strengthens' ? 'pos' : u.direction === 'weakens' ? 'neg' : u.direction === 'changes' ? 'mix' : ''}"></span><div class="body">` +
        `<div class="chips">${thChip(u.direction, TH_DIR)}${u.pillar ? `<span class="chip">${esc(u.pillar)}</span>` : ''}${u.signpost ? `<span class="chip out">${esc(u.signpost)}</span>` : ''}${(u.status || 'open') !== 'open' ? `<span class="chip out">${esc(u.status)}</span>` : ''}</div>` +
        `<div><b>${esc(u.headline || '')}</b> ${esc(u.text || '')}</div>${u.why ? `<div class="sub">Why it matters: ${esc(u.why)}</div>` : ''}${u.proposed_change ? `<div class="sub th-prop">Proposed thesis change: ${esc(u.proposed_change)}</div>` : ''}` +
        `<div class="srcl"><span>Source</span>${esc(u.source || '')}${u.ev_id ? ` · datapoint #${esc(u.ev_id)}` : ''}</div></div>` +
        `<div class="side">${esc(fmtD(u.date))}${(u.status || 'open') === 'open' ? `<div class="th-act"><button type="button" class="btn" data-thu="${esc(u.id)}" data-st="reviewed">Reviewed</button><button type="button" class="btn" data-thu="${esc(u.id)}" data-st="dismissed">Dismiss</button></div>` : ''}</div></div>`).join('')}</div>` : none(TH.show === 'open' ? 'Nothing waiting for review.' : 'No datapoints flagged yet.')) + `</section>`;
    // 3) signposts
    const SG = arr(T.signposts);
    h += `<section class="panel" id="th-sign"><h2>Signposts</h2><p class="sub">What the deck assumed, what would confirm or break it, and the latest read from your datapoints.</p>` +
      `<div class="tbl-wrap"><table class="dt th-sg"><thead><tr><th>Signpost</th><th>Deck baseline</th><th>Bull if</th><th>Bear if</th><th>Latest read</th><th>Status</th></tr></thead><tbody>${SG.map(s => `<tr><td><b>${esc(s.metric)}</b></td><td class="wrap">${esc(s.deck)}</td><td class="wrap c-pos">${esc(s.bull)}</td><td class="wrap c-neg">${esc(s.bear)}</td>` +
      `<td class="wrap">${s.latest ? `${esc(s.latest.value)}<div class="sub">${esc(fmtD(s.latest.date))}${s.latest.source ? ' · ' + esc(s.latest.source) : ''}</div>` : '<span class="muted">–</span>'}</td><td>${thChip(s.status)}</td></tr>`).join('')}</tbody></table></div></section>`;
    // 4) pillars
    h += `<section class="panel" id="th-pil"><h2>Why we are bullish on OpenAI and Anthropic</h2><div class="grid3">${arr(T.pillars).map(p => `<div class="theme"><div class="chips">${thChip(p.status)}</div><h3>${esc(p.title)}</h3><p>${esc(p.claim)}</p>${p.since ? `<p class="sub"><b>Since the deck:</b> ${esc(p.since)}</p>` : ''}</div>`).join('')}</div></section>`;
    // 5) cases
    const C = T.cases || {};
    h += `<section class="panel" id="th-cases"><h2>Bull, uber-bull and bear cases</h2><p class="sub">Probabilities are unassigned in the deck.</p><div class="grid3">` +
      [['Bull case', C.bull], ['Uber-bull case', C.uber], ['Bear case', C.bear]].map(([t, xs]) => `<div class="theme"><h3>${t}</h3>${thList(xs)}</div>`).join('') + `</div>` +
      (C.tam ? `<h3>TAM math</h3>${thTable(C.tam)}` : '') + (C.downside ? `<h3>Downside in the stocks</h3>${thList(C.downside)}` : '') + `</section>`;
    // 6) ROI math
    const R0 = T.roi || {};
    h += `<section class="panel" id="th-roi"><h2>Capex ROI math</h2>${thList(R0.points)}` + arr(R0.tables).map(t => `<h3>${esc(t.title)}</h3>${thTable(t)}`).join('') + `</section>`;
    // 7) risks
    h += `<section class="panel" id="th-risk"><h2>Risks</h2><div class="grid2">${arr(T.risks).map(r => `<div class="theme"><div class="chips">${thChip(r.status)}</div><h3>${esc(r.title)}</h3>${thList(r.points)}${r.since ? `<p class="sub"><b>Since the deck:</b> ${esc(r.since)}</p>` : ''}</div>`).join('')}</div></section>`;
    // 8) next steps + questions
    h += `<section class="panel" id="th-next"><div class="grid2"><div><h2>Next steps</h2>${thList(T.next_steps)}</div><div><h2>Questions for OpenAI / Anthropic</h2>${thList(T.questions)}</div></div></section>`;
    // 9) changelog
    const LG = arr(T.changelog).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)));
    h += `<section class="panel" id="th-log"><h2>Changelog</h2>${LG.length ? `<div class="list">${LG.map(l => `<div class="li"><div class="body"><b>${esc(l.change)}</b>${l.why ? ` <span class="sub">${esc(l.why)}</span>` : ''}</div><div class="side">${esc(fmtD(l.date))}</div></div>`).join('')}</div>` : none('No changes yet.')}</section>`;
    host.innerHTML = h;
    host.querySelectorAll('[data-th]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById(a.dataset.th); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
    thSegBind(host);
    host.querySelectorAll('[data-ths]').forEach(b => b.addEventListener('click', () => { TH.show = b.dataset.ths; renderThesis(); }));
    host.querySelectorAll('[data-thu]').forEach(b => b.addEventListener('click', async () => {
      const u = TH.ups.find(x => x.id === b.dataset.thu); if (!u || !TH.db) return; b.disabled = true;
      const { id, ...rest } = u;
      try { await TH.db.collection('thesis_updates').doc(id).set({ ...rest, status: b.dataset.st, reviewed_at: new Date().toISOString() }); } catch (x) { b.disabled = false; alert('Could not save: ' + ((x && x.message) || 'error')); }
    }));
  }
  thStart();

  // ================= MANAGEMENT & INSIDERS: questions for management, insider transactions, Canary =================
  const MG = { st: { co: '', q: '', sec: '', isort: 'net', iq: '' } };
  function renderMgmt() {
    const host = document.getElementById('v-mgmt'); if (!host) return;
    const M = D.mgmt || {}, I = M.insiders || {}, st = MG.st;
    let Q = MG.Q || M.questions || {};
    if (!MG.Q && Q.file && !arr(Q.companies).length && !MG.loading) { MG.loading = true;
      fetch(Q.file).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(j => { MG.Q = j; renderMgmt(); }).catch(e => { MG.err = 'Could not load the questions file: ' + (e && e.message || e); renderMgmt(); }); }
    const money = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); const s = a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : a >= 1e3 ? (a / 1e3).toFixed(0) + 'k' : a.toFixed(0); return (v < 0 ? '−$' : '$') + s; };
    const sub = (location.hash.split('/')[1] || '');
    const paint = () => {
      let h = head('Management & insiders', 'Questions for management and insider transactions', 'Questions to ask each company (Canary super analysts, plus your own management-prep pages), what insiders are buying and selling, and what the Canary data sets offer.') +
        `<nav class="sk-tabs" aria-label="Sections"><a href="#mgmt/questions">Questions for management</a><a href="#mgmt/insiders">Insider transactions</a><a href="#mgmt/canary">Canary data sets</a></nav>`;
      h += mgCallouts(M, I, Q);
      // ---- questions ----
      const cos = arr(Q.companies);
      const prepRuns = arr((D.prep || {}).runs).filter(r => /management-prep/i.test(r.skill || ''));
      const secs = [...new Set(cos.map(c => c.sector).filter(Boolean))].sort();
      const vis = cos.filter(c => (!st.sec || c.sector === st.sec) && (!st.co || c.t === st.co) && (!st.q || JSON.stringify(c).toLowerCase().includes(st.q.toLowerCase())));
      h += `<section class="panel" id="mg-questions"><div class="panel-h"><h2>Questions for management</h2><span class="sub">${esc(Q.source || 'Canary super analyst')}${Q.as_of ? ' · ' + esc(fmtD(Q.as_of)) : ''} · ${cos.length} companies</span></div>` +
        (!cos.length ? (MG.err ? `<p class="sub c-neg">${esc(MG.err)}</p>` : `<p class="sub">${Q.file ? 'Loading questions…' : 'No questions loaded yet.'}</p>`) :
        `<div class="ctl"><label for="mg-co">Company <select id="mg-co"><option value="">All</option>${cos.slice().sort((a, b) => (a.tier - b.tier) || String(a.t).localeCompare(b.t)).map(c => `<option value="${esc(c.t)}"${st.co === c.t ? ' selected' : ''}>${esc(c.t)} · ${esc(c.name || '')}</option>`).join('')}</select></label>` +
        `<label for="mg-sec">Sector <select id="mg-sec"><option value="">All</option>${secs.map(s => `<option${st.sec === s ? ' selected' : ''}>${esc(s)}</option>`).join('')}</select></label>` +
        `<label for="mg-q">Search <input type="search" id="mg-q" value="${esc(st.q)}" placeholder="Word or theme"></label><span class="count">${vis.length} companies</span></div>` +
        vis.map(c => { const qs = arr(c.questions), th = [...new Set(qs.map(x => x.theme || 'Questions'))];
          const preps = prepRuns.filter(r => new RegExp('\\b' + String(c.t).split(' ')[0].replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b').test(r.title || ''));
          return `<details class="fr-sec"${vis.length <= 3 ? ' open' : ''}><summary>${tk(c.t)} ${esc(c.name || '')} <span class="sub">· Tier ${esc(c.tier)} · ${qs.length} questions${arr(c.debates).length ? ' · ' + arr(c.debates).length + ' debates' : ''}</span></summary>` +
            th.map(t => `<h4>${esc(t)}</h4><ol class="mg-q">${qs.filter(x => (x.theme || 'Questions') === t).map(x => `<li>${String(x.q || '').length > 380 ? `<details class="mg-long"><summary>${esc(String(x.q).slice(0, 300).replace(/\s+\S*$/, ''))}…</summary>${esc(x.q)}</details>` : esc(x.q)}${x.why ? `<div class="sub">${esc(x.why)}</div>` : ''}</li>`).join('')}</ol>`).join('') +
            (arr(c.debates).length ? `<h4>Open debates</h4><ul class="b">${arr(c.debates).map(d => `<li><b>${esc(d.title)}</b>${d.summary ? ' · ' + esc(d.summary) : ''}${d.bull ? `<div class="sub c-pos">Bull: ${esc(d.bull)}</div>` : ''}${d.bear ? `<div class="sub c-neg">Bear: ${esc(d.bear)}</div>` : ''}</li>`).join('')}</ul>` : '') +
            (c.monitoring ? `<p class="sub"><b>What to monitor:</b> ${esc(c.monitoring)}</p>` : '') +
            (preps.length ? `<p class="sub">Your management-prep pages: ${preps.map(r => `<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.title)}</a>`).join(' · ')}</p>` : '') +
            `<p class="sub"><a href="#stocks/${encodeURIComponent(c.t)}/thesis">Open ${esc(c.t)} on Stocks →</a></p></details>`; }).join('')) +
        (arr(Q.not_covered).length ? `<p class="sub">Not covered by Canary: ${arr(Q.not_covered).map(x => esc(x.t)).join(', ')}</p>` : '') + `</section>`;
      // ---- insiders ----
      const ic = arr(I.companies);
      let rows = ic.filter(c => (!st.sec || c.sector === st.sec) && (!st.iq || (c.t + ' ' + (c.name || '') + ' ' + (c.read || '')).toLowerCase().includes(st.iq.toLowerCase())));
      const key = st.isort; rows = rows.slice().sort((a, b) => key === 'buys' ? ((b.buys_6m || {}).value_usd || 0) - ((a.buys_6m || {}).value_usd || 0) : key === 'sells' ? ((b.sells_6m || {}).value_usd || 0) - ((a.sells_6m || {}).value_usd || 0) : key === 'b30' ? ((b.buys_30d || {}).value_usd || 0) - ((a.buys_30d || {}).value_usd || 0) : key === 't' ? String(a.t).localeCompare(b.t) : (b.net_6m_usd || 0) - (a.net_6m_usd || 0));
      const txT = (xs, title, cls) => `<div><h3 class="${cls}">${title}</h3><div class="tbl-wrap"><table class="dt"><thead><tr><th>Company</th><th>Date</th><th>Insider</th><th class="n">Value</th><th class="n">Price</th><th>Plan</th></tr></thead><tbody>${arr(xs).map(x => `<tr><td>${tk(x.t)}</td><td class="nowrap">${esc(x.date || '')}</td><td>${esc(x.insider || '')}<div class="sub">${esc(x.title || '')}</div></td><td class="n">${money(x.value_usd)}</td><td class="n">${x.price != null ? esc(x.price) : '–'}</td><td>${x.plan_10b5_1 ? '10b5-1' : '<b>open</b>'}</td></tr>`).join('') || `<tr><td colspan="6">${none('None.')}</td></tr>`}</tbody></table></div></div>`;
      h += `<section class="panel" id="mg-insiders"><div class="panel-h"><h2>Insider transactions</h2><span class="sub">${esc(arr(I.sources).join(' · '))}${I.window ? ' · ' + esc(fmtD(I.window.start)) + ' to ' + esc(fmtD(I.window.end)) : ''}</span></div>` +
        (!ic.length ? none('No insider data loaded yet.') :
        (arr(I.summary).length ? `<ul class="b">${arr(I.summary).map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : '') +
        `<div class="grid2">${txT(I.top_buys, 'Largest buys', 'c-pos')}${txT(I.top_sells, 'Largest sells', 'c-neg')}</div>` +
        `<div class="ctl"><label for="mg-iq">Search <input type="search" id="mg-iq" value="${esc(st.iq)}" placeholder="Ticker or word"></label>` +
        `<label for="mg-is">Sort <select id="mg-is">${[['net', 'Net $ (6M)'], ['buys', 'Buys $ (6M)'], ['b30', 'Buys $ (30D)'], ['sells', 'Sells $ (6M)'], ['t', 'Ticker']].map(([v, l]) => `<option value="${v}"${key === v ? ' selected' : ''}>${l}</option>`).join('')}</select></label><span class="count">${rows.length} companies</span></div>` +
        `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Company</th><th class="n">Buys 6M</th><th class="n">Sells 6M</th><th class="n">Net 6M</th><th class="n">Buys 30D</th><th class="n">Sells 30D</th><th class="n">Buyers</th><th class="n">Plan sells</th><th>Read</th></tr></thead><tbody>${rows.map(c => `<tr><td>${tk(c.t)}<div class="sub">${esc(c.sector || '')}</div></td><td class="n c-pos">${(c.buys_6m || {}).n || 0} · ${money((c.buys_6m || {}).value_usd)}</td><td class="n c-neg">${(c.sells_6m || {}).n || 0} · ${money((c.sells_6m || {}).value_usd)}</td><td class="n ${(c.net_6m_usd || 0) >= 0 ? 'c-pos' : 'c-neg'}"><b>${money(c.net_6m_usd)}</b></td><td class="n">${money((c.buys_30d || {}).value_usd)}</td><td class="n">${money((c.sells_30d || {}).value_usd)}</td><td class="n">${c.buyers_6m != null ? esc(c.buyers_6m) : '–'}</td><td class="n">${c.plan_sell_pct != null ? Math.round(c.plan_sell_pct) + '%' : '–'}</td><td class="ev-wrap">${esc(c.read || '')}${arr(c.notable).length ? `<details><summary>Notable</summary><ul class="b">${arr(c.notable).map(x => `<li>${esc(x.date || '')} · ${esc(x.insider || '')} (${esc(x.title || '')}) ${/buy/i.test(x.buy_sell || x.type || '') ? 'bought' : 'sold'} ${money(x.value_usd)}${x.price != null ? ' at ' + esc(x.price) : ''}${x.plan_10b5_1 ? ' · 10b5-1' : ''}</li>`).join('')}</ul></details>` : ''}</td></tr>`).join('')}</tbody></table></div>` +
        (arr(I.not_covered).length ? `<p class="sub">No insider data: ${arr(I.not_covered).map(x => esc(x.t)).join(', ')}</p>` : '')) + `</section>`;
      // ---- canary ----
      h += `<section class="panel" id="mg-canary"><div class="panel-h"><h2>Canary data sets and super analysts</h2>${M.canary_asof ? `<span class="sub">${esc(fmtD(M.canary_asof))}</span>` : ''}</div>${M.canary_md ? `<div class="fr-html">${xHtml(xParse(M.canary_md))}</div>` : none('The Canary survey is not loaded yet.')}</section>`;
      host.innerHTML = h; wire(); dedupeNames(host);
      host.querySelectorAll('.sk-tabs a').forEach(a => a.toggleAttribute('aria-current', a.getAttribute('href') === '#mgmt/' + sub));
      if (sub) { const el = document.getElementById('mg-' + sub); if (el) setTimeout(() => el.scrollIntoView({ block: 'start' }), 0); }
    };
    function wire() {
      const $ = id => document.getElementById(id);
      $('mg-co') && $('mg-co').addEventListener('change', e => { st.co = e.target.value; paint(); });
      $('mg-sec') && $('mg-sec').addEventListener('change', e => { st.sec = e.target.value; paint(); });
      $('mg-is') && $('mg-is').addEventListener('change', e => { st.isort = e.target.value; paint(); });
      const live = (id, k) => $(id) && $(id).addEventListener('input', e => { st[k] = e.target.value; const p = e.target.selectionStart; paint(); const n = $(id); n.focus(); n.setSelectionRange(p, p); });
      live('mg-q', 'q'); live('mg-iq', 'iq');
    }
    paint();
  }

  
  /* twitter-digest tab v2 */
  const TW = { list: [], ready: false, err: '' };
  if (window.claude && typeof window.claude.use === 'function') {
    window.claude.use('db').then(db => {
      if (!db) { TW.err = 'Twitter runs need the page open on claude.ai.'; return; }
      db.collection('twitter_runs').onSnapshot(snap => {
        TW.list = snap.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => String(b.id).localeCompare(String(a.id)));
        TW.ready = true; if ((location.hash || '').startsWith('#x')) renderX(false);
      }, err => { TW.err = 'Could not load digest runs: ' + ((err && err.code) || 'error'); if ((location.hash || '').startsWith('#x')) renderX(false); });
    }).catch(() => { TW.err = 'Twitter runs are not available in this view.'; });
  } else TW.err = 'Twitter runs need the page open on claude.ai.';
  const twDot = i => ({ very_positive: '🟢🟢', positive: '🟢', mixed: '🔵', negative: '🔴', very_negative: '🔴🔴' })[i] || '';
  const twLinks = xs => (xs || []).filter(Boolean).map(u => { const h = (String(u).match(/x\.com\/([^/]+)/) || [])[1];
    const lb = h ? '@' + h : /notion\.(so|com)/.test(String(u)) ? 'Notion page' : 'source';
    return `<a class="ext" href="${esc(u)}" target="_blank" rel="noopener">${esc(lb)}</a>`; }).join(' ');
  const twTk = (t, imp) => t ? `<span class="tk-chip ${/positive/.test(imp || '') ? 'up' : /negative/.test(imp || '') ? 'dn' : ''}">${esc(t)}</span>` : '';
  const twBold = s => esc(s || '').replace(/\*\*(.+?)\*\*/g, '<b class="n">$1</b>');
  const twLine = x => `<div class="li"><div class="body">${twDot(x.impact)} ${twTk(x.tk, x.impact)} ${twBold(x.text)} ${twLinks(x.urls)}</div><div class="side">${esc(x.date || '')}</div></div>`;
  function twRun(r, open) {
    const c = r.callouts || {}, h = r.hot_topic;
    const sec = (title, inner) => inner ? `<section class="panel tw-sec"><h3>${title}</h3>${inner}</section>` : '';
    const list = xs => (xs && xs.length) ? `<div class="list">${xs.map(twLine).join('')}</div>` : '';
    const hot = h ? `<section class="panel tw-hot"><span class="eyebrow">🔥 Hot topic</span><h2>${twBold(h.title)}</h2>
      <p class="lede">${twBold(h.what)}</p>
      <div class="tw-sides"><div><b>Bull:</b> ${twBold(h.bull)}</div><div><b>Bear:</b> ${twBold(h.bear)}</div></div>
      <div>${(h.tickers || []).map(t => twTk(t.tk, t.impact)).join(' ')} <span class="muted">· why now: ${esc(h.why_now || '')} · ${esc(String(h.accounts ?? ''))} accounts${h.accounts_delta != null ? ` (${h.accounts_delta >= 0 ? '+' : ''}${esc(String(h.accounts_delta))} vs last run)` : ''}</span></div>
      <div>${twLinks(h.urls)}</div></section>` : '';
    const callouts = [c.biggest ? `<div class="eyebrow">🎯 Biggest datapoint</div>${list([c.biggest])}` : '',
      c.positive && c.positive.length ? `<div class="eyebrow">🟢 Most positive</div>${list(c.positive)}` : '',
      c.negative && c.negative.length ? `<div class="eyebrow">🔴 Most negative</div>${list(c.negative)}` : '',
      c.inflections && c.inflections.length ? `<div class="eyebrow">🔄 Inflections</div>${list(c.inflections)}` : ''].join('');
    const changing = (r.changing || []).map(x => `<div class="li"><div class="body">${twTk(x.tk, x.impact)} <b>${esc(x.what || '')}</b>: ${twBold(x.was)} → ${twBold(x.now)} ${twLinks(x.urls)}</div><div class="side">${esc(x.date || '')}</div></div>`).join('');
    const chat = r.chatter || [];
    const dl = d => d == null ? '<span class="muted">new</span>' : `<span class="tw-delta ${d > 0 ? 'up' : d < 0 ? 'dn' : ''}">${d > 0 ? '+' : ''}${d}</span>`;
    const chatT = chat.length ? `<div class="tbl-wrap"><table><thead><tr><th>Ticker / topic</th><th class="n">Mentions</th><th class="n">Accounts</th><th class="n">Δ vs last</th><th>Gist</th></tr></thead><tbody>${chat.map(x =>
      `<tr><td>${x.kind === 'ticker' ? twTk(x.key) : esc(x.key)}</td><td class="n">${esc(String(x.mentions))}</td><td class="n">${esc(String(x.accounts))}</td><td class="n">${dl(x.delta)}</td><td>${esc(x.gist || '')}</td></tr>`).join('')}</tbody></table></div>` : '';
    const themes = (r.themes || []).map(t => `<details ${open ? 'open' : ''}><summary>${esc(t.title)}</summary>
      <ul class="b"><li><b>Changing:</b> ${twBold(t.changing)}</li><li><b>Benefits:</b> ${twBold(t.benefits)}</li><li><b>Loses:</b> ${twBold(t.loses)}</li>
      <li><b>Evidence:</b> ${twBold(t.evidence)} ${twLinks(t.urls)}</li><li><b>Wrong if:</b> ${twBold(t.wrong_if)}</li></ul></details>`).join('');
    const dps = r.datapoints || [], byTk = {};
    dps.forEach(d => (byTk[d.tk || '—'] = byTk[d.tk || '—'] || []).push(d));
    const dpH = Object.keys(byTk).sort().map(t => `<details><summary>${esc(t)} · ${byTk[t].length}</summary><div class="list">${byTk[t].map(d =>
      `<div class="li"><div class="body">${twDot(d.impact)} <span class="chip">${esc(d.field_key || '')}</span> <span class="chip out">${esc(d.confidence || '')}</span> ${twBold(d.text)}<br><span class="muted">${esc(d.primary_source || '')} via ${twLinks(d.urls)}</span></div>
       <div class="side">${esc(d.date || '')}<br><span class="tw-sb">${d.sb ? 'SB #' + esc(String(d.sb)) : d.held ? 'Held: ' + esc(d.held) : 'staged'}</span></div></div>`).join('')}</div></details>`).join('');
    const sb = r.supabase || {}, inp = r.inputs || {};
    const inputs = `<details><summary>📥 Inputs</summary><ul class="b">
      ${(inp.pages || []).map(p => `<li><a class="ext" href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a> · ${esc(String(p.posts_read ?? '?'))} read · ${esc(String(p.kept ?? '?'))} kept${p.archived ? ' · archived' : ''}</li>`).join('')}
      ${(inp.skipped || []).map(p => `<li class="muted">Skipped: ${esc(p.title)} (${esc(p.reason || '')})</li>`).join('')}
      ${(inp.notes || []).map(n => `<li>${esc(n)}</li>`).join('')}
      <li>📤 Supabase: ${esc(String(sb.loaded ?? 0))} loaded${sb.ids ? ' (' + esc(sb.ids) + ')' : ''} · ${esc(String(sb.held ?? 0))} held · ${esc(String(sb.dups ?? 0))} duplicates · ${esc(String(sb.failed ?? 0))} failed</li>
      </ul><p class="muted">${esc(r.footer || '')}</p></details>`;
    return `<div class="tw-runs">${hot}
      ${sec('📢 Callouts', callouts)}${sec('🔄 What\'s changing', changing ? `<div class="list">${changing}</div>` : '')}
      ${sec('📈 Most talked about <span class="muted" style="font-size:12px;font-weight:400">mentions in the Grok pages this run, not all of X</span>', chatT)}
      ${sec('🧵 Key themes', themes)}${sec('📊 Datapoints <span class="muted" style="font-size:12px;font-weight:400">' + dps.length + ' kept</span>', dpH)}
      <section class="panel">${inputs}</section></div>`;
  }
  function twDigest() {
    const hd = `<div class="vh"><div class="row"><h2>🧵 Twitter digest</h2><span class="src">twitter-digest skill · filtered datapoints, what changed vs the last run, mention leaderboard</span></div></div>`;
    if (!TW.ready) return hd + `<section class="panel"><p class="sub">${esc(TW.err || 'Loading digest runs…')}</p></section>`;
    if (!TW.list.length) return hd + '<section class="panel"><p class="sub">No digest runs yet. Say "run twitter" to Claude.</p></section>';
    const [cur, ...old] = TW.list;
    const lbl = r => `${esc(String(r.id).replace(/T(\d\d)(\d\d)$/, ' $1:$2'))} ET · ${esc((r.window && r.window.start) || '')} → ${esc((r.window && r.window.end) || '')}`;
    return hd.replace('</span></div></div>', ` · latest ${lbl(cur)}</span></div></div>`) + twRun(cur, true)
      + (old.length ? `<section class="panel"><h3>Earlier digest runs</h3>${old.slice(0, 14).map(r => `<details class="tw-old"><summary>${lbl(r)}${r.hot_topic ? ' · 🔥 ' + esc(r.hot_topic.title) : ''}</summary>${twRun(r, false)}</details>`).join('')}</section>` : '')
      + `<div class="vh"><div class="row"><h2>📡 Raw run</h2><span class="src">the Grok page as written, read live from Notion</span></div></div>`;
  }


  /* mgmt-callouts v1 */
  // Callouts for the Management & insiders tab: rank what matters out of ~100 companies' insider trades and
  // the Canary question lists, so the top of the tab says what to look at first.
  function mgCallouts(M, I, Q) {
    const DAY = 864e5, now = Date.now();
    const days = d => (now - new Date(d + 'T12:00:00').getTime()) / DAY;
    const csuite = s => /\b(CEO|CFO|COO|CTO|Chief|Chair(man|woman)?|President|Founder)\b/i.test(s || '');
    const sponsor = s => /sponsor|major holder|10% owner|beneficial owner/i.test(s || '');
    const isBuy = x => /buy|purchase/i.test(x.buy_sell || x.type || '');
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const cos = arr(I.companies);
    const trades = [];
    cos.forEach(c => arr(c.notable).forEach(x => { if (x.date) trades.push({ ...x, t: x.t || c.t, name: x.name || c.name, tier: c.tier, co: c }); }));
    // caveated rows (e.g. possible off-market transfers) never lead; they go to "verify"
    const seenV = new Set(), verify = trades.concat(arr(I.top_buys), arr(I.top_sells)).filter(x => x.caveat && !seenV.has(x.t + x.insider + x.date) && seenV.add(x.t + x.insider + x.date));
    const clean = trades.filter(x => !x.caveat);
    const score = x => (x.value_usd || 0) * (csuite(x.title) ? 3 : 1) * (x.plan_10b5_1 === false ? 1.5 : 1) * (x.tier === 1 ? 1.5 : 1);
    const buys30 = clean.filter(x => isBuy(x) && days(x.date) <= 30).sort((a, b) => score(b) - score(a));
    const sells30 = clean.filter(x => !isBuy(x) && days(x.date) <= 30 && x.plan_10b5_1 !== true && !sponsor(x.title) && csuite(x.title)).sort((a, b) => score(b) - score(a));
    // a buy below the same insider's earlier buy price = adding on weakness
    const lowerAdd = x => clean.some(y => y !== x && isBuy(y) && y.insider === x.insider && y.t === x.t && y.date < x.date && y.price && x.price && x.price < y.price * 0.9);
    const tag = x => [csuite(x.title) ? 'C-suite' : (x.title || 'insider'), x.plan_10b5_1 === false ? 'open-market' : x.plan_10b5_1 === true ? '10b5-1 plan' : '', lowerAdd(x) ? 'adding lower' : '', (x.co && x.co.buyers_6m >= 2) ? x.co.buyers_6m + ' buyers in 6M' : ''].filter(Boolean).join(' · ');
    const line = (dot, x) => `<li>${dot} ${tk(x.t)} <b>${esc(x.insider || '')}</b> ${isBuy(x) ? 'bought' : 'sold'} <b>${m$(x.value_usd)}</b>${x.price ? ' at ' + esc(x.price) : ''} <span class="sub">${esc(fmtD(x.date))} · ${esc(tag(x))}</span></li>`;
    // inflections: 30-day buying against 6-month net selling, and clusters
    const turning = cos.filter(c => (c.buys_30d || {}).value_usd > 0 && (c.net_6m_usd || 0) < 0 && !arr(c.notable).some(x => x.caveat));
    const clusters = cos.filter(c => (c.buyers_6m || 0) >= 2 && !turning.includes(c) && !arr(c.notable).some(x => x.caveat) && !arr(I.top_buys).some(x => x.caveat && x.t === c.t)).sort((a, b) => (b.buyers_6m - a.buyers_6m) || ((b.buys_6m || {}).value_usd - (a.buys_6m || {}).value_usd));
    // ask this week: covered names reporting in the next 10 days, with their first Canary question
    const qcos = arr(Q && Q.companies), up = arr((D.prep || {}).upcoming).filter(u => { const d = -days(u.date); return d >= -0.5 && d <= 10 && (u.tier || 9) <= 2; }).sort((a, b) => a.date.localeCompare(b.date));
    const key = t => String(t || '').toUpperCase().split(' ')[0];
    const ask = up.map(u => { const c = qcos.find(q => key(q.t) === key(u.ticker)); const q0 = c && arr(c.questions)[0]; return q0 ? { u, q: q0 } : null; }).filter(Boolean).slice(0, 6);
    const top = buys30.find(x => csuite(x.title)) || buys30[0];
    const sec = (title, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${title}</div><ul class="b">${items.join('')}</ul></div>` : '';
    const body = [
      top ? `<p class="mg-co-top">🎯 <b>Biggest signal:</b> ${tk(top.t)} ${esc(top.name || '')}: <b>${esc(top.insider || '')}</b> (${esc(top.title || 'insider')}) bought <b>${m$(top.value_usd)}</b>${top.price ? ' at ' + esc(top.price) : ''} on ${esc(fmtD(top.date))}${lowerAdd(top) ? ', adding below an earlier buy' : ''}.</p>` : '',
      sec('🟢 Insider buying, last 30 days', buys30.filter(x => x !== top).slice(0, 5).map(x => line('🟢', x))),
      sec('🔴 Discretionary C-suite selling, last 30 days', sells30.slice(0, 5).map(x => line('🔴', x))),
      sec('🔄 Inflections', turning.slice(0, 3).map(c => `<li>🔄 ${tk(c.t)} insiders buying in the last 30 days (<b>${m$((c.buys_30d || {}).value_usd)}</b>) after net selling of <b>${m$(c.net_6m_usd)}</b> over 6 months</li>`)
        .concat(clusters.slice(0, 3).map(c => `<li>👥 ${tk(c.t)} cluster: <b>${c.buyers_6m}</b> insiders bought <b>${m$((c.buys_6m || {}).value_usd)}</b> in 6 months</li>`))),
      sec('❓ Ask this week (reporting in the next 10 days)', ask.map(a => `<li>${tk(a.u.ticker)} <span class="sub">${esc(fmtD(a.u.date))}${a.u.time ? ' ' + esc(a.u.time) : ''} · ${esc(a.q.theme || '')}</span><br>${esc(String(a.q.q || '').slice(0, 260))}${String(a.q.q || '').length > 260 ? '…' : ''}</li>`)),
      sec('⚠️ Verify before acting', verify.slice(0, 3).map(x => `<li>${tk(x.t)} ${esc(x.insider || '')} ${m$(x.value_usd)} on ${esc(fmtD(x.date))}: ${esc(x.caveat)}</li>`))
    ].join('');
    const body2 = body + insSignals();
    if (!body2) return '';
    return `<section class="panel mg-callouts"><div class="panel-h"><h2>📢 Callouts</h2><span class="sub">ranked from ${cos.length} companies' insider trades${I.as_of ? ' as of ' + esc(fmtD(I.as_of)) : ''}${qcos.length ? ' and ' + qcos.length + ' Canary question sets' : ''}</span></div>${body2}</section>`;
  }


  /* insider-signals v1 */
  // Universe-wide insider signals from the page database (insider_signals/latest), refreshed by the
  // "Insider signals" scheduled task: 10b5-1 step-outs, cessation of selling, option skimming, plan changes.
  const INS = { doc: null, err: '' };
  if (window.claude && typeof window.claude.use === 'function') {
    window.claude.use('db').then(db => { if (!db) return;
      db.collection('insider_signals').doc('latest').onSnapshot(s => { INS.doc = s && s.exists ? s.data() : null; if ((location.hash || '').startsWith('#mgmt')) renderMgmt(); },
        e => { INS.err = (e && e.code) || 'error'; });
    }).catch(() => {});
  }
  function insSignals() {
    const S = INS.doc; if (!S) return `<p class="sub">Universe-wide insider signals (10b5-1 step-outs, cessation of selling, option skimming) load from the Insider signals task${INS.err ? ': ' + esc(INS.err) : '…'}</p>`;
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const who = x => `<b>${esc(x.insider || '')}</b>${x.title ? ` <span class="sub">(${esc(x.title)})</span>` : ''}`;
    const lk = x => x.link ? ` <a class="ext" href="${esc(x.link)}" target="_blank" rel="noopener">filing</a>` : '';
    const sec = (title, note, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${title}</div>${note ? `<p class="sub" style="margin:2px 0 4px">${note}</p>` : ''}<ul class="b">${items.join('')}</ul></div>` : '';
    const steps = arr(S.step_outs).slice(0, 8).map(x => `<li>🚪 ${tk(x.t)} ${who(x)} sold <b>${m$(x.value_usd)}</b> outside a 10b5-1 plan on ${esc(fmtD(x.date))}${x.prior_plan_sales_12m ? ` after <b>${esc(x.prior_plan_sales_12m)}</b> plan sales in 12 months` : ''}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}${lk(x)}</li>`);
    const stops = arr(S.cessations).slice(0, 8).map(x => `<li>⏸️ ${tk(x.t)} ${who(x)} has not sold for <b>${esc(x.days_since)} days</b> after <b>${esc(x.sells_prior)}</b> sales (${m$(x.value_prior_usd)}) over the prior 9 months${x.plan_note ? ` <span class="sub">· ${esc(x.plan_note)}</span>` : ''}</li>`);
    const skim = arr(S.skimming).slice(0, 8).map(x => `<li>${x.kind === 'exercise_hold' ? '🟢' : '🔻'} ${tk(x.t)} ${who(x)} ${x.kind === 'exercise_hold' ? 'exercised and <b>kept</b>' : 'exercised and sold'} ${x.shares != null ? Number(x.shares).toLocaleString() + ' sh' : ''} (<b>${m$(x.value_usd)}</b>) on ${esc(fmtD(x.date))}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}${lk(x)}</li>`);
    const plans = arr(S.plan_changes).slice(0, 8).map(x => `<li>📝 ${tk(x.t)} ${who(x)} ${esc(x.kind === 'terminated' ? 'terminated a 10b5-1 plan' : x.kind === 'modified' ? 'modified a 10b5-1 plan' : 'adopted a new 10b5-1 plan')}${x.date ? ' · ' + esc(fmtD(x.date)) : ''}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}</li>`);
    const buys = arr(S.universe_buys).slice(0, 6).map(x => `<li>🟢 ${tk(x.t)} ${who(x)} bought <b>${m$(x.value_usd)}</b> on ${esc(fmtD(x.date))}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}</li>`);
    const cov = S.coverage || {};
    return `<div class="mg-co-sec"><div class="eyebrow" style="color:var(--ink)">Across your universe${cov.us != null ? ` · ${esc(cov.us)} US-listed names (Insider Score)${cov.non_us_covered != null ? ` + ${esc(cov.non_us_covered)} of ${esc(cov.non_us)} non-US (Canary)` : ''}` : ''}${S.as_of ? ' · as of ' + esc(fmtD(S.as_of)) : ''}</div></div>` +
      sec('🚪 Stepping out of 10b5-1 plans', 'Insiders who sell on a pre-set plan and then sell outside it: a discretionary choice, so it says more than plan sales.', steps) +
      sec('⏸️ Cessation of selling', 'Regular sellers who have stopped. Often read as insiders seeing more upside (or a blackout before news).', stops) +
      sec('🔻 Option skimming', 'Options exercised and the shares sold at once, often for a small gain or well before expiry. Exercise-and-hold (🟢) is the bullish version.', skim) +
      sec('📝 10b5-1 plan changes', '', plans) +
      sec('🟢 Open-market buying beyond Tier 1–2', '', buys) + canaryWide(S);
  }


  /* kpi-tab v1 */
  // Stocks › KPIs & guidance. Source of record: Supabase kpi_profiles / company_kpis / guidance_history;
  // the backfill task mirrors each company into page-database doc kpi_profiles/<id> so this tab reads it live.
  const KP = { db: null, ready: null, cache: new Map() };
  KP.ready = (window.claude && typeof window.claude.use === 'function') ? window.claude.use('db').then(d => { KP.db = d; }).catch(() => {}) : Promise.resolve();
  const WHERE_L = { press_release: 'Release', deck: 'Deck', call: 'Call', '10q': '10-Q', '10k': '10-K', investor_day: 'Investor day', shareholder_letter: 'Letter', '8k': '8-K', conference: 'Conference' };
  function stockKpiView(cur, el) {
    const id = qrId(cur.t);
    el.innerHTML = `<section class="panel"><p class="sub">Loading KPIs and guidance…</p></section>`;
    const paint = doc => {
      if (!document.body.contains(el)) return;
      if (!doc) { el.innerHTML = `<section class="panel"><h2>KPIs &amp; guidance</h2>${none('Not built yet for ' + esc(cur.t) + '. The nightly KPI & guidance backfill adds companies Tier 1 first.')}</section>`; return; }
      const P = doc.profile || {}, K = arr(doc.kpis), G = arr(doc.guidance);
      const wh = w => `<span class="kp-where">${arr(w).map(x => `<span class="chip">${esc(WHERE_L[x] || x)}</span>`).join('')}</span>`;
      const seg = arr(P.segmentation).map(s => `<div><b>${esc(s.basis || 'Segments')}</b>: ${arr(s.segments).map(esc).join(' · ')} <span class="sub">· ${wh(s.where)} · ${esc(s.frequency || '')}${s.since ? ' · since ' + esc(s.since) : ''}${s.note ? ' · ' + esc(s.note) : ''}</span></div>`).join('');
      const cats = [...new Set(K.map(k => k.category || 'other'))];
      const kt = K.length ? `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Metric</th><th>Unit</th><th>Where disclosed</th><th>How often</th><th>Reported</th><th>Note</th></tr></thead><tbody>${cats.map(c => `<tr class="kp-h"><td colspan="6">${esc(c)}</td></tr>` + K.filter(k => (k.category || 'other') === c).map(k => `<tr><td class="wrap">${esc(k.metric)}${k.definition ? `<div class="sub">${esc(k.definition)}</div>` : ''}</td><td>${esc(k.unit || '')}</td><td>${wh(k.where_disclosed)}</td><td>${esc(k.frequency || '')}${k.status && k.status !== 'active' ? ` <span class="chip out">${esc(k.status)}</span>` : ''}</td><td class="nowrap">${esc(k.first_period || '')}${k.last_period ? ' → ' + esc(k.last_period) : ''}</td><td class="wrap">${esc(k.note || '')}${k.source_url ? ` <a class="ext" href="${esc(k.source_url)}" target="_blank" rel="noopener">source</a>` : ''}</td></tr>`).join('')).join('')}</tbody></table></div>` : none('No KPIs recorded.');
      // guidance: one row per metric + target period, one column per date the guide was given, read left to right
      const fmtV = g => g.value_text ? esc(g.value_text) : (g.low != null && g.high != null && g.low !== g.high ? `${esc(g.low)}–${esc(g.high)}` : esc(g.mid ?? g.low ?? g.high ?? '')) + (g.unit && !/^\$/.test(g.unit) ? ' ' + esc(g.unit) : '');
      const cls = c => /raised|up/i.test(c || '') ? 'up' : /lowered|cut|withdrawn/i.test(c || '') ? 'dn' : '';
      const hz = [['quarter', 'Quarterly guidance'], ['fiscal_year', 'Fiscal-year guidance'], ['long_term', 'Long-term targets (analyst days)']];
      const gt = hz.map(([h, label]) => {
        const rows = G.filter(g => g.horizon === h); if (!rows.length) return '';
        const dates = [...new Set(rows.map(g => g.given_on))].sort();
        const keys = [...new Set(rows.map(g => g.target_period + '||' + g.metric))].sort((a, b) => b.localeCompare(a));
        const evt = d => { const r = rows.find(g => g.given_on === d); return r && r.event ? r.event : ''; };
        return `<h3 style="margin-top:8px">${label}</h3><div class="tbl-wrap"><table class="dt kp-g"><thead><tr><th>Period · metric</th>${dates.map(d => `<th class="n" title="${esc(evt(d))}">${esc(d)}<div class="sub" style="text-transform:none;letter-spacing:0">${esc(evt(d)).slice(0, 28)}</div></th>`).join('')}</tr></thead><tbody>${keys.map(k => { const [tp, m] = k.split('||');
          return `<tr><td class="wrap"><b>${esc(tp)}</b> · ${esc(m)}</td>${dates.map(d => { const g = rows.find(x => x.given_on === d && x.target_period === tp && x.metric === m); return g ? `<td class="n ${cls(g.change)}" title="${esc([g.change, g.given_at, g.note].filter(Boolean).join(' · '))}">${fmtV(g)}${g.change && !/initial|reiterated/i.test(g.change) ? `<div class="sub">${esc(g.change)}</div>` : ''}</td>` : '<td class="n sub">·</td>'; }).join('')}</tr>`; }).join('')}</tbody></table></div>`;
      }).join('');
      el.innerHTML = `<section class="panel"><div class="panel-h"><h2>Revenue segmentation</h2><span class="sub">${P.fiscal_year_end ? 'FY ends ' + esc(P.fiscal_year_end) + ' · ' : ''}checked ${esc(fmtD(String(P.checked_at || '').slice(0, 10)))}</span></div>${P.summary ? `<p style="margin:0">${esc(P.summary)}</p>` : ''}<div class="kp-seg">${seg || none('No segmentation recorded.')}</div></section>` +
        `<section class="panel"><div class="panel-h"><h2>Reported KPIs</h2><span class="sub">${K.length} metrics · where and how often each is disclosed</span></div>${kt}</section>` +
        `<section class="panel"><div class="panel-h"><h2>Guidance</h2><span class="sub">each column is a date guidance was given; green raised, red lowered</span></div>${gt || none('No guidance recorded.')}</section>` +
        (arr(P.sources).length ? `<section class="panel"><details><summary>Sources</summary><ul class="b">${arr(P.sources).map(s => `<li>${s.url ? `<a class="ext" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.url)}</a>` : esc(s.title || '')}${s.date ? ' · ' + esc(fmtD(s.date)) : ''}</li>`).join('')}</ul></details></section>` : '');
    };
    if (KP.cache.has(id)) { paint(KP.cache.get(id)); return; }
    KP.ready.then(() => {
      if (!KP.db) { el.innerHTML = `<section class="panel">${none('KPIs and guidance need the page open on claude.ai.')}</section>`; return; }
      KP.db.collection('kpi_profiles').doc(id).get().then(s => { const d = s && s.exists ? s.data() : null; KP.cache.set(id, d); paint(d); })
        .catch(e => { el.innerHTML = `<section class="panel">${none('Could not load KPIs: ' + esc((e && e.code) || 'error'))}</section>`; });
    });
  }


  /* canary-wide v1 */
  // Canary insider flags across global Tech, Industrials and Materials names over $1bn market cap and
  // $70mm/day traded (not limited to the Companies DB). Written by the Insider signals task as S.canary_wide.
  function canaryWide(S) {
    const W = S && S.canary_wide; if (!W) return '';
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(0) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const FL = { insider_selling_large_sale: 'large sale', insider_selling_large_percent: 'large % of holding sold', insider_selling_acceleration: 'selling accelerating',
      insider_selling_commencement_buyer: 'prior buyer now selling', insider_buying: 'buying', skilled_buyer: 'skilled buyer', insider_selling_cluster: 'cluster selling', insider_buying_cluster: 'cluster buying' };
    const fl = f => esc(FL[f] || String(f || '').replace(/^insider_/, '').replace(/_/g, ' '));
    const sevDot = s => s === 'red' ? '🔴' : s === 'orange' ? '🟠' : s === 'yellow' ? '🟡' : '🟢';
    const row = x => `<li>${sevDot(x.severity)} <b>${esc(x.t || '')}</b> ${esc(x.name || '')} <span class="sub">${esc([x.country, x.sector].filter(Boolean).join(' · '))} · mcap ${m$(x.mcap_usd)} · ${m$(x.advt_usd)}/day</span> · ${arr(x.flags).map(f => `<span class="chip">${fl(f)}</span>`).join(' ')}${x.summary ? `<div class="sub" style="margin-left:22px">${esc(x.summary)}${x.latest_date ? ' · ' + esc(fmtD(x.latest_date)) : ''}</div>` : ''}</li>`;
    const sells = arr(W.sells).slice(0, 12).map(row), buys = arr(W.buys).slice(0, 10).map(row);
    const head = `<div class="mg-co-sec"><div class="eyebrow" style="color:var(--ink)">Canary · global Tech, Industrials &amp; Materials · &gt;$1bn mcap · &gt;$70mm/day traded${W.window ? ' · ' + esc(W.window) : ''}${W.as_of ? ' · as of ' + esc(fmtD(W.as_of)) : ''}</div>${W.coverage ? `<p class="sub" style="margin:2px 0 4px">${esc(W.coverage)}</p>` : ''}</div>`;
    const sec2 = (t, note, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${t}</div>${note ? `<p class="sub" style="margin:2px 0 4px">${note}</p>` : ''}<ul class="b">${items.join('')}</ul></div>` : '';
    return head + sec2('🔻 Insider selling flagged', 'Canary flags: large sales, large % of holding, accelerating selling, prior buyers turning sellers. Red and orange first.', sells) +
      sec2('🟢 Insider buying flagged', 'Canary buying and skilled-buyer flags.', buys) +
      (!sells.length && !buys.length ? '<p class="sub">No Canary insider flags in this universe for the window.</p>' : '');
  }

  // ================= DC PERMITS & FINANCING: research report kept in this page's database =================
  /* dc-risk report tab v1 */
  // The report lives in the page database (collection "dc_risk", doc "report"), not in the code, so page rebuilds leave it in place.
  // Doc shape: {title, lede, as_of, updated_at, doc_url, source, sections:[{id, nav, title, blocks:[...]}], charts:{<id>: {...}}}
  // Blocks: {t:'p'|'h3', md} | {t:'ul'|'ol', items:[md]} | {t:'table', head:[md], rows:[[md]], num:[bool]} | {t:'chart', id}
  // md keeps only **bold**, *italic* and [label](https://...) links; everything else is escaped.
  // Charts: {type:'waterfall', rows:[{l1, l2, kind:'start'|'delta'|'end', gw}], refs:[{name, gw}]} | {type:'timeline', ref_date, ref_label, rows:[{label, start, end, kind:'span'|'milestone', strong}]}
  const DCR = { doc: null, err: '', started: false, timer: 0, io: null };
  function dcrStart() {
    if (DCR.started) return; DCR.started = true;
    if (!(window.claude && typeof window.claude.use === 'function')) { DCR.err = 'The report is kept in this page’s database; open the page on claude.ai to see it.'; return; }
    const stop = msg => { clearTimeout(DCR.timer); if (msg) DCR.err = msg; dcrPaint(); };
    DCR.timer = setTimeout(() => { if (!DCR.doc && !DCR.err) { DCR.err = 'The report has not loaded yet; it will appear here when it does.'; dcrPaint(); } }, 10000);
    window.claude.use('db').then(db => {
      if (!db) { stop('The report is not available in this view.'); return; }
      db.collection('dc_risk').doc('report').onSnapshot(s => {
        DCR.doc = s && s.exists ? JSON.parse(JSON.stringify(s.data())) : null;
        DCR.err = DCR.doc ? '' : 'No report saved yet.'; stop();
      }, e => stop('The report could not load: ' + ((e && e.code) || 'error')));
    }).catch(() => stop('The report is not available in this view.'));
  }
  const dcrPaint = () => { if ((location.hash || '').startsWith('#dcrisk')) renderDcr(); };
  const dcrInline = s => esc(s).replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/(^|[^*\w])\*([^*\s][^*]*?)\*(?!\*)/g, '$1<i>$2</i>');
  const dcrMd = s => {
    const L = [];
    const t = String(s == null ? '' : s).replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (m, lab, url) => { L.push([lab, url]); return '\u0001' + (L.length - 1) + '\u0002'; });
    return dcrInline(t).replace(/\u0001(\d+)\u0002/g, (m, k) => `<a class="dcr-a" href="${esc(L[+k][1])}" target="_blank" rel="noopener">${dcrInline(L[+k][0])}</a>`);
  };
  const dcrN = v => (Math.round((+v || 0) * 10) / 10).toFixed(1);
  const dcrSigned = v => (v > 0 ? '+' : v < 0 ? '−' : '') + dcrN(Math.abs(v));
  const dcrMon = s => { const d = new Date(String(s || '').slice(0, 10) + 'T12:00:00Z'); return isNaN(d) ? esc(s) : d.toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' }); };
  // waterfall: a start total, signed steps, an end total; dashed reference lines (sell-side forecasts) across the end bar
  function dcrWaterfall(c) {
    let run = 0;
    const bars = arr(c.rows).map(r => {
      const v = +r.gw || 0;
      if (r.kind === 'start') { run = v; return { r, lo: 0, hi: run, v: run, cls: 'tot', total: true, lvl: run }; }
      if (r.kind === 'end') return { r, lo: 0, hi: run, v: run, cls: 'tot', total: true, lvl: run };
      const a = run; run += v; return { r, lo: Math.min(a, run), hi: Math.max(a, run), v, cls: v < 0 ? 'neg' : 'pos', lvl: run };
    });
    if (!bars.length) return '';
    const refs = arr(c.refs).filter(f => isFinite(+f.gw)).sort((a, b) => b.gw - a.gw), unit = esc(c.unit || '');
    const top = Math.ceil(Math.max(...bars.map(b => b.hi), ...refs.map(f => +f.gw)) / 10) * 10 || 10;
    const W = 760, H = 362, x0 = 46, x1 = refs.length ? 628 : 744, y0 = 26, y1 = 318;
    const band = (x1 - x0) / bars.length, bw = Math.min(54, band * 0.64);
    const Y = v => y1 - (v / top) * (y1 - y0), X = i => x0 + band * i + band / 2, f1 = n => n.toFixed(1);
    let g = '';
    for (let t = 0; t <= top + 1e-9; t += 10) g += `<line class="grid" x1="${x0}" x2="${x1}" y1="${f1(Y(t))}" y2="${f1(Y(t))}"/><text class="sm" x="${x0 - 8}" y="${f1(Y(t) + 3.5)}" text-anchor="end">${t}</text>`;
    g += `<text class="sm" x="${x0 - 8}" y="${y0 - 14}" text-anchor="end">${unit}</text>`;
    bars.forEach((b, i) => {
      const cx = X(i), xl = cx - bw / 2, lab = b.total ? dcrN(b.v) : dcrSigned(b.v);
      if (i < bars.length - 1) g += `<line class="cn" x1="${f1(xl + bw)}" x2="${f1(X(i + 1) - bw / 2)}" y1="${f1(Y(b.lvl))}" y2="${f1(Y(b.lvl))}"/>`;
      g += `<rect class="${b.cls}" x="${f1(xl)}" y="${f1(Y(b.hi))}" width="${f1(bw)}" height="${f1(Math.max(1, Y(b.lo) - Y(b.hi)))}" rx="2"><title>${esc([b.r.l1, b.r.l2].filter(Boolean).join(' '))}: ${lab} ${unit}</title></rect>`;
      g += `<text class="v" x="${f1(cx)}" y="${f1(b.cls === 'neg' ? Y(b.lo) + 15 : Y(b.hi) - 6)}" text-anchor="middle">${lab}</text>`;
      g += `<text class="lbl" x="${f1(cx)}" y="${y1 + 18}" text-anchor="middle">${esc(b.r.l1 || '')}</text><text class="sm" x="${f1(cx)}" y="${y1 + 33}" text-anchor="middle">${esc(b.r.l2 || '')}</text>`;
    });
    const xs = X(bars.length - 1) - bw / 2 - 8, xe = x1 + 6;
    refs.forEach((f, k) => { const y = Y(+f.gw); g += `<line class="ref" x1="${f1(xs)}" x2="${f1(xe)}" y1="${f1(y)}" y2="${f1(y)}"/><text class="s" x="${f1(xe + 4)}" y="${f1(k % 2 ? y + 13 : y - 5)}">${esc(f.name || '')} ${dcrN(f.gw)}</text>`; });
    g += `<line class="ax" x1="${x0}" x2="${x1}" y1="${y1}" y2="${y1}"/>`;
    return `<svg class="dcr-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(c.title || 'Waterfall chart')}">${g}</svg>`;
  }
  // timeline: one bar per step from its latest start to its finish; red when the latest start is before the reference date
  function dcrTimeline(c) {
    const rows = arr(c.rows); if (!rows.length) return '';
    const M = s => { const d = new Date(String(s || '').slice(0, 10) + 'T12:00:00Z'); return d.getUTCFullYear() * 12 + d.getUTCMonth() + (d.getUTCDate() - 1) / 30.5; };
    const lo = Math.floor(Math.min(...rows.map(r => M(r.start))) / 6) * 6, hi = Math.ceil((Math.max(...rows.map(r => M(r.end || r.start))) + 1) / 6) * 6;
    const W = 760, L = 252, R0 = 736, top = 34, rh = 26, H = top + rows.length * rh + 28, f1 = n => n.toFixed(1);
    const X = m => L + (m - lo) / Math.max(1, hi - lo) * (R0 - L), MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const ref = c.ref_date ? M(c.ref_date) : null, yb = top + rows.length * rh + 4;
    let g = '';
    for (let m = lo; m <= hi; m += 6) g += `<line class="grid" x1="${f1(X(m))}" x2="${f1(X(m))}" y1="${top - 4}" y2="${yb}"/><text class="sm" x="${f1(X(m))}" y="${yb + 16}" text-anchor="middle">${MON[m % 12]} ’${String(Math.floor(m / 12)).slice(2)}</text>`;
    rows.forEach((r, i) => {
      const y = top + i * rh + rh / 2, s = M(r.start), e = M(r.end || r.start), cls = r.strong ? 'key' : ref != null && s < ref ? 'early' : 'later';
      g += `<text class="${r.strong ? 't' : 'lbl'}" x="16" y="${f1(y + 4)}">${esc(r.label || '')}</text>`;
      if (r.kind === 'milestone' || e <= s) g += `<path class="${cls}" d="M${f1(X(s))} ${f1(y - 7)}l7 7-7 7-7-7z"><title>${esc(r.label || '')}: ${dcrMon(r.start)}</title></path>`;
      else g += `<rect class="${cls}" x="${f1(X(s))}" y="${f1(y - 6)}" width="${f1(X(e) - X(s))}" height="12" rx="2"><title>${esc(r.label || '')}: start by ${dcrMon(r.start)}, done ${dcrMon(r.end)}</title></rect>`;
    });
    if (ref != null) { const x = X(ref); g += `<line class="today" x1="${f1(x)}" x2="${f1(x)}" y1="${top - 10}" y2="${yb}"/><text class="acc" x="${f1(x + 5)}" y="${top - 14}">${esc(c.ref_label || 'Today')}</text>`; }
    return `<svg class="dcr-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(c.title || 'Timeline chart')}">${g}</svg>`;
  }
  function dcrChart(c) {
    if (!c) return '';
    const svg = c.type === 'waterfall' ? dcrWaterfall(c) : c.type === 'timeline' ? dcrTimeline(c) : ''; if (!svg) return '';
    const cap = [c.note, c.caption].filter(Boolean).join(' · ');
    return `<figure class="dcr-fig"><div class="dcr-fh"><b>${esc(c.title || '')}</b>${c.sub ? `<span class="sub">${esc(c.sub)}</span>` : ''}</div><div class="dcr-svgw">${svg}</div>${cap ? `<figcaption class="sub">${esc(cap)}</figcaption>` : ''}</figure>`;
  }
  function dcrBlock(b, C) {
    if (!b) return '';
    if (b.t === 'h3') return `<h3>${dcrMd(b.md)}</h3>`;
    if (b.t === 'p') return `<p>${dcrMd(b.md)}</p>`;
    if (b.t === 'ul' || b.t === 'ol') return `<${b.t} class="${b.t === 'ul' ? 'b' : 'dcr-ol'}">${arr(b.items).map(x => `<li>${dcrMd(x)}</li>`).join('')}</${b.t}>`;
    if (b.t === 'table') { const n = arr(b.num); return `<div class="tbl-wrap"><table class="dt dcr-t"><thead><tr>${arr(b.head).map((x, i) => `<th${n[i] ? ' class="n"' : ''}>${dcrMd(x)}</th>`).join('')}</tr></thead><tbody>${arr(b.rows).map(r => `<tr>${arr(r).map((x, i) => `<td${n[i] ? ' class="n"' : ''}>${dcrMd(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`; }
    if (b.t === 'chart') return dcrChart((C || {})[b.id]);
    return '';
  }
  function renderDcr() {
    const host = document.getElementById('v-dcrisk'); if (!host) return;
    dcrStart();
    const T = DCR.doc;
    if (DCR.io) { DCR.io.disconnect(); DCR.io = null; }
    const link = T && T.doc_url ? ` <a class="ext" href="${esc(T.doc_url)}" target="_blank" rel="noopener">Open the editable doc ↗</a>` : '';
    let h = head('Research report' + (T && T.as_of ? ' · as of ' + updFmt(T.as_of) : ''), T ? esc(T.title || 'Data center permits and financing') : 'Data center permits and financing', T ? esc(T.lede || '') + link : '');
    if (!T) { host.innerHTML = h + `<section class="panel">${none(esc(DCR.err || 'Loading the report…'))}</section>`; return; }
    const S = arr(T.sections);
    h += `<nav class="sk-tabs dcr-nav" aria-label="Report sections">${S.map(s => `<a href="#dcrisk" data-dcr="dcr-${esc(s.id)}">${esc(s.nav || s.title)}</a>`).join('')}</nav>`;
    h += S.map(s => `<section class="panel dcr-sec" id="dcr-${esc(s.id)}"><h2>${dcrMd(s.title)}</h2>${arr(s.blocks).map(b => dcrBlock(b, T.charts)).join('')}</section>`).join('');
    if (T.source) h += `<p class="sub">${esc(T.source)}${T.updated_at ? ' · added to this page ' + updFmt(T.updated_at) : ''}</p>`;
    host.innerHTML = h;
    const smooth = !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    const links = [...host.querySelectorAll('.dcr-nav a')], nav = host.querySelector('.dcr-nav');
    links.forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById(a.dataset.dcr); if (t) t.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' }); }));
    if ('IntersectionObserver' in window) {
      DCR.io = new IntersectionObserver(es => es.forEach(e => {
        if (!e.isIntersecting) return;
        links.forEach(a => { if (a.dataset.dcr === e.target.id) { a.setAttribute('aria-current', 'location'); if (nav && (a.offsetLeft < nav.scrollLeft || a.offsetLeft + a.offsetWidth > nav.scrollLeft + nav.clientWidth)) nav.scrollLeft = Math.max(0, a.offsetLeft - 16); } else a.removeAttribute('aria-current'); });
      }), { rootMargin: '-25% 0px -65% 0px' });
      host.querySelectorAll('.dcr-sec').forEach(s => DCR.io.observe(s));
    }
  }

  // ================= ROUTER =================
  const VIEWS = ['today', 'x', 'ai', 'thesis', 'dcrisk', 'mgmt', 'daily', 'routines', 'stocks', 'notes', 'earnings', 'datapoints', 'screens', 'ideas', 'prep', 'health', 'sources', 'method'];
  const R = { mgmt: renderMgmt, ai: () => {}, thesis: () => {}, dcrisk: renderDcr, x: () => renderX(false), daily: renderDaily, routines: renderRoutines, stocks: renderStocks, notes: renderNotes, sources: renderSources, today: renderToday, themes: renderThemes, datapoints: renderDatapoints, screens: renderScreens, ideas: renderIdeas, prep: renderPrep, health: renderHealth };
  // ---- top tabs: drag to reorder; order remembered per viewer ----
  (function navOrder() {
    const nav = document.querySelector('nav.tabs'); if (!nav) return;
    const links = () => [...nav.querySelectorAll('a')];
    try { const saved = JSON.parse(localStorage.getItem('td-nav') || 'null'); if (Array.isArray(saved)) saved.forEach(h => { const a = links().find(x => x.getAttribute('href') === h); if (a) nav.appendChild(a); }); } catch (e) {}
    const save = () => { try { localStorage.setItem('td-nav', JSON.stringify(links().map(a => a.getAttribute('href')))); } catch (e) {} };
    let drag = null;
    links().forEach(a => {
      a.draggable = true; a.title = 'Drag to reorder';
      a.addEventListener('dragstart', e => { drag = a; a.classList.add('dragging'); e.dataTransfer.effectAllowed = 'move'; try { e.dataTransfer.setData('text/plain', a.getAttribute('href')); } catch (x) {} });
      a.addEventListener('dragend', () => { if (drag) drag.classList.remove('dragging'); drag = null; links().forEach(x => x.classList.remove('drop-l', 'drop-r')); save(); });
      a.addEventListener('dragover', e => { if (!drag || drag === a) return; e.preventDefault(); const r = a.getBoundingClientRect(), after = e.clientX > r.left + r.width / 2; links().forEach(x => x.classList.remove('drop-l', 'drop-r')); a.classList.add(after ? 'drop-r' : 'drop-l'); });
      a.addEventListener('drop', e => { if (!drag || drag === a) return; e.preventDefault(); const r = a.getBoundingClientRect(); nav.insertBefore(drag, e.clientX > r.left + r.width / 2 ? a.nextSibling : a); });
    });
    const reset = document.createElement('button'); reset.type = 'button'; reset.className = 'nav-reset'; reset.textContent = '↺'; reset.title = 'Reset tab order';
    const DEF = links().map(a => a.getAttribute('href'));
    try { const d0 = JSON.parse(localStorage.getItem('td-nav-default') || 'null'); if (Array.isArray(d0)) DEF.splice(0, DEF.length, ...d0); } catch (e) {}
    reset.addEventListener('click', () => { try { localStorage.removeItem('td-nav'); } catch (e) {} location.reload(); });
    nav.after(reset);
  })();

  let done = {};
  const HIST = D.daily_history || {};
  const gN = document.getElementById('g-n'), gD = document.getElementById('g-d'), gA = document.getElementById('g-asof'), gAL = document.getElementById('g-asof-l');
  const histDates = Object.keys(HIST).sort().reverse();
  if (gA) gA.innerHTML = [DLY.as_of].concat(histDates.filter(d => d !== DLY.as_of)).filter(Boolean).map(d => `<option value="${esc(d)}">${fmtD(d)}</option>`).join('');
  if (gN) gN.value = G.n ? String(G.n) : ''; if (gD) gD.value = G.days ? String(G.days) : '';
  const saveG = () => { try { localStorage.setItem('td-view', JSON.stringify(G)); } catch (e) {} };
  const rerender = () => { done = {}; liveStarted = false; show(); if (window.__earnRender) window.__earnRender(); };
  if (gN) gN.addEventListener('change', () => { G.n = +gN.value || null; saveG(); rerender(); });
  if (gD) gD.addEventListener('change', () => { G.days = +gD.value || null; saveG(); rerender(); });
  if (gA) gA.addEventListener('change', () => { DLY = gA.value === (D.daily || {}).as_of ? (D.daily || {}) : (HIST[gA.value] || D.daily || {}); done.daily = 0; show(); });
  /* refresh-button v1 */
  const RF = { mcp: null, ok: null, open: false, run: null, msg: '', t: 0, firedAt: 0 };
  const RF_SRV = 'Claude Code Remote';
  const RF_MAIN = 'trig_016XHWMU5iFnTSewgLzdeERi';           // Bobby Tech Daily refresh (09:20 task, same prompt as the others)
  const RF_SWEEP = 'trig_01XawnybdQAxKeAxCqbgRxYQ';          // Anthropic Output Sweep
  const RF_SOURCES = [['trig_01Nbwu1ZNrQWtequVtj6Ccnc', 'Tech Specialist'], ['trig_01MrpFhDeY5rPBH8Gc9YNHhb', 'SemiAnalysis'], ['trig_01FWUbz2T5ku7cY2LwQvMDon', 'Research'], ['trig_01XxZpvJFfqadWNW1tnwhLnZ', 'Sell-side'], ['trig_01XsDkh8ViR8Fv4MZWKyhSsG', 'Twitter'], ['trig_01QzfSrsKryy6WTE2DjKYwUV', 'Earnings reviews']];
  const rfPayload = r => { let p = r && (r.payload !== undefined ? r.payload : r); if (typeof p === 'string') { try { p = JSON.parse(p); } catch (e) {} } return p; };
  const rfHM = s => { try { return new Date(s).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); } catch (e) { return ''; } };
  async function rfInit() {
    if (RF.ok !== null) return RF.ok;
    try {
      RF.mcp = await (window.claude && window.claude.use ? window.claude.use('mcp') : null);
      if (!RF.mcp) { RF.ok = false; RF.msg = 'Connectors are not available in this view.'; return false; }
      const L = await RF.mcp.listTools();
      const srv = (L && (L.servers || L)) || [];
      const s = (Array.isArray(srv) ? srv : []).find(x => (x.server || x.name) === RF_SRV);
      const names = s ? (s.tools || []).map(t => t.name || t) : [];
      RF.ok = !s || (names.includes('fire_trigger') && names.includes('list_triggers')) || !names.length;
      if (!RF.ok) RF.msg = 'Your Claude Code Remote connector does not offer the scheduled-task tools here.';
    } catch (e) { RF.ok = true; }   // listing unsupported: try the calls and handle their errors
    return RF.ok;
  }
  async function rfStatus() {
    let cur, n = 0, found = null;
    do {
      const r = rfPayload(await RF.mcp.callTool(RF_SRV, 'list_triggers', cur ? { limit: 100, cursor: cur } : { limit: 100 }, { cache: false }));
      found = (r && r.data || []).find(t => t.id === RF_MAIN) || found;
      cur = r && r.has_more && !found ? r.next_cursor : null;
    } while (cur && ++n < 6);
    RF.run = found ? (found.last_run || null) : null; RF.t = Date.now();
    return RF.run;
  }
  const rfRunning = () => RF.run && /PENDING|RUNNING|QUEUED|STARTED/i.test(String(RF.run.status || '')) && !RF.run.finished_at;
  function rfText(kind) {
    const now = new Date().toISOString(), v = (location.hash || '#today').slice(1).split('/')[0] || 'today';
    const a = document.querySelector(`nav.tabs a[href="#${v}"]`), label = a ? a.textContent.replace(/\s+\d+$/, '').trim() : v;
    const head = `ON-DEMAND REFRESH requested from the Tech Daily page at ${now} (Bobby pressed Update). Ignore the ET-hour SCHEDULE table for this run. `;
    const tail = ' Skip the history writes (tech_daily_snapshots, daily_moves) unless it is after 16:00 ET. Publish to the same artifact, then do the ARCHIVE STEP as usual. If another refresh run is already publishing, wait for it to finish first.';
    if (kind === 'tab') return head + `Rebuild ONLY the "${label}" tab (view "${v}") with the file's steps for it, from the latest sources; carry every other tab over from the live page (--keep-full <S>/live.html).` + tail;
    if (kind === 'all') return head + 'Rebuild every tab the file builds (the full EVENING tab set: Datapoints first, Routines and Today, Earnings, Stocks and revised theses, Daily moves from the intraday Live sheet if the market is open else closes, AI, and the WHEN-CHANGED tabs), publishing a checkpoint after Datapoints and Today.' + tail;
    return head + `FIRST WAIT FOR SOURCES: the page just fired these scheduled tasks at ${now}: ${RF_SOURCES.map(s => s[1] + ' ' + s[0]).join(', ')}. Using mcp__claude-code-remote__list_triggers, wait until each one's last_run (fired after ${now}) has finished (check every 2 minutes, at most 45 minutes; carry on without any that are still running then and name them in the summary). Then fire the Anthropic Output Sweep (${RF_SWEEP}) with mcp__claude-code-remote__fire_trigger and wait for it the same way (at most 20 minutes). If you cannot check run status, wait 35 minutes and continue. THEN rebuild every tab the file builds (the full EVENING tab set), publishing a checkpoint after Datapoints and Today.` + tail;
  }
  async function rfFire(kind) {
    RF.msg = 'Checking for a refresh already running…'; rfPaint();
    try {
      await rfStatus();
      if (rfRunning()) { RF.msg = `A refresh is already running (started ${rfHM(RF.run.fired_at)}). It will update the page when it finishes.`; rfPaint(); rfPoll(); return; }
      if (kind === 'sources') {
        const res = await Promise.allSettled(RF_SOURCES.map(([id]) => RF.mcp.callTool(RF_SRV, 'fire_trigger', { trigger_id: id }, { cache: false })));
        const bad = res.map((r, i) => r.status === 'rejected' ? RF_SOURCES[i][1] : null).filter(Boolean);
        if (bad.length === RF_SOURCES.length) throw res[0].reason;
        RF.msg = `Sources started${bad.length ? ` (could not start: ${bad.join(', ')})` : ''}. `;
      } else RF.msg = '';
      await RF.mcp.callTool(RF_SRV, 'fire_trigger', { trigger_id: RF_MAIN, text: rfText(kind) }, { cache: false });
      RF.firedAt = Date.now();
      RF.msg += kind === 'tab' ? 'Refreshing this tab now; usually 10–20 minutes.' : kind === 'all' ? 'Refreshing every tab now; usually 25–40 minutes.' : 'The refresh waits for the sources and the Output Sweep, then rebuilds every tab; usually 60–90 minutes.';
      RF.run = { status: 'PENDING', fired_at: new Date().toISOString() }; rfPaint(); rfPoll();
    } catch (e) {
      const c = e && e.code;
      RF.msg = c === 'not_granted' || c === 'consent_required' ? 'Allow the Claude Code Remote connector for this page to use Update (Permissions in the artifact menu).' : (c === 'server_not_connected' || c === 'server_not_found' || c === 'needs_reauth') ? 'Connect Claude Code Remote in claude.ai connectors to use Update.' : c === 'blocked_by_policy' ? 'Your organization does not allow pages to start scheduled tasks.' : `Could not start the refresh${e && e.message ? ': ' + e.message : ''}.`;
      rfPaint();
    }
    // live parts of the open tab re-fetch at once
    try { if (typeof show === 'function') show(); } catch (e) {}
  }
  function rfPoll() {
    clearTimeout(RF.timer);
    RF.timer = setTimeout(async () => {
      try { await rfStatus(); } catch (e) {}
      if (rfRunning() && Date.now() - (RF.firedAt || RF.t) < 2 * 3600e3) { rfPaint(); rfPoll(); return; }
      if (RF.run && RF.run.finished_at) RF.msg = `Last refresh ${/SUCC/i.test(RF.run.status) ? 'finished' : 'ended (' + String(RF.run.status).replace(/^ROUTINE_RUN_STATUS_/, '').toLowerCase() + ')'} at ${rfHM(RF.run.finished_at)}. Reload the page to see it.`;
      rfPaint();
    }, 60e3);
  }
  function rfPaint() {
    const box = document.getElementById('rf'); if (!box) return;
    const run = rfRunning(), mins = run && RF.run.fired_at ? Math.max(0, Math.round((Date.now() - new Date(RF.run.fired_at)) / 60e3)) : 0;
    box.innerHTML = `<button type="button" class="rf-btn${run ? ' on' : ''}" aria-expanded="${RF.open}" aria-haspopup="true">${run ? `Updating… ${mins} min` : '↻ Update'}</button>` +
      (RF.open ? `<div class="rf-pop" role="menu"><p class="rf-h">Update Tech Daily now</p>` +
        `<button type="button" role="menuitem" data-rf="tab"${run ? ' disabled' : ''}><b>Refresh this tab</b><span>Rebuild the open tab from the latest sources</span></button>` +
        `<button type="button" role="menuitem" data-rf="all"${run ? ' disabled' : ''}><b>Refresh all tabs</b><span>Full rebuild from what the routines have produced</span></button>` +
        `<button type="button" role="menuitem" data-rf="sources"${run ? ' disabled' : ''}><b>Run all sources, then refresh</b><span>Runs the digests, sell-side, Twitter and earnings reviews first</span></button>` +
        `<p class="rf-msg" aria-live="polite">${esc(RF.msg || (RF.run && RF.run.fired_at ? (run ? `Running since ${rfHM(RF.run.fired_at)}.` : RF.run.finished_at ? `Last refresh finished ${rfHM(RF.run.finished_at)}.` : '') : 'Scheduled refreshes run 09:20, 14:25 and 18:15 ET.'))}</p></div>` : '');
    box.querySelector('.rf-btn').onclick = async () => {
      RF.open = !RF.open; rfPaint();
      if (RF.open) { if (!(await rfInit())) { rfPaint(); return; } try { await rfStatus(); } catch (e) {} rfPaint(); if (rfRunning()) rfPoll(); }
    };
    box.querySelectorAll('[data-rf]').forEach(b => b.onclick = () => { if (RF.ok === false) return; rfFire(b.dataset.rf); });
  }
  document.addEventListener('click', e => { if (RF.open && e.target.isConnected && !e.target.closest('#rf')) { RF.open = false; rfPaint(); } });
  document.addEventListener('keydown', e => { if (RF.open && e.key === 'Escape') { RF.open = false; rfPaint(); } });
  setTimeout(rfPaint, 0);
  function show() {
    let v = (location.hash || '').slice(1).split('/')[0]; if (v === 'themes' || v === 'pipeline') v = 'ideas'; if (v === 'twitter') v = 'x'; if (v === 'thesis') { aiModeSet((location.hash.split('/')[1] || '') === 'tenets' ? 'tenets' : 'overview'); history.replaceState(null, '', '#ai'); v = 'ai'; } else if (v === 'ai' && (location.hash.split('/')[1] || '')) aiModeSet('data'); if (!VIEWS.includes(v)) v = 'today';
    if (gAL) gAL.hidden = !(v === 'daily' && gA && gA.options.length > 1);
    if (v === 'routines' && done[v]) { renderRoutines(); }
    if (v === 'stocks' && done[v]) { renderStocks(); }
    if (v === 'notes' && done[v]) { renderNotes(); }
    if (v === 'ai') { aiShow(); done.ai = 1; }
    if (v === 'mgmt' && done[v]) { renderMgmt(); }
    if (v === 'dcrisk' && done[v]) { renderDcr(); }
    if (R[v] && !done[v]) { try { R[v](); } catch (e) { document.getElementById('v-' + v).innerHTML = `<div class="nores">This tab could not render: ${esc(e.message)}</div>`; } done[v] = 1; }
    paintUpd(v);
    document.querySelectorAll('.view').forEach(el => el.classList.toggle('on', el.dataset.view === v));
    document.querySelectorAll('nav.tabs a').forEach(a => { if (a.getAttribute('href') === '#' + v) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
    window.scrollTo(0, 0);
  }
  const mast = document.querySelector('.mast');
  const setH = () => document.documentElement.style.setProperty('--mast-h', mast.offsetHeight + 'px');
  setH(); window.addEventListener('resize', setH);
  if (window.__earnRender) window.__earnRender();
  window.addEventListener('hashchange', show);
  show();
})();
