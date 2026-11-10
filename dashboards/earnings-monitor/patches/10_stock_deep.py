#!/usr/bin/env python3
"""Stocks page: company deep-dive tabs (Bobby, 2026-11-10). A doc in page db collection 'stock_deep' (doc id = ticker,
built from a Notion deep-dive page by store/stock_deep/build_from_notion.py) adds its tabs (for ORCL: Sites & build,
Financing & guarantees, RPO & contracts) after Thesis. Each tab renders the Notion section (tables, lists, toggles)
plus a live feed of the ticker's Supabase datapoints matching the tab, flagging those newer than the Notion page.
Usage: 10_stock_deep.py FILE [FILE ...] (in place). Idempotent."""
import sys

MARKER = "/* stock-deep v1 */"
JS = r"""  """ + MARKER + r"""
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
"""

CSS = """.sd h3 { margin-top: 10px; }
.sk-main, .sk-wrap > * { min-width: 0; }
.sd .panel-h a.ext { white-space: normal; overflow-wrap: anywhere; }
.sd .sd-p { margin: 0; font-size: 13px; color: var(--ink-2); max-width: 120ch; }
.sd .sd-ul { font-size: 13px; max-width: 120ch; } .sd .sd-d1 { margin-left: 18px; } .sd .sd-d2 { margin-left: 36px; } .sd .sd-d3 { margin-left: 54px; }
table.sd-t td { white-space: normal; min-width: 90px; max-width: 360px; font-size: 12px; line-height: 1.4; }
table.sd-t td:first-child { min-width: 150px; }
.sd-tog > summary { font-size: 13px; text-transform: none; letter-spacing: 0; color: var(--ink); font-weight: 650; }
.sd-tog .sd-in { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
"""

REPL = [
    ("  function renderStocks() {\n", JS + "  function renderStocks() {\n    sdStart();\n"),
    ("['insiders', 'Questions & insiders']];", "['insiders', 'Questions & insiders']]; sdTabs(cur).forEach((x, i) => tabs.splice(2 + i, 0, x));"),
    ("    if (sub === 'earnings') { $('sk-body').innerHTML = earningsView(cur); return; }",
     "    if (String(sub).startsWith('dd-')) { sdView(cur, sub, $('sk-body')); return; }\n    if (sub === 'earnings') { $('sk-body').innerHTML = earningsView(cur); return; }"),
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
