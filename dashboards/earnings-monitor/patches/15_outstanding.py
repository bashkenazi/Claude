#!/usr/bin/env python3
"""Outstanding tab (Bobby, 2026-11-18: "see what I've asked of people and if they've done it ... filter it by my
analysts: Poojan, Adish, Shish, Rebecca, but also anyone else").

Every ask Bobby made by email (Sent Items, last 30 days), with whether the person did it, judged from their replies
across every mail folder. Rows live only in the page database:
  - collection "outstanding": one doc per ask (id = sha1(internetMessageId|first asked email)[:16]) with fields
    people[], to[], ask, subject, sent_at, link, status (done|replied|no_reply|closed), evidence, reply_at,
    reply_link, ticker, and manual_status (set from the page: done|dismissed|null; a refresh must keep it).
  - collection "outstanding_meta", doc "run": last_run, window_days, scanned, found.
The sweep writes them with ArtifactData; this tab only reads them and writes manual_status.
Usage: 15_outstanding.py FILE [FILE ...] (in place). Idempotent."""
import sys

MARKER = "/* outstanding-tab v1 */"

NAV_OLD = '<a href="#today">Today</a>'
NAV_NEW = NAV_OLD + '\n    <a href="#outstanding">Outstanding <span id="os-count" class="sub"></span></a>'
VIEW_OLD = '<div class="view" data-view="today" id="v-today"></div>'
VIEW_NEW = VIEW_OLD + '\n<div class="view" data-view="outstanding" id="v-outstanding"></div>'
VIEWS_OLD = "const VIEWS = ['today', "
VIEWS_NEW = "const VIEWS = ['today', 'outstanding', "
R_OLD = "const R = { mgmt: renderMgmt, "
R_NEW = "const R = { outstanding: renderOutstanding, mgmt: renderMgmt, "
SHOW_OLD = "    if (v === 'notes' && done[v]) { renderNotes(); }"
SHOW_NEW = SHOW_OLD + "\n    if (v === 'outstanding' && done[v]) { renderOutstanding(); }"
ROUTER = "  // ================= ROUTER ================="

CSS = r"""
/* outstanding-tab v1 */
#v-outstanding .os-who { display: flex; align-items: baseline; gap: 8px; padding: 10px 0 2px; border-bottom: 1px solid var(--rule-2); }
#v-outstanding .os-who h2 { font-size: 15px; }
#v-outstanding .stripe.os-no_reply { background: var(--neg); } #v-outstanding .stripe.os-replied { background: var(--warn); }
#v-outstanding .stripe.os-done, #v-outstanding .stripe.os-closed { background: var(--pos); }
#v-outstanding .os-ask { color: var(--ink); font-weight: 650; }
#v-outstanding .os-ev { font-size: 12.5px; color: var(--ink-2); margin-top: 2px; }
#v-outstanding .os-act { display: flex; gap: 4px; margin-top: 4px; justify-content: flex-end; }
#v-outstanding .os-act .btn { padding: 2px 8px; font-size: 12px; }
#v-outstanding .stat.os-on { background: var(--surface-2); box-shadow: inset 0 -2px 0 var(--ink); }
#v-outstanding .stat { cursor: pointer; }
#v-outstanding .os-age.old { color: var(--neg); font-weight: 600; }
"""

JS = r"""  """ + MARKER + r"""
  const OS = { started: false, items: [], meta: null, db: null, err: '', who: 'all', st: 'open', src: 'all', q: '' };
  const osSrc = r => r.source === 'slack' ? 'slack' : 'email';
  const OS_PEOPLE = [['poojan', 'Poojan'], ['adish', 'Adish'], ['ashish', 'Ashish'], ['rebecca', 'Rebecca'], ['ademola', 'Ademola'], ['other', 'Others']];
  const OS_LBL = { no_reply: 'No reply', replied: 'In progress', done: 'Done', closed: 'Closed', dismissed: 'Dismissed' };
  const OS_CHIP = { no_reply: 's-negative', replied: 's-mixed', done: 's-positive', closed: 'out', dismissed: 'out' };
  const osSt = r => r.manual_status || r.status || 'no_reply';
  const osOpen = r => ['no_reply', 'replied'].includes(osSt(r));
  const osAge = r => Math.max(0, Math.floor((Date.now() - new Date(r.sent_at)) / 864e5));
  const osPeople = r => (Array.isArray(r.people) && r.people.length ? r.people : ['other']);
  function osStart() {
    if (OS.started) return; OS.started = true;
    if (!(window.claude && typeof window.claude.use === 'function')) { OS.err = 'The asks are kept in this page’s database; open the page on claude.ai to see them.'; return; }
    const t = setTimeout(() => { if (!OS.db) { OS.err = 'Could not reach the page database.'; osRe(); } }, 10000);
    window.claude.use('db').then(db => {
      if (!db) { clearTimeout(t); OS.err = 'Sign in on claude.ai to see your outstanding asks.'; osRe(); return; }
      OS.db = db;
      db.collection('outstanding').onSnapshot(snap => { clearTimeout(t); OS.items = snap.docs.map(d => ({ id: d.id, ...JSON.parse(JSON.stringify(d.data())) })); osRe(); }, () => { clearTimeout(t); OS.err = 'Could not read the asks.'; osRe(); });
      db.collection('outstanding_meta').onSnapshot(snap => { const d = snap.docs.find(x => x.id === 'run'); OS.meta = d ? JSON.parse(JSON.stringify(d.data())) : null; osRe(); }, () => {});
    }).catch(() => { clearTimeout(t); OS.err = 'Could not reach the page database.'; osRe(); });
  }
  function osRe() {
    const c = document.getElementById('os-count'); if (c) { const n = OS.items.filter(osOpen).length; c.textContent = n ? String(n) : ''; }
    const v = document.getElementById('v-outstanding'); if (v && v.classList.contains('on')) { try { renderOutstanding(); } catch (e) {} }
  }
  UPD.outstanding = () => ({ t: OS.meta && OS.meta.last_run, src: 'email + Slack sweep' });
  function renderOutstanding() {
    osStart();
    const host = document.getElementById('v-outstanding'); if (!host) return;
    const all = OS.items, open = all.filter(osOpen);
    const cnt = k => open.filter(r => osPeople(r).includes(k)).length;
    const oldest = open.reduce((m, r) => Math.max(m, osAge(r)), 0);
    const q = OS.q.trim().toLowerCase();
    let rows = all.filter(r => (OS.who === 'all' || osPeople(r).includes(OS.who)) && (OS.src === 'all' || osSrc(r) === OS.src));
    rows = rows.filter(r => OS.st === 'all' ? true : OS.st === 'open' ? osOpen(r) : osSt(r) === OS.st || (OS.st === 'done' && ['done', 'closed', 'dismissed'].includes(osSt(r))));
    if (q) rows = rows.filter(r => [r.ask, r.subject, r.evidence, r.ticker, r.channel, ...(r.to || []).map(p => p.name)].join(' ').toLowerCase().includes(q));
    rows.sort((a, b) => String(a.sent_at).localeCompare(String(b.sent_at)));
    const groups = (OS.who === 'all' ? OS_PEOPLE : OS_PEOPLE.filter(p => p[0] === OS.who)).map(([k, l]) => [k, l, rows.filter(r => osPeople(r)[0] === k || (OS.who !== 'all' && osPeople(r).includes(k)))]).filter(g => g[2].length);
    const last = OS.meta && OS.meta.last_run ? `Last sweep ${esc(fmtD(String(OS.meta.last_run).slice(0, 10)))} · ${esc(OS.meta.window_days || 30)}-day window · ${esc(OS.meta.scanned || '?')} sent emails${OS.meta.slack_scanned != null ? ` and ${esc(OS.meta.slack_scanned)} Slack messages` : ''} read` : 'Not swept yet';
    const row = r => {
      const st = osSt(r), age = osAge(r), to = (r.to || []).map(p => p.name || p.email).join(', ');
      return `<div class="li"><span class="stripe os-${esc(st === 'dismissed' ? 'closed' : st)}"></span><div class="body">` +
        `<div class="chips"><span class="chip ${OS_CHIP[st] || ''}">${esc(OS_LBL[st] || st)}</span><span class="chip out">${osSrc(r) === 'slack' ? 'Slack' + (r.channel ? ' · ' + esc(r.channel) : '') : 'Email'}</span>${r.ticker ? tk(r.ticker) : ''}<span class="sub">to ${esc(to)}</span>${r.manual_status ? '<span class="chip out">set by you</span>' : ''}</div>` +
        `<div class="os-ask">${esc(r.ask || '')}</div>` +
        (r.evidence ? `<div class="os-ev">${esc(r.evidence)}${r.reply_at ? ` <span class="muted">(${esc(fmtD(r.reply_at))})</span>` : ''}</div>` : '') +
        `<div class="srcl"><span>${osSrc(r) === 'slack' ? 'Slack' : 'Email'}</span>${r.link ? `<a class="ext" href="${esc(r.link)}" target="_blank" rel="noopener">${esc(r.subject || 'Your message')} →</a>` : esc(r.subject || '')}${r.reply_link ? ` · <a class="ext" href="${esc(r.reply_link)}" target="_blank" rel="noopener">Their reply →</a>` : ''}</div></div>` +
        `<div class="side">${esc(fmtD(r.sent_at))} · <span class="os-age${osOpen(r) && age >= 7 ? ' old' : ''}">${age}d</span>` +
        `<div class="os-act">${osOpen(r) ? `<button type="button" class="btn" data-os="${esc(r.id)}" data-st="done">Done</button><button type="button" class="btn" data-os="${esc(r.id)}" data-st="dismissed">Dismiss</button>` : (r.manual_status ? `<button type="button" class="btn" data-os="${esc(r.id)}" data-st="">Reopen</button>` : '')}</div></div></div>`;
    };
    host.innerHTML =
      `<section class="panel" style="gap:8px"><span class="eyebrow">Outstanding · asks from your email and Slack</span><h1>What you’re waiting on</h1>` +
      `<p class="lede">Every question or request you sent by email or Slack (channels and DMs) in the last 30 days, and whether the person did it, judged from their replies in every mail folder and in Slack. Red: no reply. Amber: replied but not finished. Mark a row Done or Dismiss it and the next sweep keeps your call.</p><p class="sub">${last}</p></section>` +
      `<div class="summary">` + [['all', 'All open', open.length]].concat(OS_PEOPLE.map(([k, l]) => [k, l, cnt(k)])).map(([k, l, n]) => `<div class="stat${OS.who === k ? ' os-on' : ''}" data-osw="${k}" role="button" tabindex="0"><span class="v">${n}</span><span class="l">${esc(l)}</span></div>`).join('') +
      `<div class="stat"><span class="v">${open.length ? oldest + 'd' : '–'}</span><span class="l">Oldest open</span></div></div>` +
      `<div class="ctl" role="group" aria-label="Filters"><div class="seg" aria-label="Person">${[['all', 'Everyone']].concat(OS_PEOPLE).map(([k, l]) => `<button type="button" data-osw="${k}" aria-pressed="${OS.who === k}">${esc(l)}</button>`).join('')}</div>` +
      `<div class="seg" aria-label="Status">${[['open', 'Open'], ['no_reply', 'No reply'], ['replied', 'In progress'], ['done', 'Done'], ['all', 'All']].map(([k, l]) => `<button type="button" data-oss="${k}" aria-pressed="${OS.st === k}">${l}</button>`).join('')}</div>` +
      `<div class="seg" aria-label="Source">${[['all', 'Email + Slack'], ['email', 'Email'], ['slack', 'Slack']].map(([k, l]) => `<button type="button" data-osc="${k}" aria-pressed="${OS.src === k}">${l}</button>`).join('')}</div>` +
      `<label for="os-q">Search <input type="search" id="os-q" placeholder="Ask, ticker or name" value="${esc(OS.q)}"></label><span class="count">${rows.length} shown</span></div>` +
      (OS.err ? none(esc(OS.err)) : !OS.db && !all.length ? none('Loading…') : !rows.length ? `<section class="panel">${none(OS.st === 'open' ? 'Nothing open for this filter.' : 'No asks match.')}</section>` :
        groups.map(([k, l, xs]) => `<section class="panel"><div class="os-who"><h2>${esc(l)}</h2><span class="muted">${xs.filter(osOpen).length} open · ${xs.length} shown</span></div><div class="list">${xs.map(row).join('')}</div></section>`).join(''));
    host.querySelectorAll('[data-osw]').forEach(b => { const go = () => { OS.who = b.dataset.osw; renderOutstanding(); }; b.addEventListener('click', go); b.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } }); });
    host.querySelectorAll('[data-oss]').forEach(b => b.addEventListener('click', () => { OS.st = b.dataset.oss; renderOutstanding(); }));
    host.querySelectorAll('[data-osc]').forEach(b => b.addEventListener('click', () => { OS.src = b.dataset.osc; renderOutstanding(); }));
    const qi = host.querySelector('#os-q'); if (qi) qi.addEventListener('input', () => { OS.q = qi.value; clearTimeout(OS.qt); OS.qt = setTimeout(() => { renderOutstanding(); const n = document.getElementById('os-q'); if (n) { n.focus(); n.setSelectionRange(n.value.length, n.value.length); } }, 250); });
    host.querySelectorAll('[data-os]').forEach(b => b.addEventListener('click', async () => {
      if (!OS.db) return; b.disabled = true;
      try { await OS.db.collection('outstanding').doc(b.dataset.os).update({ manual_status: b.dataset.st || null, manual_at: new Date().toISOString() }); }
      catch (x) { b.disabled = false; alert('Could not save: ' + ((x && x.message) || 'error')); }
    }));
  }
  setTimeout(osStart, 0);

"""


def patch(path):
    s = open(path, encoding="utf-8").read()
    if MARKER in s:
        print(f"{path}: already patched"); return
    for old, new in [(NAV_OLD, NAV_NEW), (VIEW_OLD, VIEW_NEW), (VIEWS_OLD, VIEWS_NEW), (R_OLD, R_NEW), (SHOW_OLD, SHOW_NEW)]:
        if s.count(old) != 1:
            sys.exit(f"{path}: anchor not found exactly once: {old[:60]!r}")
        s = s.replace(old, new)
    if s.count(ROUTER) != 1:
        sys.exit(f"{path}: router anchor missing")
    s = s.replace(ROUTER, JS + ROUTER)
    i = s.find("</style>")
    i = s.find("</style>", i + 1)  # first is the publish skeleton's reset; the page's own style block is next
    s = s[:i] + CSS + s[i:]
    open(path, "w", encoding="utf-8").write(s)
    print(f"{path}: patched")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        patch(f)
