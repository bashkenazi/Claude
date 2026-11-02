(function () {
  const D = JSON.parse(document.getElementById('data').textContent);
  const SRC = D.sources || {};
  const SIG = D.signals || {};
  const CMP = D.comps || {}, DLY = D.daily || {};
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
  const tk = (t, cls) => t ? `<span class="tk-chip${cls ? ' ' + cls : ''}">${esc(t)}</span>` : '';
  const signOf = v => { const s = String(v == null ? '' : v).trim().toLowerCase(); if (/^\+|^pos|bull|up\b|beat|raise|improv|accel/.test(s)) return 1; if (/^[-−–]|^neg|bear|down\b|miss|cut|deteri|decel/.test(s)) return -1; return 0; };
  const numCls = v => { const g = signOf(v); return g > 0 ? 'up' : g < 0 ? 'dn' : ''; };
  const SKILL_NAME = {
    'morning': 'Morning', 'research-folder-digest': 'Research folder', 'tech-email-digest-new': 'Tech email', 'semianalysis-digest': 'SemiAnalysis',
    'analyst-folder-extractor': 'Analyst folders', 'alphasense-digest': 'AlphaSense', 'sellside-folder-digest': 'Sell-side PDFs',
    'consensus-revisions': 'Consensus revisions', 'comps-screen': 'Comps screen', 'idea-generator': 'Idea generator', 'thesis-builder': 'Thesis builder',
    'industry-cycle': 'Industry cycle', 'operating-comps': 'Operating comps', 'management-prep': 'Management prep', 'analyst-day': 'Analyst day',
    'print-tables': 'Print tables', 'quarterly-review': 'Quarterly review', 'earnings-preview': 'Earnings preview / review', 'earnings-recap': 'Earnings recap',
    'datapoint-filter': 'Supabase loads (Datapoint Filter)'
  };
  const sk = s => SKILL_NAME[s] || s;
  const fresh = a => a == null ? '' : a <= 2 ? 'fresh' : a <= 7 ? 'aging' : 'stale';
  const head = (eyebrow, title, lede) => `<section class="panel vh"><span class="eyebrow">${eyebrow}</span><h1>${title}</h1>${lede ? `<p class="lede">${lede}</p>` : ''}</section>`;
  const none = msg => `<p class="empty-panel">${msg}</p>`;
  const attr = t => esc(t).replace(/\s*\[([^\]]{2,90})\]\s*$/, ' <span class="attr">$1</span>');
  const srcList = x => arr(x && x.sources).concat(x && x.source ? [x.source] : []).filter(Boolean);
  const srcLine = (x, label) => { const l = srcList(x); return l.length ? `<div class="srcl"><span>${label || 'Source'}</span>${l.map(esc).join(' · ')}</div>` : ''; };
  window.__srcLine = srcLine; window.__attr = attr;

  // ================= TODAY =================
  function renderToday() {
    const digs = arr(TODAY.digests).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)));
    const latestBySkill = new Map();
    digs.forEach(d => { if (!latestBySkill.has(d.skill)) latestBySkill.set(d.skill, d); });
    const order = ['morning', 'research-folder-digest', 'tech-email-digest-new', 'semianalysis-digest', 'analyst-folder-extractor', 'alphasense-digest', 'sellside-folder-digest'];
    const strip = order.map(s => {
      const d = latestBySkill.get(s); const a = d ? ageDays(d.date) : null;
      return d ? `<a class="run" href="${esc(d.url)}" target="_blank" rel="noopener"><span class="n">${esc(sk(s))}</span><span class="d"><i class="dot ${fresh(a)}"></i>${fmtD(d.date)}${d.datapoint_count != null ? ' · ' + esc(d.datapoint_count) + ' datapoints' : ''}</span></a>`
        : `<div class="run"><span class="n">${esc(sk(s))}</span><span class="d"><i class="dot"></i>No run found</span></div>`;
    }).join('');

    // callouts from digests in the last 3 days (fallback: latest per skill)
    let pool = digs.filter(d => ageDays(d.date) <= 3);
    if (!pool.length) pool = [...latestBySkill.values()];
    const calls = [];
    pool.forEach(d => arr(d.callouts).forEach(c => calls.push(Object.assign({ skill: d.skill, date: d.date, url: d.url }, c))));
    const kindOf = c => { const k = String(c.kind || '').toLowerCase(); return k.startsWith('pos') ? 'pos' : k.startsWith('neg') ? 'neg' : k.startsWith('infl') ? 'inf' : 'oth'; };
    const col = (k, title) => {
      const xs = calls.filter(c => kindOf(c) === k).slice(0, 12);
      return `<div class="panel"><div class="panel-h"><h2>${title}</h2><span class="muted">${xs.length}</span></div>${xs.length ? `<div class="list">${xs.map(c =>
        `<div class="li"><span class="stripe ${k}"></span><div class="body">${tk(c.ticker)} ${attr(c.text)}${c.ticker ? valLine(c.ticker, true) : ''}<div class="sub">${c.source ? `<b class="srcb">${esc(c.source)}</b> · ` : ''}${esc(sk(c.skill))} · ${fmtD(c.date)}</div></div></div>`).join('')}</div>` : none('None in the latest digests.')}</div>`;
    };
    const themes = [];
    pool.forEach(d => arr(d.themes).forEach(t => themes.push(Object.assign({ skill: d.skill, date: d.date, url: d.url }, t))));

    const earn = arr(window.__EARN).filter(i => ageDays(i.date) <= 4).slice(0, 8);
    const up = arr(PR.upcoming).filter(u => { const a = ageDays(u.date); return a != null && a <= 0 && a >= -7; }).slice(0, 14);
    const LBL = { very_positive: 'Very positive', positive: 'Positive', mixed: 'Mixed', negative: 'Negative', very_negative: 'Very negative' };
    const tone = it => `<span class="chip s-${esc(it.tone)}">${LBL[it.tone] || esc(it.tone)}</span>`;

    document.getElementById('v-today').innerHTML =
      head('Today · ' + built.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' }), 'What changed',
        'Callouts from your latest digest runs with their primary sources, the prints from the last few days and what reports next.') +
      `<div class="runs">${strip}</div>` +
      `<div class="grid3">${col('pos', 'Most positive')}${col('neg', 'Most negative')}${col('inf', 'Inflections')}</div>` +
      (calls.some(c => kindOf(c) === 'oth') ? `<div>${col('oth', 'Other callouts')}</div>` : '') +
      `<div class="panel"><div class="panel-h"><h2>Latest themes</h2><a href="#themes">All themes →</a></div>${themes.length ? `<div class="list">${themes.slice(0, 6).map(t =>
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
    const host = document.getElementById('v-themes');
    host.innerHTML = head('Themes · from every digest', 'Themes', 'What is changing across your research flow, who benefits and who gets hurt, with the primary sources behind each theme.') +
      `<div class="panel" id="th-names"></div>` +
      `<div class="ctl" role="group" aria-label="Theme filters">
        <label for="th-q">Search <input type="search" id="th-q" placeholder="Theme, ticker or source"></label>
        <div class="seg" id="th-skill"><button type="button" data-v="" aria-pressed="true">All digests</button>${skills.map(k => `<button type="button" data-v="${esc(k)}" aria-pressed="false">${esc(sk(k))}</button>`).join('')}</div>
        <div class="seg" id="th-days"><button type="button" data-v="3" aria-pressed="false">3d</button><button type="button" data-v="7" aria-pressed="false">7d</button><button type="button" data-v="999" aria-pressed="true">All</button></div>
        <span class="count" id="th-count"></span></div>
      <div id="th-list"></div>`;
    const st = { q: '', skill: '', days: '999' };
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
      document.getElementById('th-list').innerHTML = xs.length ? `<div class="grid3">${xs.map(t =>
        `<div class="theme"><div class="panel-h"><h3>${esc(t.theme)}</h3>${link(t.url, fmtD(t.date))}</div><div class="sub">${esc(sk(t.skill))}</div><p>${attr(t.whats_changing)}</p>${(arr(t.winners).length || arr(t.losers).length) ? `<div class="wl">${arr(t.winners).length ? `<span>Benefits</span>${arr(t.winners).map(x => tk(x, 'up')).join(' ')}` : ''}${arr(t.losers).length ? `<span>Hurt</span>${arr(t.losers).map(x => tk(x, 'dn')).join(' ')}` : ''}</div>` : ''}${srcLine(t, 'Sources')}</div>`).join('')}</div>` : `<div class="nores">No themes match. Clear the search or widen the window.</div>`;
    }
    draw();
  }

  // ================= DAILY MOVES =================
  function renderDaily() {
    const host = document.getElementById('v-daily');
    const up = arr(DLY.up), dn = arr(DLY.down), secs = arr(DLY.sectors);
    const pct = v => v == null ? '' : ((+v > 0 ? '+' : '') + (+v).toFixed(1) + '%');
    const mover = (m) => `<div class="li"><span class="stripe ${+m.chg_1d >= 0 ? 'pos' : 'neg'}"></span><div class="body">${tk(m.ticker)} <b>${esc(m.name || '')}</b> <span class="mono ${+m.chg_1d >= 0 ? 'c-pos' : 'c-neg'}">${pct(m.chg_1d)}</span>${m.group ? ` <span class="chip out">${esc(m.group)}</span>` : ''}<div>${attr(m.why || 'No catalyst found in your sources or the news.')}</div>${valLine(m.ticker, true)}${srcLine(m)}</div></div>`;
    const W = 900, bar = secs.length ? Math.max(...secs.map(s => Math.abs(+s.median_1d || 0)), 0.5) : 1;
    host.innerHTML = head('Daily moves · ' + esc(DLY.as_of || ''), 'What moved and why',
      `Biggest one-day moves across the ${esc(DLY.universe_n || '')}-name Master comps universe on ${esc(DLY.as_of || 'the last trading day')}, by company and by subsector, with the catalyst from your research flow or the news.`) +
      `<section class="panel" id="live-moves"><div class="panel-h"><h2 id="live-h">Live prices</h2><span class="muted" id="live-status">connecting…</span></div><div id="live-body"><p class="sub" style="margin:0">Intraday moves load here from the Live sheet in your newest Master comps file (Bloomberg, via Microsoft 365); FactSet closes are the fallback.</p></div></section>` +
      (DLY.summary ? `<section class="panel"><h2>The day in brief</h2><ul class="b">${arr(DLY.summary).map(x => `<li>${attr(x)}</li>`).join('')}</ul></section>` : '') +
      `<section class="panel"><div class="panel-h"><h2>Sectors</h2><span class="muted">median 1-day move by Master comps subsector</span></div>${secs.length ? `<div class="secbars">${secs.map(s => `<div class="sb-row sb-click" data-g="${esc(s.group)}" data-src="eod" tabindex="0" role="button" aria-expanded="false"><span class="sb-l">${esc(s.group)} <span class="sub">(${esc(s.n)})</span></span><span class="sb-track"><span class="sb-bar ${+s.median_1d >= 0 ? 'pos' : 'neg'}" style="width:${(Math.abs(+s.median_1d || 0) / bar * 50).toFixed(1)}%;${+s.median_1d >= 0 ? 'left:50%' : 'right:50%'}"></span></span><span class="sb-v mono ${+s.median_1d >= 0 ? 'c-pos' : 'c-neg'}">${pct(s.median_1d)}</span><span class="sb-w sub">${s.why ? attr(s.why) : ''}</span></div>`).join('')}</div>` : none('No sector data yet.')}</section>` +
      `<div class="grid2"><section class="panel"><div class="panel-h"><h2 class="c-pos">Biggest gainers</h2><span class="muted">${up.length}</span></div>${up.length ? `<div class="list">${up.map(mover).join('')}</div>` : none('No data yet.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2 class="c-neg">Biggest decliners</h2><span class="muted">${dn.length}</span></div>${dn.length ? `<div class="list">${dn.map(mover).join('')}</div>` : none('No data yet.')}</section></div>` +
      (DLY.notes ? `<p class="sub" style="margin:0">${esc(DLY.notes)}</p>` : '');
    wireSectors(host);
    startLive();
  }

  // ---- sector drill-down: click a sector bar to see the reason and every name in it, with each name's story ----
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
      return `<div class="sd-row${big ? ' big' : ''}"><span class="sd-t">${tk(x.t)} <span class="sub">${esc(x.n || '')}</span></span><span class="mono ${x.c >= 0 ? 'c-pos' : 'c-neg'}">${p1(x.c)}</span>${x.c5 != null ? `<span class="sub mono">5d ${p1(x.c5)}</span>` : '<span></span>'}<span class="sd-w">${s && s.why ? attr(s.why) + (arr(s.sources).length ? ` <span class="sub">· ${arr(s.sources).map(esc).join(' · ')}</span>` : '') : (big && useStories ? '<span class="sub">No catalyst found in your sources or the news.</span>' : '')}</span></div>`; }).join('');
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
      const head = document.getElementById('live-h'); if (head) head.textContent = showDate ? 'Live from FactSet (closes)' : 'Live from Bloomberg (intraday)';
      const pct = v => v == null || !isFinite(v) ? '—' : ((v > 0 ? '+' : '') + v.toFixed(1) + '%');
      const cls = v => v >= 0 ? 'c-pos' : 'c-neg';
      const med = a => { const s = a.slice().sort((x, y) => x - y); return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0; };
      const groups = new Map(); stocks.forEach(r => { if (!groups.has(r.g)) groups.set(r.g, []); groups.get(r.g).push(r); });
      LIVE_G = groups; LIVE_SAME = sameDayOf(latest, showDate);
      const secs = [...groups].map(([g, a]) => ({ g, n: a.length, m: med(a.map(r => r.c1)), best: a.reduce((x, y) => y.c1 > x.c1 ? y : x), worst: a.reduce((x, y) => y.c1 < x.c1 ? y : x) })).sort((a, b) => b.m - a.m);
      const bar = Math.max(...secs.map(s => Math.abs(s.m)), 0.5);
      const why = new Map(arr(DLY.up).concat(arr(DLY.down)).map(m => [m.ticker, m]));
      const sameDay = showDate ? (latest && DLY.as_of === latest) : (DLY.as_of === latest);
      const line = r => { const w = sameDay ? why.get(r.t) : null; return `<div class="li"><span class="stripe ${r.c1 >= 0 ? 'pos' : 'neg'}"></span><div class="body">${tk(r.t)} <b>${esc(r.n)}</b> <span class="mono ${cls(r.c1)}">${pct(r.c1)}</span> ${r.c5 != null ? `<span class="sub mono">5d ${pct(r.c5)}</span>` : ''} <span class="chip out">${esc(r.g)}</span>${showDate && r.date !== latest ? ` <span class="sub">close ${esc(r.date)}</span>` : ''}${w && w.why ? `<div>${attr(w.why)}</div>` : ''}</div></div>`; };
      const s = stocks.slice().sort((a, b) => b.c1 - a.c1), up = s.slice(0, 12), dn = s.slice(-12).reverse();
      const upN = stocks.filter(r => r.c1 > 0).length;
      status(stat);
      body(`<p class="sub" style="margin:0 0 8px">${stocks.length} names priced · ${upN} up / ${stocks.length - upN} down · median ${pct(med(stocks.map(r => r.c1)))}${bm.length ? ' · ' + bm.map(b => `${esc(b.t)} <span class="mono ${cls(b.c1)}">${pct(b.c1)}</span>`).join(' · ') : ''}${sameDay || !DLY.as_of ? '' : ` · <b>newer than the written read below (${esc(DLY.as_of)})</b>`}</p>` +
        `<div class="secbars">${secs.map(x => `<div class="sb-row sb-click" data-g="${esc(x.g)}" data-src="live" tabindex="0" role="button" aria-expanded="false"><span class="sb-l">${esc(x.g)} <span class="sub">(${x.n})</span></span><span class="sb-track"><span class="sb-bar ${x.m >= 0 ? 'pos' : 'neg'}" style="width:${(Math.abs(x.m) / bar * 50).toFixed(1)}%;${x.m >= 0 ? 'left:50%' : 'right:50%'}"></span></span><span class="sb-v mono ${cls(x.m)}">${pct(x.m)}</span><span class="sb-w sub">best ${esc(x.best.t)} ${pct(x.best.c1)} · worst ${esc(x.worst.t)} ${pct(x.worst.c1)}</span></div>`).join('')}</div>` +
        `<div class="grid2" style="margin-top:14px"><div><h3 class="c-pos">Biggest gainers</h3><div class="list">${up.map(line).join('')}</div></div><div><h3 class="c-neg">Biggest decliners</h3><div class="list">${dn.map(line).join('')}</div></div></div>`);
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
              stocks.push({ t: u.t || (parts[1] && parts[1] !== 'US' ? full : parts[0]), n: u.n || '', g: (c[3] || '').trim() || u.g || 'Other', c1, c5: null, px, date: today }); }
            if (!stocks.length) { if (!okOnce) fallback(); return; }
            okOnce = true;
            const saved = f.lastModifiedDateTime ? new Date(f.lastModifiedDateTime) : null;
            const got = r.cache && r.cache.storedAt ? new Date(r.cache.storedAt) : new Date();
            const hm = d => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
        .sort((a, b) => ((+b[st.k] || 0) - (+a[st.k] || 0)) * (st.dir === 'desc' ? 1 : -1)).slice(0, 150);
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
    const st = { sec: '', sub: '', sel: [], range: 270, mode: 'c', pil: '', imp: 'all', stype: '', q: '', shown: 100 };
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
      $('lb-body').innerHTML = list.slice(0, 150).map(c => `<tr><td>${tk(c.t)} <span class="sub">${esc(c.n || '')}</span></td><td class="sub">${esc(c.sub || c.sec)}</td><td class="n mono">${sgn(c.c[n])}</td><td class="n mono ${c.x[n] >= 0 ? 'c-pos' : 'c-neg'}">${sgn(c.x[n])}</td><td class="n mono ${c.d30 >= 0 ? 'c-pos' : 'c-neg'}">${sgn(c.d30)}</td><td class="n mono">${sgn(c.g[n])}</td><td class="n mono">${sgn(c.m[n])}</td><td class="n mono">${sgn(c.k[n])}</td><td class="n mono">${sgn(c.r[n])}</td><td class="n">${c.e[n]}</td><td>${st.sel.includes(c.rid) ? '' : `<button type="button" class="btn lb-add" data-r="${c.rid}" aria-label="Chart ${esc(c.t)}">Chart</button>`}</td></tr>`).join('') || `<tr><td colspan="11" class="nores">No indexed companies in this selection.</td></tr>`;
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
      body.innerHTML = list.length ? list.slice(0, st.shown).map(r => { const m = byRid.get(r[1]) || {}, d = DIR[r[4]]; return `<tr><td class="mono">${fmtD(r[2])}</td><td>${tk(m.t)}</td><td class="sub">${esc(r[3])}</td><td>${d ? `<span class="chip ${d[1] === 'pos' ? 'up' : d[1] === 'neg' ? 'dn' : ''}">${d[0]}</span>` : ''}</td><td>${esc(r[9])}</td><td class="sub">${esc(SRC[r[7]] || '')}${r[6] ? ` <span class="chip out">${esc(r[6])}</span>` : ''}</td></tr>`; }).join('')
        : `<tr><td colspan="6" class="nores">No datapoints match. Widen the range or clear a filter.</td></tr>`;
      more.hidden = list.length <= st.shown;
    }
    function load() {
      const n = +X.parts || 0, get = p => fetch(p).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); });
      Promise.all([get('dp/sources.json')].concat(Array.from({ length: n }, (_, i) => get(`dp/part${i + 1}.json`)))).then(([s, ...ps]) => {
        SRC = arr(s.sources); ROWS = ps.flatMap(p => arr(p.rows));
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
    rows = arr(rows); if (!rows.length) return none('Nothing in the latest run.');
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
    const ideas = arr(ID.ideas), theses = arr(ID.theses), cycles = arr(ID.cycles), oc = arr(ID.opcomps);
    const dir = d => { const s = String(d || '').toLowerCase(); return ['long', 'short', 'pair', 'watch'].find(k => s.includes(k)) || 'watch'; };
    document.getElementById('v-ideas').innerHTML =
      head('Idea generator · thesis builder · industry cycle · operating comps', 'Ideas &amp; cycle', 'Open ideas, where each thesis stands, and where each industry sits in its cycle.') +
      `<section class="panel"><div class="panel-h"><h2>Ideas</h2><span class="muted">${ideas.length}</span></div>${ideas.length ? `<div class="grid3">${ideas.map(i =>
        `<article class="idea"><div class="top">${tk(i.ticker)}<b>${esc(i.company)}</b><span class="chip dir-${dir(i.direction)}">${esc(i.direction || 'watch')}</span>${i.conviction ? `<span class="chip out">${esc(i.conviction)}</span>` : ''}${link(i.url, fmtD(i.date))}</div><p><b>${esc(i.idea)}</b></p>${i.why_now ? `<p>${esc(i.why_now)}</p>` : ''}${arr(i.catalysts).length ? `<div class="sub">Catalysts: ${arr(i.catalysts).map(esc).join(' · ')}</div>` : ''}${arr(i.risks).length ? `<div class="sub">Risks: ${arr(i.risks).map(esc).join(' · ')}</div>` : ''}${srcLine(i)}</article>`).join('')}</div>` : none('No idea-generator output found since September.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2>Industry cycle</h2></div>${cycles.length ? `<div class="grid3">${cycles.map(c =>
        `<article class="idea"><div class="top"><b>${esc(c.industry)}</b>${c.phase ? `<span class="chip phase">${esc(c.phase)}</span>` : ''}${link(c.url, fmtD(c.date))}</div><dl class="kv">${c.margin_vs_peak ? `<dt>Margin vs peak</dt><dd>${esc(c.margin_vs_peak)}</dd>` : ''}${c.valuation ? `<dt>Valuation</dt><dd>${esc(c.valuation)}</dd>` : ''}</dl>${arr(c.signals).length ? `<ul class="b">${arr(c.signals).map(s => `<li>${attr(s)}</li>`).join('')}</ul>` : ''}${srcLine(c)}</article>`).join('')}</div>` : none('No industry-cycle output found since September.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2>Theses</h2><span class="muted">${theses.length} · dated by last edit</span></div>${theses.length ? `<div class="list">${theses.map(t =>
        `<div class="li"><div class="body">${tk(t.ticker)} <b>${esc(t.company)}</b> ${t.stance ? `<span class="chip dir-${dir(t.stance)}">${esc(t.stance)}</span>` : ''}<div>${esc(t.summary)}</div>${srcLine(t)}${arr(t.tenets).length ? `<details><summary>Tenets</summary><ul class="b">${arr(t.tenets).map(x => `<li>${esc(x)}</li>`).join('')}</ul>${t.what_would_change ? `<p class="sub" style="margin:6px 0 0">What would change it: ${esc(t.what_would_change)}</p>` : ''}</details>` : ''}</div><div class="side">${fmtD(t.updated)} ${link(t.url, 'Notion')}</div></div>`).join('')}</div>` : none('No thesis-builder output found since September.')}</section>` +
      `<section class="panel"><div class="panel-h"><h2>Operating comps</h2></div>${oc.length ? `<div class="grid2">${oc.map(o =>
        `<article class="idea"><div class="top"><b>${esc(o.title)}</b>${link(o.url, fmtD(o.date))}</div>${o.peer_set ? `<div class="sub">${esc(o.peer_set)}</div>` : ''}<ul class="b">${arr(o.findings).map(f => `<li>${attr(f)}</li>`).join('')}</ul>${srcLine(o)}</article>`).join('')}</div>` : none('No operating-comps output found since September.')}</section>`;
  }

  // ================= PREP =================
  function renderPrep() {
    const up = arr(PR.upcoming).slice().sort((a, b) => String(a.date).localeCompare(String(b.date)));
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
      const xs = prep.filter(p => !cur || p.type === cur);
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

  // ================= ROUTINES: one page per scheduled routine =================
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
      const runs = arr(cur.runs);
      const li = x => `<div class="li"><span class="stripe ${sent(x.sentiment)}"></span><div class="body">${x.ticker ? tk(x.ticker) + ' ' : ''}${attr(x.text || '')}${x.sb_id ? ` <span class="sub mono">SB #${esc(x.sb_id)}</span>` : ''}</div></div>`;
      const secs = Object.entries(cur.by_sector || {});
      body = `<section class="panel"><div class="panel-h"><h2>${esc(cur.name)}</h2><span class="muted"><i class="dot ${dotCls(cur.status)}"></i> ${esc(cur.status || '')}${cur.last_run ? ' · last run ' + esc(cur.last_run) : ''}</span></div>` +
        `<p class="sub" style="margin:0 0 8px">${esc(cur.schedule || '')}${cur.note ? ' · ' + attr(cur.note) : ''}</p>` +
        (runs[0] ? `<p style="margin:0">${link(runs[0].url, 'Open the latest page in Notion')}${runs[0].window ? ' · ' + esc(runs[0].window) : ''}${runs[0].supabase_line ? ' · ' + esc(runs[0].supabase_line) : ''}</p>` : '') + `</section>` +
        (arr(cur.callouts).length ? `<section class="panel"><h2>Call-outs</h2><div class="list">${arr(cur.callouts).map(li).join('')}</div></section>` : '') +
        (arr(cur.themes).length ? `<section class="panel"><h2>Themes</h2>${arr(cur.themes).map(t => `<div class="theme"><h3>${esc(t.theme || '')}</h3><p>${attr(t.whats_changing || '')}</p>${(arr(t.winners).length || arr(t.losers).length) ? `<div class="wl">${arr(t.winners).length ? `<span>Benefits</span>${arr(t.winners).map(x => tk(x, 'up')).join(' ')}` : ''}${arr(t.losers).length ? `<span>Hurt</span>${arr(t.losers).map(x => tk(x, 'down')).join(' ')}` : ''}</div>` : ''}</div>`).join('')}</section>` : '') +
        (arr(cur.revisions).length ? `<section class="panel"><h2>Revisions</h2><div class="list">${arr(cur.revisions).map(x => li({ ticker: x.ticker, text: [x.metric, x.change, x.text].filter(Boolean).join(' · '), sentiment: x.sentiment || (String(x.change || '').trim().startsWith('-') ? 'negative' : 'positive') })).join('')}</div></section>` : '') +
        (arr(cur.ideas).length ? `<section class="panel"><h2>Ideas</h2><div class="list">${arr(cur.ideas).map(x => li({ ticker: x.ticker, text: (x.bucket ? '<b>' + esc(x.bucket) + '</b> · ' : '') + esc(x.thesis || x.text || ''), sentiment: /short/i.test(x.bucket || '') ? 'negative' : 'positive' })).join('')}</div></section>` : '') +
        (secs.length ? `<section class="panel"><h2>Datapoints by sector</h2>${secs.map(([g, xs]) => `<details class="rt-sec"><summary><b>${esc(g)}</b> <span class="sub">${arr(xs).length}</span></summary><div class="list">${arr(xs).map(li).join('')}</div></details>`).join('')}</section>` : '') +
        (runs.length ? `<section class="panel"><h2>Recent runs</h2><table class="dt"><thead><tr><th>Run</th><th>Window</th><th class="n">Datapoints</th><th>Supabase</th></tr></thead><tbody>${runs.map(r => `<tr><td>${link(r.url, r.title || r.date)}</td><td class="sub">${esc(r.window || '')}</td><td class="n">${esc(r.datapoint_count ?? '')}</td><td class="sub">${esc(r.supabase_line || '')}</td></tr>`).join('')}</tbody></table></section>` : '');
    }
    host.innerHTML = head('Routines' + (RT.as_of ? ' · ' + esc(RT.as_of) : ''), 'Your scheduled research routines', 'One page per routine: its latest call-outs, themes and datapoints, whether it ran on schedule, and its recent runs. The Daily moves reasons are drawn from these first.') +
      `<div class="rt-wrap">${nav}<div class="rt-body">${body}</div></div>`;
  }

  // ================= PIPELINE: every long and short being tracked =================
  function renderPipeline() {
    const P = D.pipeline || {}, items = arr(P.items), host = document.getElementById('v-pipeline');
    const moves = new Map(arr(DLY.moves).map(m => [String(m.t).toUpperCase(), m]));
    const pctTxt = v => v == null || !isFinite(v) ? '' : (v > 0 ? '+' : '') + Math.round(v * 100) + '%';
    const upOf = it => { const u = it.upside; if (!u) return null; const lo = u.pct_low, hi = u.pct_high; const v = hi != null ? hi : lo; return v == null ? null : v; };
    const secs = [...new Set(items.map(i => i.sector).filter(Boolean))].sort();
    const st = { dir: '', status: '', sec: '', q: '', sort: 'status' };
    host.innerHTML = head('Pipeline' + (P.as_of ? ' · ' + esc(P.as_of) : ''), 'Longs & shorts we are tracking',
      'Every name on the Pipeline/Active/Ideas page, the Shorts database, recent Idea Generator runs and thesis pages: the elevator pitch, and the upside or downside where a target has been written down.') +
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
      let list = items.filter(it => (!st.dir || it.direction === st.dir) && (!st.status || it.status === st.status) && (!st.sec || it.sector === st.sec) &&
        (!st.q || `${it.ticker} ${it.company} ${it.pitch} ${it.theme}`.toLowerCase().includes(st.q)));
      if (st.sort === 'up') list = list.slice().sort((a, b) => { const x = upOf(a), y = upOf(b); const fx = x == null ? -9 : (a.direction === 'short' ? -x : x), fy = y == null ? -9 : (b.direction === 'short' ? -y : y); return fy - fx; });
      else if (st.sort === 'recent') list = list.slice().sort((a, b) => String(b.updated || b.added || '').localeCompare(String(a.updated || a.added || '')));
      else if (st.sort === 'az') list = list.slice().sort((a, b) => String(a.ticker).localeCompare(String(b.ticker)));
      else list = list.slice().sort((a, b) => (SO[a.status] ?? 3) - (SO[b.status] ?? 3) || (a.direction === 'short') - (b.direction === 'short'));
      const nl = list.filter(i => i.direction === 'long').length;
      $('pl-count').textContent = `${list.length} names · ${nl} long / ${list.length - nl} short`;
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

  // ================= ROUTER =================
  const VIEWS = ['today', 'daily', 'routines', 'pipeline', 'themes', 'earnings', 'datapoints', 'signals', 'screens', 'ideas', 'prep', 'health', 'sources', 'method'];
  const R = { daily: renderDaily, routines: renderRoutines, pipeline: renderPipeline, signals: renderSignals, sources: renderSources, today: renderToday, themes: renderThemes, datapoints: renderDatapoints, screens: renderScreens, ideas: renderIdeas, prep: renderPrep, health: renderHealth };
  const done = {};
  function show() {
    let v = (location.hash || '').slice(1).split('/')[0]; if (!VIEWS.includes(v)) v = 'today';
    if (v === 'routines' && done[v]) { renderRoutines(); }
    if (R[v] && !done[v]) { try { R[v](); } catch (e) { document.getElementById('v-' + v).innerHTML = `<div class="nores">This tab could not render: ${esc(e.message)}</div>`; } done[v] = 1; }
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
