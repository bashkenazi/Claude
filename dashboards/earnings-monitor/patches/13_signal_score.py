#!/usr/bin/env python3
"""Stocks: backtested Signal score (Bobby, 2026-11-13: "see what's been the most predictive for stock prices, and
change those weights"). Reads page db stock_scores/latest (built by store/signal_score/ from FactSet prices, estimates,
surprises and targets, Insider Score Form 4s and Supabase research_evidence). The Signal score becomes the headline
number in the sidebar and the default sort of the ranking table; its parts (Earnings, Valuation, Insider, Crowding,
Volatility) are sortable columns; the evidence index stays as context. The method panel shows the backtest.
Requires stock-scores v1. Usage: 13_signal_score.py FILE [FILE ...] (in place). Idempotent."""
import sys

MARKER = "/* signal-score v1 */"
NEEDS = "/* stock-scores v1 */"

LOADER = r"""  """ + MARKER + r"""
  const SSC = { doc: null, by: new Map(), started: false };
  function sscStart() {
    if (SSC.started) return; SSC.started = true;
    (window.claude && window.claude.use ? window.claude.use('db') : Promise.resolve(null)).then(db => {
      if (!db) return;
      db.doc('stock_scores/latest').onSnapshot(s => {
        const d = s && s.exists !== false && s.data ? s.data() : null; if (!d) return;
        SSC.doc = JSON.parse(JSON.stringify(d)); SSC.by = new Map(arr(SSC.doc.scores).map(x => [String(x.t).toUpperCase(), x]));
        if ((location.hash || '').startsWith('#stocks')) renderStocks();
      }, () => {});
    }).catch(() => {});
  }
"""

HELPERS_OLD = "    const SKM = c => { const I = idxOf(c); if (!I) return null; const n = I.c.length - 1, mv = MV.get(String(c.t).toUpperCase()) || MV.get(String(c.bbg).toUpperCase()); return { x: I.x[n], c: I.c[n], d30: I.c[n] - I.c[Math.max(0, n - 4)], g: I.g[n], m: I.m[n], k: I.k[n], r: I.r[n], e: I.e[n], cnt: I.count, mv: mv ? +mv.c : null }; };"
HELPERS_NEW = ("    const SKM = c => { const I = idxOf(c), S = SSC.by.get(String(c.t).toUpperCase()); if (!I && !S) return null; const n = I ? I.c.length - 1 : 0, mv = MV.get(String(c.t).toUpperCase()) || MV.get(String(c.bbg).toUpperCase()), P = S ? S.parts || {} : {};\n"
               "      return Object.assign(I ? { x: I.x[n], c: I.c[n], d30: I.c[n] - I.c[Math.max(0, n - 4)], g: I.g[n], m: I.m[n], k: I.k[n], r: I.r[n], e: I.e[n], cnt: I.count } : {}, { mv: mv ? +mv.c : null }, S ? { sig: S.score, pctl: S.pctl, p_earn: P.earn ?? null, p_val: P.val ?? null, p_ins: P.ins ?? null, p_crowd: P.crowd ?? null, p_risk: P.risk ?? null } : {}); };")

COLS_OLD = "    const SK_COLS = [['x', 'vs universe',"
COLS_NEW = ("    const SK_COLS = [['sig', 'Signal', 'Backtested signal score, −100 to +100: earnings surprises, valuation, insider selling, crowding and volatility, weighted by what predicted 4- and 12-week returns over the last 6 months'], ['p_earn', 'Earnings', 'Signal part: revenue and EPS surprise at the last print (last 95 days)'], ['p_val', 'Valuation', 'Signal part: forward earnings yield (cheaper scores higher)'], ['p_ins', 'Insider', 'Signal part: insiders selling outside 10b5-1 plans in the last 90 days (US only; more sellers scores lower)'], ['p_crowd', 'Crowding', 'Signal part: bullish sell-side evidence, rising estimates and few negative datapoints score lower (they predicted underperformance)'], ['p_risk', 'Volatility', 'Signal part: 12-week volatility (calmer scores higher)'],\n"
            "      ['x', 'vs universe',")

FLT_OLD = "      if (fs.flt === 'above' && !(m.x > 0)) return false; if (fs.flt === 'below' && !(m.x < 0)) return false;"
FLT_NEW = "      if (fs.flt === 'above' && !((m.sig ?? m.x) > 0)) return false; if (fs.flt === 'below' && !((m.sig ?? m.x) < 0)) return false; if (fs.flt === 'top' && !(m.pctl >= 80)) return false; if (fs.flt === 'bottom' && !(m.pctl != null && m.pctl <= 20)) return false;"

FLTOPT_OLD = "<option value=\"above\"${fs.flt === 'above' ? ' selected' : ''}>Above universe</option><option value=\"below\"${fs.flt === 'below' ? ' selected' : ''}>Below universe</option>"
FLTOPT_NEW = "<option value=\"top\"${fs.flt === 'top' ? ' selected' : ''}>Signal top 20%</option><option value=\"bottom\"${fs.flt === 'bottom' ? ' selected' : ''}>Signal bottom 20%</option><option value=\"above\"${fs.flt === 'above' ? ' selected' : ''}>Signal above 0</option><option value=\"below\"${fs.flt === 'below' ? ' selected' : ''}>Signal below 0</option>"

# sidebar default number: Signal when present
SIDE_OLD = ": I ? `<span class=\"mono ${I.x[n] >= 0 ? 'c-pos' : 'c-neg'}\" title=\"Composite vs universe\">${sgn(I.x[n])}</span>` : ''}</a>`; }).join('')}</div></div>`;"
SIDE_NEW = ": (() => { const S = SSC.by.get(String(c.t).toUpperCase()); return S ? `<span class=\"mono ${S.score >= 0 ? 'c-pos' : 'c-neg'}\" title=\"Signal score (percentile ${S.pctl})\">${sgn(S.score)}</span>` : I ? `<span class=\"mono muted\" title=\"Evidence index vs universe (no Signal score)\">${sgn(I.x[n])}</span>` : ''; })()}</a>`; }).join('')}</div></div>`;"

KEY_OLD = "Number = evidence index vs universe (−100 to +100; 0 = average, + more bullish)</div>"
KEY_NEW = "Number = Signal score (−100 to +100, backtested; 0 = average). Ranking table explains it.</div>"

TBL_SORT_OLD = "const sk = fs.sort || 'x', dir = fs.sort ? fs.dir : 'desc'"
TBL_SORT_NEW = "const sk = fs.sort || (SSC.doc ? 'sig' : 'x'), dir = fs.sort ? fs.dir : 'desc'"
TBL_CLICK_OLD = "const k = th.dataset.sk, curS = fs.sort || 'x';"
TBL_CLICK_NEW = "const k = th.dataset.sk, curS = fs.sort || (SSC.doc ? 'sig' : 'x');"
CELL_OLD = "`<td class=\"n ${['x', 'd30', 'mv'].includes(k) ? (v >= 0 ? 'up' : 'dn') : ''}\">"
CELL_NEW = "`<td class=\"n ${['x', 'd30', 'mv', 'sig', 'p_earn', 'p_val', 'p_ins', 'p_crowd', 'p_risk'].includes(k) ? (v >= 0 ? 'up' : 'dn') : ''}${k === 'sig' ? ' sk-sig' : ''}\">"

HOW_OLD = "<section class=\"panel\"><details class=\"sk-how\"><summary>How the score works</summary><div class=\"method\">"
HOW_NEW = ("${SSC.doc ? (() => { const B = SSC.doc.backtest || {}, G = SSC.doc.signals || {}, W = SSC.doc.weights || {}, LBL = { sur_sales: 'Revenue surprise, last print', sur_eps: 'EPS surprise, last print', ey: 'Forward earnings yield', ins_sellers_np: 'Insiders selling outside 10b5-1 plans, 90 days', ev_sell: 'Sell-side evidence tone, 90 days', ev_neg30: 'Share of negative datapoints, 30 days', rev_eps4: 'NTM EPS revision, 4 weeks', ev_r: 'Risk pillar of the evidence index', vol12: '12-week volatility', ev_comp: 'Old evidence index', mom6x1: '6-month momentum (ex last month)', mom3: '3-month momentum', pt_up: 'Upside to consensus target', ev_channel: 'Channel-check evidence tone', ev_mgmt: 'Management evidence tone', ev_g: 'Growth pillar', rev_sales4: 'NTM sales revision, 4 weeks', size: 'Size (trading value)', beta: 'Beta' };"
           " const keys = Object.keys(G).sort((a, b) => Math.abs(G[b].ic4) - Math.abs(G[a].ic4)).slice(0, 18);"
           " return `<section class=\"panel\"><details class=\"sk-how\" open><summary>How the Signal score works</summary><div class=\"method\">"
           "<p><b>What it is:</b> one number per stock built from the inputs that best predicted each stock's return over the next 4 and 12 weeks, after removing its market beta, across ${esc(SSC.doc.universe || '')} from ${esc((B['4 weeks'] || {}).dates || '')}. As of ${esc(fmtD(SSC.doc.as_of))}.</p>"
           "<div class=\"tbl-wrap\"><table class=\"dt\"><thead><tr><th>Input</th><th class=\"n\">Weight</th><th class=\"n\">4-week IC</th><th class=\"n\">12-week IC</th></tr></thead><tbody>${Object.entries(W).map(([k, w]) => `<tr><td>${esc(LBL[k] || k)}</td><td class=\"n\">${w > 0 ? '+' : ''}${Math.round(w * 100)}%</td><td class=\"n\">${G[k] ? (G[k].ic4 > 0 ? '+' : '') + G[k].ic4.toFixed(2) + ` (t ${G[k].t4})` : '–'}</td><td class=\"n\">${G[k] ? (G[k].ic12 > 0 ? '+' : '') + G[k].ic12.toFixed(2) + ` (t ${G[k].t12})` : '–'}</td></tr>`).join('')}</tbody></table></div>"
           "<p><b>Backtest:</b> ${Object.entries(B).map(([h, b]) => `${esc(h)}: rank IC ${b.ic > 0 ? '+' : ''}${b.ic} (t ${b.t}), top-minus-bottom fifth ${b.spread_pct > 0 ? '+' : ''}${b.spread_pct}% per period, positive in ${Math.round(b.spread_hit * 100)}% of weeks; the old evidence index scored ${b.old_ic > 0 ? '+' : ''}${b.old_ic}`).join('. ')}.</p>"
           "<p class=\"th-rec\"><b>Caveat:</b> ${esc(SSC.doc.oos_note || '')} The weights were chosen with the full 6 months in view, so the backtest flatters them; the period includes two sharp AI sell-offs (June–July and late September–October).</p>"
           "<details><summary>Every input tested (4-week IC, beta-adjusted)</summary><div class=\"tbl-wrap\"><table class=\"dt\"><thead><tr><th>Input</th><th class=\"n\">4-week IC</th><th class=\"n\">12-week IC</th></tr></thead><tbody>${keys.map(k => `<tr><td>${esc(LBL[k] || k)}</td><td class=\"n\">${(G[k].ic4 > 0 ? '+' : '') + G[k].ic4.toFixed(3)} (t ${G[k].t4})</td><td class=\"n\">${(G[k].ic12 > 0 ? '+' : '') + G[k].ic12.toFixed(3)} (t ${G[k].t12})</td></tr>`).join('')}</tbody></table></div></details>"
           "</div></details></section>`; })() : ''}"
           "<section class=\"panel\"><details class=\"sk-how\"><summary>How the evidence index works (context column)</summary><div class=\"method\">")

HEAD_OLD = "        <div class=\"sk-kpis\">${mv ?"
HEAD_NEW = "        <div class=\"sk-kpis\">${(() => { const S = SSC.by.get(String(cur.t).toUpperCase()); return S ? `<span title=\"Backtested signal score; see the ranking table\"><span class=\"sub\">Signal</span> <b class=\"mono ${S.score >= 0 ? 'c-pos' : 'c-neg'}\">${sgn(S.score)}</b> <span class=\"sub\">pctl ${S.pctl}</span></span>` : ''; })()}${mv ?"

CSS = """table.sk-rt td.sk-sig { font-weight: 650; }
"""

REPL = [
    ("  function renderStocks() {\n", LOADER + "  function renderStocks() {\n    sscStart();\n"),
    (HELPERS_OLD, HELPERS_NEW), (COLS_OLD, COLS_NEW), (FLT_OLD, FLT_NEW), (FLTOPT_OLD, FLTOPT_NEW), (SIDE_OLD, SIDE_NEW), (KEY_OLD, KEY_NEW),
    (TBL_SORT_OLD, TBL_SORT_NEW), (TBL_CLICK_OLD, TBL_CLICK_NEW), (CELL_OLD, CELL_NEW), (HOW_OLD, HOW_NEW), (HEAD_OLD, HEAD_NEW),
    ("/* Thesis tab */", CSS + "/* Thesis tab */"),
]


def main(paths):
    texts = {p: open(p, encoding="utf-8").read() for p in paths}
    if any(MARKER in t for t in texts.values()):
        print("already present"); return 0
    if not any(NEEDS in t for t in texts.values()):
        print("stock-scores v1 missing", file=sys.stderr); return 2
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
