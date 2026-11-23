#!/usr/bin/env python3
"""AI › Thesis by tenet: render a tenet's extra tables (tenet.tables = [{title, cols, rows, note, dir_col}]).
Rows are arrays or {c: [...], b: bold, h: section header}. dir_col cells starting with ▲/▼/■ are coloured.
Marker "tenet-tables v1"."""
import sys
JS, CSS = 'tabs.js', 'tabs.css'
js = open(JS).read(); css = open(CSS).read()
if 'tenet-tables v1' in js: print('already applied'); sys.exit(0)
old = "        (FC.length ? `<h3>Fact check</h3>"
assert js.count(old) == 1
js = js.replace(old, "        arr(t.tables).map(X => { /* tenet-tables v1 */ const dc = X.dir_col; const cell = (c, i) => { const s = String(c == null ? '' : c); const cls = i === dc ? (s.startsWith('▲') ? 'tn-dir up' : s.startsWith('▼') ? 'tn-dir dn' : s.startsWith('■') ? 'tn-dir fl' : '') : ''; return `<td class=\"${i > 0 ? 'wrap' : ''} ${cls}\">${esc(s)}</td>`; };\n"
  "          return `<h3>${esc(X.title || '')}</h3><div class=\"tbl-wrap\"><table class=\"dt tn-x\"><thead><tr>${arr(X.cols).map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${arr(X.rows).map(r => { const R = Array.isArray(r) ? { c: r } : r; return R.h ? `<tr class=\"tn-xh\"><td colspan=\"${arr(X.cols).length}\">${esc(R.c[0])}</td></tr>` : `<tr class=\"${R.b ? 'tn-xb' : ''}\">${arr(R.c).map(cell).join('')}</tr>`; }).join('')}</tbody></table></div>${X.note ? `<p class=\"sub\">${esc(X.note)}</p>` : ''}`; }).join('') +\n" + old, 1)
css += """
/* tenet-tables v1 */
table.tn-x td { white-space: normal; vertical-align: top; }
table.tn-x td.wrap { min-width: 90px; max-width: 420px; }
table.tn-x td:first-child { min-width: 160px; }
table.tn-x tr.tn-xh td { font-weight: 700; background: var(--surface-2); color: var(--ink-2); font-size: 11.5px; text-transform: uppercase; letter-spacing: .04em; }
table.tn-x tr.tn-xb td { font-weight: 600; }
table.tn-x td.tn-dir { white-space: nowrap; font-weight: 600; }
table.tn-x td.tn-dir.up { color: var(--pos); } table.tn-x td.tn-dir.dn { color: var(--neg); } table.tn-x td.tn-dir.fl { color: var(--ink-2); }
"""
open(JS, 'w').write(js); open(CSS, 'w').write(css); print('applied')
