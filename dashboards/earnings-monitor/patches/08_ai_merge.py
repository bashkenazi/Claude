#!/usr/bin/env python3
"""Merge the AI and AI thesis tabs into one AI tab (Bobby, 2026-11-10).
The AI tab gets a switch at the top: Thesis (overview) · Thesis by tenet · Models & data (the old AI tab).
The 'AI thesis' nav link goes; its open-updates count moves onto the AI link. Old #thesis and #thesis/tenets
links redirect to #ai in the matching mode; #ai/<section> links open Models & data. The mode is remembered per viewer.
Usage: 08_ai_merge.py FILE [FILE ...]  (edits in place; pass the combined tabs.css+tabs.js and template.html,
or the single published page). Idempotent: files already carrying the marker are left alone."""
import re
import sys

MARKER = "/* ai-merge v1 */"

JS_DEFS = r"""  """ + MARKER + r"""
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
"""

REPL = [
    # nav: one AI link carrying the thesis count
    (re.compile(r'<a href="#ai">AI</a>\s*<a href="#thesis">AI thesis (<span id="th-count" class="sub"></span>)</a>'),
     r'<a href="#ai">AI \1</a>'),
    # views: switch + models & data + thesis, all under data-view="ai"
    (re.compile(r'<div class="view" data-view="ai" id="v-ai"></div>\s*<div class="view" data-view="thesis" id="v-thesis"></div>'),
     '<div class="view" data-view="ai" id="v-aimode"></div>\n<div class="view" data-view="ai" id="v-ai"></div>\n<div class="view" data-view="ai" id="v-thesis"></div>'),
    # JS: mode helpers before the thesis view code
    ("  const thView = () => {", JS_DEFS + "  const thView = () => {"),
    # the thesis no longer draws its own Overview / By tenet switch
    ("    h += thViewSeg();\n", ""),
    # live thesis updates repaint only when the thesis is showing
    ("const thPaint = () => { if ((location.hash || '').startsWith('#thesis')) renderThesis(); };",
     "const thPaint = () => { if (/^#(ai|thesis)(\\/|$)/.test(location.hash || '') && aiMode() !== 'data') renderThesis(); };"),
    # in-page anchors point at the AI tab
    ('<a href="#thesis" data-th=', '<a href="#ai" data-th='),
    ('<a href="#thesis" data-tn=', '<a href="#ai" data-tn='),
    # router: redirect #thesis, route #ai/<section> to Models & data
    ("if (v === 'twitter') v = 'x';",
     "if (v === 'twitter') v = 'x'; if (v === 'thesis') { aiModeSet((location.hash.split('/')[1] || '') === 'tenets' ? 'tenets' : 'overview'); history.replaceState(null, '', '#ai'); v = 'ai'; } else if (v === 'ai' && (location.hash.split('/')[1] || '')) aiModeSet('data');"),
    ("    if (v === 'ai' && done[v]) { renderAI(); }\n", "    if (v === 'ai') { aiShow(); done.ai = 1; }\n"),
    ("    if (v === 'thesis' && done[v]) { renderThesis(); }\n", ""),
    ("ai: renderAI, thesis: renderThesis,", "ai: () => {}, thesis: () => {},"),
    # CSS
    ("#v-thesis section[id] {", ".view[hidden] { display: none !important; }\n#v-aimode { margin-bottom: -6px; }\n.ai-mode { align-self: flex-start; flex-wrap: wrap; }\n#v-thesis section[id] {"),
]


def main(paths):
    texts = {p: open(p, encoding="utf-8").read() for p in paths}
    if any(MARKER in t for t in texts.values()):
        print("already present"); return 0
    hits = [0] * len(REPL)
    for p, s in texts.items():
        for i, (old, new) in enumerate(REPL):
            if isinstance(old, re.Pattern):
                s, n = old.subn(new, s, count=1)
            else:
                n = s.count(old)
                if n > 1 and i != 5 and i != 6:
                    print(f"anchor {i} not unique in {p}", file=sys.stderr); return 2
                s = s.replace(old, new)
            hits[i] += n
        texts[p] = s
    miss = [i for i, h in enumerate(hits) if not h]
    if miss:
        print("anchors missing:", miss, file=sys.stderr); return 2
    for p, s in texts.items():
        open(p, "w", encoding="utf-8").write(s)
    print("merged", hits); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
