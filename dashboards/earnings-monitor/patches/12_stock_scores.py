#!/usr/bin/env python3
"""Stocks: sortable, filterable evidence scores (Bobby, 2026-11-13: "let's make it so I can sort and filter").
- Sidebar: Sort by (sector default, vs universe, index, 30-day change, Growth, Margins, Competition, Risk,
  evidence in 90 days, today's move) with a direction toggle; filters (above/below universe, rising/falling,
  no index) and a minimum-evidence filter. Sorted lists drop the sector headers and show the sorted metric.
- With no company picked (#stocks), the body is a ranking table with every score input as a sortable column,
  using the same filters, plus a "How the score works" panel.
Usage: 12_stock_scores.py FILE [FILE ...] (in place). Idempotent."""
import re
import sys

MARKER = "/* stock-scores v1 */"

HELPERS = r"""    """ + MARKER + r"""
    const SKM = c => { const I = idxOf(c); if (!I) return null; const n = I.c.length - 1, mv = MV.get(String(c.t).toUpperCase()) || MV.get(String(c.bbg).toUpperCase()); return { x: I.x[n], c: I.c[n], d30: I.c[n] - I.c[Math.max(0, n - 4)], g: I.g[n], m: I.m[n], k: I.k[n], r: I.r[n], e: I.e[n], cnt: I.count, mv: mv ? +mv.c : null }; };
    const SK_COLS = [['x', 'vs universe', 'Composite index minus the same index on every name: 0 = as positive as the average name'], ['c', 'Index', 'Composite Evidence Index, −100 to +100'], ['d30', '30d Δ', 'Change in the index over the last 4 weeks'], ['g', 'Growth', 'Growth pillar (40% of the index)'], ['m', 'Margins', 'Margins pillar (25%)'], ['k', 'Competition', 'Competition pillar (20%)'], ['r', 'Risk', 'Risk pillar (15%)'], ['e', 'Evidence 90d', 'Datapoints in the last 90 days that feed the index'], ['mv', 'Today %', 'Today’s price move']];
    const skVal = (c, k) => { const m = SKM(c); return m ? m[k] : null; };
    const skPass = c => { const m = SKM(c); if (fs.flt === 'noidx') return !m; if (fs.flt && !m) return false;
      if (fs.flt === 'above' && !(m.x > 0)) return false; if (fs.flt === 'below' && !(m.x < 0)) return false;
      if (fs.flt === 'rising' && !(m.d30 > 0)) return false; if (fs.flt === 'falling' && !(m.d30 < 0)) return false;
      if (fs.minN && !(m && m.e >= +fs.minN)) return false; return true; };
    const skCmp = (a, b) => { const va = skVal(a, fs.sort), vb = skVal(b, fs.sort); if (va == null && vb == null) return a.t.localeCompare(b.t); if (va == null) return 1; if (vb == null) return -1; return fs.dir === 'asc' ? va - vb : vb - va; };
"""

NAV_CTL = r"""
      <div class="sk-ctl2"><label>Sort <select id="sk-sort"><option value=""${!fs.sort ? ' selected' : ''}>Sector</option>${SK_COLS.map(([k, l]) => `<option value="${k}"${fs.sort === k ? ' selected' : ''}>${l}</option>`).join('')}</select></label>${fs.sort ? `<button type="button" class="nav-reset" id="sk-dir" title="Flip the order">${fs.dir === 'asc' ? '↑ low first' : '↓ high first'}</button>` : ''}</div>
      <div class="sk-ctl2"><select id="sk-flt" aria-label="Filter by score"><option value="">All scores</option><option value="above"${fs.flt === 'above' ? ' selected' : ''}>Above universe</option><option value="below"${fs.flt === 'below' ? ' selected' : ''}>Below universe</option><option value="rising"${fs.flt === 'rising' ? ' selected' : ''}>Rising (30d)</option><option value="falling"${fs.flt === 'falling' ? ' selected' : ''}>Falling (30d)</option><option value="noidx"${fs.flt === 'noidx' ? ' selected' : ''}>No index yet</option></select><select id="sk-min" aria-label="Minimum evidence"><option value="">Any evidence</option>${[5, 10, 25, 50].map(v => `<option value="${v}"${fs.minN === String(v) ? ' selected' : ''}>${v}+ in 90d</option>`).join('')}</select></div>
      <a class="sk-rank" href="#stocks">Ranking table · how the score works</a>"""

TABLE = r"""if (!cur) {
      const rows = ST.filter(c => (!fs.tier || String(c.tier) === fs.tier) && (!fs.sec || c.sector === fs.sec) && (!fs.sub || arr(c.subs).includes(fs.sub)) && (!fs.q || `${c.t} ${c.name} ${c.sub}`.toLowerCase().includes(fs.q)) && skPass(c));
      const sk = fs.sort || 'x', dir = fs.sort ? fs.dir : 'desc', S2 = Object.assign({}, fs, { sort: sk, dir });
      rows.sort((a, b) => { const va = skVal(a, sk), vb = skVal(b, sk); if (va == null && vb == null) return a.t.localeCompare(b.t); if (va == null) return 1; if (vb == null) return -1; return dir === 'asc' ? va - vb : vb - va; });
      const cell = (v, k) => v == null ? '<td class="n muted">–</td>' : `<td class="n ${['x', 'd30', 'mv'].includes(k) ? (v >= 0 ? 'up' : 'dn') : ''}">${k === 'e' ? v : k === 'mv' ? sgn(v) + '%' : sgn(v)}</td>`;
      body = `<section class="panel"><div class="panel-h"><h2>Evidence scores</h2><span class="muted">${rows.length} names · click a header to sort · filters on the left apply</span></div>
        <div class="tbl-wrap"><table class="dt sk-rt"><thead><tr><th>Company</th><th>Tier</th><th>Subsector</th>${SK_COLS.map(([k, l, t]) => `<th class="n" data-sk="${k}" title="${esc(t)}" aria-sort="${sk === k ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}">${l}</th>`).join('')}<th class="n" title="All datapoints on file">Total</th></tr></thead>
        <tbody>${rows.map(c => { const m = SKM(c) || {}; return `<tr><td><a href="#stocks/${encodeURIComponent(c.key)}/debate"><b>${esc(c.t)}</b></a> <span class="sub">${esc(c.name)}</span></td><td>T${esc(c.tier)}</td><td class="sub">${esc(arr(c.subs)[0] || c.sector)}</td>${SK_COLS.map(([k]) => cell(m[k] ?? null, k)).join('')}<td class="n">${m.cnt ?? '–'}</td></tr>`; }).join('')}</tbody></table></div></section>
        <section class="panel"><details class="sk-how"><summary>How the score works</summary><div class="method">
        <p><b>Inputs:</b> every Supabase datapoint (research_evidence) on the company whose category is Growth or TAM, Margins, Competition or Risk. Other categories are counted in Total but do not move the score. A company needs 5+ scored datapoints to get an index.</p>
        <ul><li><b>Signal per datapoint</b> = direction (positive +1, negative −1, mixed 0) × confidence (high 1.0, medium 0.75, low 0.5). Size of the news is not scored yet.</li>
        <li><b>Weight</b> = source reliability × recency. Reliability: management, filings and channel checks / independent research 1.0; sell-side 0.6; news, Substack and email 0.5; Twitter 0.3; Reddit 0.2; anything inferred 0.3. Recency halves every 90 days.</li>
        <li><b>Pillar score</b> = weighted average signal, shrunk toward 0 when there is little evidence (× W ÷ (W + 5), W = sum of weights), so a name with a handful of positives cannot score +100.</li>
        <li><b>Index</b> = Growth 40% + Margins 25% + Competition 20% + Risk 15%, × 100 → −100 to +100.</li>
        <li><b>vs universe</b> = the index minus the same calculation on every datapoint in the universe that week. About 75% of stored datapoints are positive (sell-side skew), so the raw index runs high; 0 here means "as positive as the average name".</li>
        <li><b>30d Δ</b> = the index now minus four weeks ago. <b>Evidence 90d</b> = datapoints in the last 90 days.</li></ul>
        <p class="sub">Built nightly from research_evidence by store/build_datapoints.py (Composite Evidence Index v3, after your Hex "Composite Index v2"). Known gaps: no magnitude, duplicate reports of one event each count, and price/valuation are not inputs.</p></div></details></section>`;
    } else if (false) """

CSS = """.sk-ctl2 { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; font-size: 12.5px; }
.sk-ctl2 label { display: inline-flex; gap: 6px; align-items: center; color: var(--muted); }
.sk-ctl2 select { min-width: 0; flex: 1 1 auto; }
.sk-rank { font-size: 12px; color: var(--accent); text-decoration: none; } .sk-rank:hover { text-decoration: underline; }
.sk-list a .sk-m { font-size: 11.5px; }
table.sk-rt th[data-sk] { cursor: pointer; user-select: none; } table.sk-rt th[aria-sort="ascending"]::after { content: " ▲"; } table.sk-rt th[aria-sort="descending"]::after { content: " ▼"; }
table.sk-rt td:first-child { white-space: nowrap; }
.sk-how > summary { text-transform: none; letter-spacing: 0; font-size: 13px; color: var(--accent); }
"""

LIST_RX = re.compile(r"    const list = ST\.filter\(c => \(!fs\.tier \|\| String\(c\.tier\) === fs\.tier\).*?\|\| a\.t\.localeCompare\(b\.t\)\);\n", re.S)
LIST_NEW = ("    const list = ST.filter(c => (!fs.tier || String(c.tier) === fs.tier) && (!fs.sec || c.sector === fs.sec) && (!fs.sub || arr(c.subs).includes(fs.sub)) && (!fs.q || `${c.t} ${c.name} ${c.sub}`.toLowerCase().includes(fs.q)) && skPass(c))\n"
            "      .sort((a, b) => fs.sort ? skCmp(a, b) : SO.indexOf(a.sector) - SO.indexOf(b.sector) || String(arr(a.subs)[0]).localeCompare(String(arr(b.subs)[0])) || (a.tier || 9) - (b.tier || 9) || a.t.localeCompare(b.t));\n")

REPL = [
    ("    if (!host.__st) host.__st = { q: '', tier: '', sec: '', sub: '' };\n    const fs = host.__st;\n",
     "    if (!host.__st) host.__st = { q: '', tier: '', sec: '', sub: '', sort: '', dir: 'desc', flt: '', minN: '' };\n    const fs = host.__st;\n" + HELPERS),
    (LIST_RX, LIST_NEW),
    # sidebar controls after the subsector select
    ("${subsAll.map(x => `<option${x === fs.sub ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select>",
     "${subsAll.map(x => `<option${x === fs.sub ? ' selected' : ''}>${esc(x)}</option>`).join('')}</select>" + NAV_CTL),
    # sorted lists: no sector headers; show the sorted metric
    ("hdr = i === 0 || (arr(list[i - 1].subs)[0] || list[i - 1].sector) !== sb ?", "hdr = !fs.sort && (i === 0 || (arr(list[i - 1].subs)[0] || list[i - 1].sector) !== sb) ?"),
    ("${I ? `<span class=\"mono ${I.x[n] >= 0 ? 'c-pos' : 'c-neg'}\" title=\"Composite vs universe\">${sgn(I.x[n])}</span>` : ''}</a>`; }).join('')}</div></div>`;",
     "${fs.sort && fs.sort !== 'x' ? (() => { const v = skVal(c, fs.sort); return v == null ? '' : `<span class=\"mono sk-m ${['d30', 'mv'].includes(fs.sort) ? (v >= 0 ? 'c-pos' : 'c-neg') : ''}\" title=\"${esc((SK_COLS.find(x => x[0] === fs.sort) || [])[1] || '')}\">${fs.sort === 'e' ? v : sgn(v) + (fs.sort === 'mv' ? '%' : '')}</span>`; })() : I ? `<span class=\"mono ${I.x[n] >= 0 ? 'c-pos' : 'c-neg'}\" title=\"Composite vs universe\">${sgn(I.x[n])}</span>` : ''}</a>`; }).join('')}</div></div>`;"),
    ("    if (!cur) body = `<section class=\"panel\"><h2>Pick a company</h2>", "    " + TABLE + "body = `<section class=\"panel\"><h2>Pick a company</h2>"),
    ("    $('sk-sub').addEventListener('change', e => { fs.sub = e.target.value; renderStocks(); });\n",
     "    $('sk-sub').addEventListener('change', e => { fs.sub = e.target.value; renderStocks(); });\n"
     "    $('sk-sort').addEventListener('change', e => { fs.sort = e.target.value; fs.dir = 'desc'; renderStocks(); });\n"
     "    if ($('sk-dir')) $('sk-dir').addEventListener('click', () => { fs.dir = fs.dir === 'asc' ? 'desc' : 'asc'; renderStocks(); });\n"
     "    $('sk-flt').addEventListener('change', e => { fs.flt = e.target.value; renderStocks(); });\n"
     "    $('sk-min').addEventListener('change', e => { fs.minN = e.target.value; renderStocks(); });\n"
     "    host.querySelectorAll('table.sk-rt th[data-sk]').forEach(th => th.addEventListener('click', () => { const k = th.dataset.sk, curS = fs.sort || 'x'; fs.dir = curS === k && (fs.sort ? fs.dir : 'desc') === 'desc' ? 'asc' : 'desc'; fs.sort = k; renderStocks(); }));\n"),
    ("/* Thesis tab */", CSS + "/* Thesis tab */"),
]


def main(paths):
    texts = {p: open(p, encoding="utf-8").read() for p in paths}
    if any(MARKER in t for t in texts.values()):
        print("already present"); return 0
    hits = [0] * len(REPL)
    for p, s in texts.items():
        for i, (old, new) in enumerate(REPL):
            if isinstance(old, re.Pattern):
                s, n = old.subn(lambda m: new, s, count=1)
            else:
                n = s.count(old)
                if n > 1: print(f"anchor {i} not unique in {p}", file=sys.stderr); return 2
                s = s.replace(old, new)
            hits[i] += n
        texts[p] = s
    if not all(hits): print("anchors missing", hits, file=sys.stderr); return 2
    for p, s in texts.items(): open(p, "w", encoding="utf-8").write(s)
    print("added", hits); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
