#!/usr/bin/env python3
"""AI › Thesis by tenet: sentiment filter becomes multi-select (toggle chips for the five levels; none selected = all).
Idempotent; marker "tenet-sent-multi v1". Run from dashboards/earnings-monitor."""
import sys
JS, CSS = 'tabs.js', 'tabs.css'
js = open(JS).read(); css = open(CSS).read()
if 'tenet-sent-multi v1' in js: print('already applied'); sys.exit(0)

def rep(s, old, new):
    assert s.count(old) == 1, ('anchor', old[:80], s.count(old)); return s.replace(old, new)

# state: sent is an array of levels; migrate old single-select values
js = rep(js, "return Object.assign({ tenet: '', sent: '', days: '', n: '10' }, f); })();",
         "f = Object.assign({ tenet: '', sent: [], days: '', n: '10' }, f); /* tenet-sent-multi v1 */\n"
         "    if (!Array.isArray(f.sent)) f.sent = f.sent === 'g' ? [2, 1] : f.sent === 'r' ? [-1, -2] : f.sent === '' || f.sent == null ? [] : [Number(f.sent)];\n"
         "    return f; })();")
js = rep(js, "const TN_SENT = [['', 'All sentiment'], ['g', 'All supportive (green)'], ['2', '●● Strongly supports'], ['1', '● Supports'], ['0', '● Neutral (blue)'], ['-1', '● Weakens'], ['-2', '●● Strongly weakens'], ['r', 'All weakening (red)']];",
         "const TN_SENT = [[2, 'Strongly supports'], [1, 'Supports'], [0, 'Neutral'], [-1, 'Weakens'], [-2, 'Strongly weakens']];")
js = rep(js, """    const s = tnScore(d), f = TNF.sent;
    if (f === 'g' && !(s > 0)) return false; if (f === 'r' && !(s < 0)) return false;
    if (f !== '' && f !== 'g' && f !== 'r' && s !== Number(f)) return false;""",
         """    const s = tnScore(d), f = TNF.sent;
    if (f.length && !f.includes(Math.max(-2, Math.min(2, Math.round(s))))) return false;""")
js = rep(js, "`<label>Sentiment <select data-tnf=\"sent\">${opt(TN_SENT, TNF.sent)}</select></label>` +",
         "`<span class=\"tn-sent\" role=\"group\" aria-label=\"Sentiment (pick any; none = all)\"><span class=\"tn-sl\">Sentiment</span>${TN_SENT.map(([v, l]) => `<button type=\"button\" class=\"tn-sb${TNF.sent.includes(v) ? ' on' : ''}\" data-tns=\"${v}\" aria-pressed=\"${TNF.sent.includes(v)}\" title=\"${esc(l)}\">${tnDots(v)}${esc(l)}</button>`).join('')}" +
         "${TNF.sent.length ? '<button type=\"button\" class=\"tn-sb tn-sx\" data-tns=\"x\">All</button>' : ''}</span>` +")
js = rep(js, "setTimeout(() => document.querySelectorAll('#v-thesis [data-tnf]').forEach(s => s.addEventListener('change', () => { TNF[s.dataset.tnf] = s.value; tnSave(); renderThesis(); })), 0);",
         "setTimeout(() => { document.querySelectorAll('#v-thesis [data-tnf]').forEach(s => s.addEventListener('change', () => { TNF[s.dataset.tnf] = s.value; tnSave(); renderThesis(); }));\n"
         "      document.querySelectorAll('#v-thesis [data-tns]').forEach(b => b.addEventListener('click', () => { const v = b.dataset.tns; if (v === 'x') TNF.sent = []; else { const n = Number(v); TNF.sent = TNF.sent.includes(n) ? TNF.sent.filter(x => x !== n) : TNF.sent.concat(n); } tnSave(); renderThesis(); })); }, 0);")
css += """
/* tenet-sent-multi v1 */
.tn-sent { display: inline-flex; flex-wrap: wrap; gap: 4px 6px; align-items: center; min-width: 0; max-width: 100%; }
.tn-sl { color: var(--muted); margin-right: 2px; }
.tn-sb { display: inline-flex; align-items: center; gap: 5px; font: inherit; font-size: 12px; padding: 3px 9px; border: 1px solid var(--rule); border-radius: 999px; background: var(--bg); color: var(--ink-2); cursor: pointer; }
.tn-sb:hover { border-color: var(--ink-2); }
.tn-sb.on { background: var(--surface-2); border-color: var(--ink); color: var(--ink); font-weight: 600; }
.tn-sb.tn-sx { color: var(--muted); }
"""
open(JS, 'w').write(js); open(CSS, 'w').write(css); print('applied')
