#!/usr/bin/env python3
"""AI › Thesis by tenet: number each tenet ("Tenet 1"...) and show risks as "Risk 1"... Label comes from the doc
(tenet.label, e.g. "Tenet 1" / "Risk 1"); otherwise tenets with kind "risk" are numbered Risk n, the rest Tenet n.
Marker "tenet-numbers v1"."""
import sys
JS, CSS = 'tabs.js', 'tabs.css'
js = open(JS).read(); css = open(CSS).read()
if 'tenet-numbers v1' in js: print('already applied'); sys.exit(0)
def rep(s, old, new, n=1):
    assert s.count(old) == n, ('anchor', old[:80], s.count(old)); return s.replace(old, new)
js = rep(js, "    const TS = arr(D2.tenets).slice().sort((a, b) => (a.sort || 0) - (b.sort || 0));\n    const asOf = String(D2.updated_at",
         "    const TS = arr(D2.tenets).slice().sort((a, b) => (a.sort || 0) - (b.sort || 0)); /* tenet-numbers v1 */\n"
         "    { let ti = 0, ri = 0; TS.forEach(t => { t._lab = t.label || (t.kind === 'risk' ? 'Risk ' + (++ri) : 'Tenet ' + (++ti)); }); }\n"
         "    const tnL = t => `<span class=\"tn-num${/^risk/i.test(t._lab) ? ' risk' : ''}\">${esc(t._lab)}</span> `;\n"
         "    const asOf = String(D2.updated_at")
js = rep(js, "${TNF.tenet === t.key ? ' selected' : ''}>${esc(t.title)}</option>`", "${TNF.tenet === t.key ? ' selected' : ''}>${esc(t._lab)}: ${esc(t.title)}</option>`")
js = rep(js, "<span class=\"chips\">${thChip(t.status)}</span><b>${esc(t.title)}</b>", "<span class=\"chips\">${thChip(t.status)}</span><b>${tnL(t)}${esc(t.title)}</b>")
js = rep(js, "<div class=\"panel-h\"><h2>${esc(t.title)}</h2><span class=\"chips\">${thChip(t.status)}</span></div>", "<div class=\"panel-h\"><h2>${tnL(t)}${esc(t.title)}</h2><span class=\"chips\">${thChip(t.status)}</span></div>")
css += """
/* tenet-numbers v1 */
.tn-num { display: inline-block; font-size: .78em; font-weight: 700; letter-spacing: .02em; padding: 1px 7px; margin-right: 4px; border-radius: 4px; background: var(--surface-2); color: var(--ink-2); vertical-align: 2px; white-space: nowrap; }
.tn-num.risk { background: var(--neg-wash); color: var(--neg); }
"""
open(JS, 'w').write(js); open(CSS, 'w').write(css); print('applied')
