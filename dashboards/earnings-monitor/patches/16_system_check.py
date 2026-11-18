#!/usr/bin/env python3
"""Routines › System check (Bobby, 2026-11-18: "all routines, all agents, and have a check or an X ... one central place
to see what's going on with all our skills, agents, and automations").

A sub-view of the Routines tab (#routines/check). Rows come from page db collection "system_check", doc "latest":
  {checked_at, checked_by, note, items: [{kind: routine|skill|agent|connector, name, status: ok|warn|fail|off,
   headline, problems[], fix, trigger_id?}]}
written by the "System check (Tech Daily)" scheduled task (or a manual audit) with ArtifactData. The page overlays the live
list_triggers data the All routines view already loads: a routine whose live health is Missed/Failed, or that has a run
newer than the check, is flagged; live tasks missing from the doc show as "Not checked yet".
Usage: 16_system_check.py FILE [FILE ...] (in place; tabs.js or a built page). Idempotent."""
import sys

MARKER = "/* system-check v1 */"

NAV_OLD = """<a href="#routines/all"${!cur ? ' aria-current="page"' : ''}><i class="dot fresh"></i><span><b>All routines</b><span class="sub">Health of every scheduled agent</span></span></a>"""
NAV_NEW = """<a href="#routines/all"${!cur && key !== 'check' ? ' aria-current="page"' : ''}><i class="dot fresh"></i><span><b>All routines</b><span class="sub">Health of every scheduled agent</span></span></a><a href="#routines/check"${key === 'check' ? ' aria-current="page"' : ''}><i class="dot ${scDot()}"></i><span><b>System check</b><span class="sub">✓ / ✗ for every routine, skill, agent and connector</span></span></a>"""
CUR_OLD = "const cur = key === 'all' ? null"
CUR_NEW = "const cur = (key === 'all' || key === 'check') ? null"
BODY_OLD = "let body = cur ? none('No routine output collected yet.') : rtOverview(list);"
BODY_NEW = "let body = cur ? none('No routine output collected yet.') : key === 'check' ? scView() : rtOverview(list);"
ANCHOR = "  function renderRoutines() {"

CSS = r"""
/* system-check v1 */
.sc-row { border-bottom: 1px solid var(--rule-2); }
.sc-row > summary { display: flex; gap: 10px; align-items: baseline; padding: 8px 2px; cursor: pointer; list-style: none; text-transform: none; letter-spacing: normal; font-size: 14px; color: var(--ink); }
.sc-row > summary::-webkit-details-marker { display: none; }
.sc-ic { flex: 0 0 22px; font-weight: 700; text-align: center; border-radius: 4px; }
.sc-ok .sc-ic { color: var(--pos); } .sc-fail .sc-ic { color: var(--neg); } .sc-warn .sc-ic { color: var(--warn); } .sc-off .sc-ic { color: var(--ink-3, #888); }
.sc-nm { font-weight: 650; min-width: 0; } .sc-hd { color: var(--ink-2); font-size: 13px; flex: 1; min-width: 0; }
.sc-det { padding: 0 0 10px 32px; font-size: 13px; } .sc-det ul { margin: 4px 0; padding-left: 18px; } .sc-fix { margin-top: 4px; }
.sc-grp { margin-top: 6px; }
@media (max-width: 640px) { .sc-row > summary { flex-wrap: wrap; } .sc-hd { flex-basis: 100%; padding-left: 32px; } }
"""

JS = r"""  """ + MARKER + r"""
  const SYC = { st: 'idle', doc: null, err: '', f: 'problems' };
  const SYC_IC = { ok: '✓', warn: '!', fail: '✗', off: '–' }, SYC_ORD = { fail: 0, warn: 1, off: 2, ok: 3 };
  const SYC_KIND = [['routine', 'Routines (scheduled tasks)'], ['skill', 'Skills'], ['agent', 'Agents'], ['connector', 'Connectors & data feeds']];
  function scLoad() {
    if (SYC.st !== 'idle') return; SYC.st = 'loading';
    (async () => {
      try {
        const db = window.claude && window.claude.use ? await window.claude.use('db') : null;
        if (!db) throw new Error('no db');
        db.collection('system_check').doc('latest').onSnapshot(sn => { SYC.doc = sn && sn.exists ? JSON.parse(JSON.stringify(sn.data())) : null; SYC.st = 'ok'; scRe(); }, () => { SYC.st = 'err'; SYC.err = 'Could not read the system check.'; scRe(); });
      } catch (e) { SYC.st = 'err'; SYC.err = 'The system check is kept in this page’s database; open the page on claude.ai to see it.'; scRe(); }
    })();
  }
  function scRe() { const h = location.hash || ''; if (h.startsWith('#routines')) renderRoutines(); }
  function scItems() {
    const d = SYC.doc || {}, chk = rtMs(d.checked_at) || 0, out = arr(d.items).map(x => ({ ...x, live: '' }));
    const byId = new Map(out.filter(x => x.trigger_id).map(x => [x.trigger_id, x]));
    if (RTL.st === 'ok') RTL.tasks.forEach(t => {
      const h = rtHealth(t, null), x = byId.get(t.id), lr = t.last_run, fired = rtMs(lr && lr.fired_at) || 0;
      if (!x) { out.push({ kind: 'routine', name: t.name, status: h[0] === 'fail' || h[0] === 'miss' ? 'fail' : t.enabled ? 'warn' : 'off', headline: t.enabled ? 'New since the last check — not checked yet' : 'Paused', problems: h[2] ? [h[1] + ': ' + h[2]] : [], fix: '', live: 'live' }); return; }
      if (!t.enabled && x.status !== 'off') { x.status = 'off'; x.live = 'Paused since the check'; }
      if (h[0] === 'fail' || h[0] === 'miss') { x.status = 'fail'; x.live = h[1] + (h[2] ? ': ' + h[2] : ''); }
      else if (fired > chk + 60e3 && t.enabled) x.live = 'Ran again ' + rtET(fired) + ' (after this check)';
      x.session = lr && lr.session_id;
    });
    return out;
  }
  function scDot() { if (SYC.st === 'idle') scLoad(); const xs = scItems(); return xs.some(x => x.status === 'fail') ? 'stale' : xs.some(x => x.status === 'warn') ? 'aging' : 'fresh'; }
  function scView() {
    scLoad(); rtLoad();
    if (SYC.st === 'err') return `<section class="panel">${none(esc(SYC.err))}</section>`;
    if (!SYC.doc) return `<section class="panel">${none(SYC.st === 'ok' ? 'No system check has been written yet.' : 'Loading…')}</section>`;
    const xs = scItems(), c = k => xs.filter(x => x.status === k).length;
    const show = SYC.f === 'problems' ? xs.filter(x => x.status === 'fail' || x.status === 'warn') : xs;
    const row = x => `<details class="sc-row sc-${esc(x.status)}"${x.status === 'fail' && SYC.f === 'problems' ? ' open' : ''}><summary><span class="sc-ic" aria-label="${esc(x.status)}">${SYC_IC[x.status] || '?'}</span><span class="sc-nm">${esc(x.name)}</span><span class="sc-hd">${esc(x.headline || '')}</span></summary>` +
      `<div class="sc-det">${x.live ? `<div><span class="chip ${x.status === 'fail' ? 's-negative' : 'out'}">live</span> ${esc(x.live)}</div>` : ''}` +
      (arr(x.problems).length ? `<ul>${arr(x.problems).map(p => `<li>${esc(p)}</li>`).join('')}</ul>` : (x.status === 'ok' ? '<p class="sub">No problems found.</p>' : '')) +
      (x.fix ? `<div class="sc-fix"><b>Fix:</b> ${esc(x.fix)}</div>` : '') +
      (x.session ? `<div class="sub"><a class="ext" href="https://claude.ai/code/session_${esc(String(x.session).replace(/^cse_/, ''))}" target="_blank" rel="noopener">Last run log →</a></div>` : '') + `</div></details>`;
    const grp = SYC_KIND.map(([k, l]) => { const g = show.filter(x => (x.kind || 'routine') === k).sort((a, b) => (SYC_ORD[a.status] - SYC_ORD[b.status]) || String(a.name).localeCompare(String(b.name))); return g.length ? `<div class="sc-grp"><h3>${esc(l)} <span class="sub">${g.length}</span></h3>${g.map(row).join('')}</div>` : ''; }).join('');
    return `<section class="panel" id="rt-check"><div class="panel-h"><h2>System check</h2><span class="muted">Checked ${esc(rtET(rtMs(SYC.doc.checked_at)))}${SYC.doc.checked_by ? ' · ' + esc(SYC.doc.checked_by) : ''}${RTL.st === 'ok' ? ' · live routine status overlaid' : ''}</span></div>` +
      `<p class="sub" style="margin:0">Every routine, skill, agent and data feed with a ✓ or ✗. Click a row for the problem and the fix. ${esc(SYC.doc.note || '')}</p>` +
      `<div class="summary"><div class="stat"><span class="v c-pos">${c('ok')}</span><span class="l">✓ Working</span></div><div class="stat"><span class="v c-neg">${c('fail')}</span><span class="l">✗ Broken</span></div><div class="stat"><span class="v">${c('warn')}</span><span class="l">! Needs a look</span></div><div class="stat"><span class="v">${c('off')}</span><span class="l">Paused</span></div></div>` +
      `<div class="ctl"><div class="seg" aria-label="Show">${[['problems', 'Problems only'], ['all', 'Everything']].map(([k, l]) => `<button type="button" data-scf="${k}" aria-pressed="${SYC.f === k}">${l}</button>`).join('')}</div></div>` +
      (grp || none('Nothing to show.')) + `</section>`;
  }
  document.addEventListener('click', e => { const b = e.target.closest && e.target.closest('[data-scf]'); if (b) { SYC.f = b.dataset.scf; renderRoutines(); } });

"""


def patch(path):
    s = open(path, encoding="utf-8").read()
    if MARKER in s:
        print(f"{path}: already patched"); return
    for old, new in [(NAV_OLD, NAV_NEW), (CUR_OLD, CUR_NEW), (BODY_OLD, BODY_NEW), (ANCHOR, JS + ANCHOR)]:
        if s.count(old) != 1:
            sys.exit(f"{path}: anchor not found exactly once: {old[:60]!r}")
        s = s.replace(old, new)
    if path.endswith(".js"):
        css = path[:-3] + ".css"
        c = open(css, encoding="utf-8").read()
        if MARKER not in c:
            open(css, "w", encoding="utf-8").write(c + CSS)
    else:
        i = s.find("</style>"); i = s.find("</style>", i + 1)
        s = s[:i] + CSS + s[i:]
    open(path, "w", encoding="utf-8").write(s)
    print(f"{path}: patched")


if __name__ == "__main__":
    for f in sys.argv[1:]:
        patch(f)
