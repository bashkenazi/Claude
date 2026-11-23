#!/usr/bin/env python3
"""AI › Thesis by tenet: sentiment chips show how many datapoints each level has (for the tenets/dates in view),
and each tenet says which picked levels it has none of. Requires tenet-sent-multi v1. Marker "tenet-sent-counts v1"."""
import sys
JS, CSS = 'tabs.js', 'tabs.css'
js = open(JS).read(); css = open(CSS).read()
if 'tenet-sent-counts v1' in js: print('already applied'); sys.exit(0)
assert 'tenet-sent-multi v1' in js
def rep(s, old, new):
    assert s.count(old) == 1, ('anchor', old[:80], s.count(old)); return s.replace(old, new)

# date-only pass (ignores sentiment) for chip counts
js = rep(js, "  function tnPass(d, asOf) {",
         "  const tnLvl = d => Math.max(-2, Math.min(2, Math.round(tnScore(d)))); /* tenet-sent-counts v1 */\n"
         "  function tnDateOk(d, asOf) { if (!TNF.days) return true; const lim = new Date(asOf); lim.setDate(lim.getDate() - Number(TNF.days)); return !(new Date(d.date) < lim); }\n"
         "  function tnPass(d, asOf) {")
# counts per level across the tenets in view
js = rep(js, "    const bar = `<div class=\"tn-bar\" role=\"group\" aria-label=\"Datapoint filters\">` +",
         "    const inView = TS.filter(t => !TNF.tenet || t.key === TNF.tenet).flatMap(t => arr(t.dps)).filter(d => tnDateOk(d, asOf));\n"
         "    const lvN = v => inView.filter(d => tnLvl(d) === v).length;\n"
         "    const bar = `<div class=\"tn-bar\" role=\"group\" aria-label=\"Datapoint filters\">` +")
js = rep(js, "title=\"${esc(l)}\">${tnDots(v)}${esc(l)}</button>`",
         "title=\"${esc(l)}: ${lvN(v)} datapoints in view\">${tnDots(v)}${esc(l)} <span class=\"tn-sn\">${lvN(v)}</span></button>`")
# per-tenet note on picked levels with no datapoints
js = rep(js, "`<h3>Datapoints <span class=\"muted\">${DP.length} of ${pass.length}${pass.length !== all.length ? ` matching (${all.length} total)` : ''}</span></h3>` +",
         "`<h3>Datapoints <span class=\"muted\">${DP.length} of ${pass.length}${pass.length !== all.length ? ` matching (${all.length} total)` : ''}</span></h3>` +\n"
         "        (() => { const miss = TNF.sent.filter(v => !all.some(d => tnLvl(d) === v && tnDateOk(d, asOf))); return miss.length ? `<p class=\"sub tn-miss\">No ${miss.map(v => (TN_SENT.find(x => x[0] === v) || [, ''])[1].toLowerCase()).join(' or ')} datapoints in this tenet${TNF.days ? ' for these dates' : ''}.</p>` : ''; })() +")
css += """
/* tenet-sent-counts v1 */
.tn-sn { font-variant-numeric: tabular-nums; color: var(--muted); font-weight: 400; }
.tn-sb.on .tn-sn { color: var(--ink-2); }
.tn-miss { margin: -4px 0 8px; }
"""
open(JS, 'w').write(js); open(CSS, 'w').write(css); print('applied')
