#!/usr/bin/env python3
"""Update button on every tab (Bobby, 2026-11-13: "shouldn't we have a refresh button on all pages if I want
everything updated"). Sits in the masthead, so it is on every tab. Three choices, each firing Bobby's own scheduled
tasks through the Claude Code Remote connector (as the viewer):
  - Refresh this tab: the Tech Daily refresh task, scoped to the open tab (other tabs carried over).
  - Refresh all tabs: the Tech Daily refresh task, full build now.
  - Run all sources, then refresh: fires the digest tasks (Tech Specialist, SemiAnalysis, Research, sell-side,
    Twitter, Earnings Review), then the refresh task, told to wait for them and the Output Sweep before building.
Shows whether a refresh is already running (and blocks a second one), and polls until it finishes. Live parts of the
open tab re-render at once. Needs capability mcp server "Claude Code Remote" tools fire_trigger + list_triggers;
without them the button explains and does nothing.
Usage: 11_refresh_button.py FILE [FILE ...] (in place). Idempotent."""
import sys

MARKER = "/* refresh-button v1 */"

JS = r"""  """ + MARKER + r"""
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
  document.addEventListener('click', e => { if (RF.open && !e.target.closest('#rf')) { RF.open = false; rfPaint(); } });
  document.addEventListener('keydown', e => { if (RF.open && e.key === 'Escape') { RF.open = false; rfPaint(); } });
  setTimeout(rfPaint, 0);
"""

CSS = """/* Update button */
.rf { position: relative; }
.rf-btn { font: inherit; font-size: 12.5px; border: 1px solid var(--rule-2); background: var(--surface); color: var(--ink); border-radius: 6px; padding: 4px 10px; cursor: pointer; white-space: nowrap; }
.rf-btn:hover { background: var(--surface-2); } .rf-btn.on { border-color: var(--accent); color: var(--accent); }
.rf-pop { position: absolute; right: 0; top: calc(100% + 6px); z-index: 40; width: min(340px, calc(100vw - 32px)); background: var(--surface); border: 1px solid var(--rule-2); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,.16); padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.rf-pop .rf-h { margin: 2px 4px 4px; font-size: 11px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 650; }
.rf-pop button { all: unset; display: flex; flex-direction: column; gap: 2px; padding: 7px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--ink); }
.rf-pop button span { font-size: 12px; color: var(--muted); }
.rf-pop button:hover:not([disabled]), .rf-pop button:focus-visible { background: var(--surface-2); outline: none; }
.rf-pop button[disabled] { opacity: .45; cursor: default; }
.rf-pop .rf-msg { margin: 4px 6px 2px; font-size: 12px; color: var(--ink-2); }
"""

REPL = [
    ('  <div class="stamp" id="stamp"></div>', '  <div class="stamp" id="stamp"></div>\n  <div class="rf" id="rf"></div>'),
    ("  function show() {", JS + "  function show() {"),
    ("/* Thesis tab */", CSS + "/* Thesis tab */"),
]


def main(paths):
    texts = {p: open(p, encoding="utf-8").read() for p in paths}
    if any(MARKER in t for t in texts.values()):
        print("already present"); return 0
    hits = [0] * len(REPL)
    for p, s in texts.items():
        for i, (old, new) in enumerate(REPL):
            n = s.count(old)
            if n > 1: print(f"anchor {i} not unique in {p}", file=sys.stderr); return 2
            s = s.replace(old, new); hits[i] += n
        texts[p] = s
    if not all(hits): print("anchors missing", hits, file=sys.stderr); return 2
    for p, s in texts.items(): open(p, "w", encoding="utf-8").write(s)
    print("added", hits); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
