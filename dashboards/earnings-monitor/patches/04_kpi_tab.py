#!/usr/bin/env python3
"""Add a 'KPIs & guidance' sub-tab to each stock on Bobby Tech Daily's Stocks tab.
Reads page-database collection kpi_profiles/<qrId(ticker)> (mirror of Supabase kpi_profiles,
company_kpis and guidance_history, written by the KPI & guidance backfill task). Idempotent."""
import sys

MARKER = "/* kpi-tab v1 */"
TABS_OLD = "['qr', 'Quarterly review'], "
TABS_NEW = "['qr', 'Quarterly review'], ['kpis', 'KPIs & guidance'], "
DISP_OLD = "    if (sub === 'insiders') { stockMgView(cur, $('sk-body')); return; }"
DISP_NEW = DISP_OLD + "\n    if (sub === 'kpis') { stockKpiView(cur, $('sk-body')); return; }"
ROUTER = "  // ================= ROUTER ================="
CSS_ANCHOR = ".mg-callouts { border-left: 3px solid var(--accent); }"
CSS = """
.kp-where { display: inline-flex; gap: 3px; flex-wrap: wrap; }
.kp-where .chip { font-size: 10.5px; padding: 0 6px; }
.kp-g td.n { white-space: nowrap; }
.kp-g td.up { color: var(--pos); } .kp-g td.dn { color: var(--neg); }
.kp-g tr.kp-h td { background: var(--surface-2); font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
.kp-seg { display: flex; flex-direction: column; gap: 6px; }
"""

JS = r"""
  """ + MARKER + r"""
  // Stocks › KPIs & guidance. Source of record: Supabase kpi_profiles / company_kpis / guidance_history;
  // the backfill task mirrors each company into page-database doc kpi_profiles/<id> so this tab reads it live.
  const KP = { db: null, ready: null, cache: new Map() };
  KP.ready = (window.claude && typeof window.claude.use === 'function') ? window.claude.use('db').then(d => { KP.db = d; }).catch(() => {}) : Promise.resolve();
  const WHERE_L = { press_release: 'Release', deck: 'Deck', call: 'Call', '10q': '10-Q', '10k': '10-K', investor_day: 'Investor day', shareholder_letter: 'Letter', '8k': '8-K', conference: 'Conference' };
  function stockKpiView(cur, el) {
    const id = qrId(cur.t);
    el.innerHTML = `<section class="panel"><p class="sub">Loading KPIs and guidance…</p></section>`;
    const paint = doc => {
      if (!document.body.contains(el)) return;
      if (!doc) { el.innerHTML = `<section class="panel"><h2>KPIs &amp; guidance</h2>${none('Not built yet for ' + esc(cur.t) + '. The nightly KPI & guidance backfill adds companies Tier 1 first.')}</section>`; return; }
      const P = doc.profile || {}, K = arr(doc.kpis), G = arr(doc.guidance);
      const wh = w => `<span class="kp-where">${arr(w).map(x => `<span class="chip">${esc(WHERE_L[x] || x)}</span>`).join('')}</span>`;
      const seg = arr(P.segmentation).map(s => `<div><b>${esc(s.basis || 'Segments')}</b>: ${arr(s.segments).map(esc).join(' · ')} <span class="sub">· ${wh(s.where)} · ${esc(s.frequency || '')}${s.since ? ' · since ' + esc(s.since) : ''}${s.note ? ' · ' + esc(s.note) : ''}</span></div>`).join('');
      const cats = [...new Set(K.map(k => k.category || 'other'))];
      const kt = K.length ? `<div class="tbl-wrap"><table class="dt"><thead><tr><th>Metric</th><th>Unit</th><th>Where disclosed</th><th>How often</th><th>Reported</th><th>Note</th></tr></thead><tbody>${cats.map(c => `<tr class="kp-h"><td colspan="6">${esc(c)}</td></tr>` + K.filter(k => (k.category || 'other') === c).map(k => `<tr><td class="wrap">${esc(k.metric)}${k.definition ? `<div class="sub">${esc(k.definition)}</div>` : ''}</td><td>${esc(k.unit || '')}</td><td>${wh(k.where_disclosed)}</td><td>${esc(k.frequency || '')}${k.status && k.status !== 'active' ? ` <span class="chip out">${esc(k.status)}</span>` : ''}</td><td class="nowrap">${esc(k.first_period || '')}${k.last_period ? ' → ' + esc(k.last_period) : ''}</td><td class="wrap">${esc(k.note || '')}${k.source_url ? ` <a class="ext" href="${esc(k.source_url)}" target="_blank" rel="noopener">source</a>` : ''}</td></tr>`).join('')).join('')}</tbody></table></div>` : none('No KPIs recorded.');
      // guidance: one row per metric + target period, one column per date the guide was given, read left to right
      const fmtV = g => g.value_text ? esc(g.value_text) : (g.low != null && g.high != null && g.low !== g.high ? `${esc(g.low)}–${esc(g.high)}` : esc(g.mid ?? g.low ?? g.high ?? '')) + (g.unit && !/^\$/.test(g.unit) ? ' ' + esc(g.unit) : '');
      const cls = c => /raised|up/i.test(c || '') ? 'up' : /lowered|cut|withdrawn/i.test(c || '') ? 'dn' : '';
      const hz = [['quarter', 'Quarterly guidance'], ['fiscal_year', 'Fiscal-year guidance'], ['long_term', 'Long-term targets (analyst days)']];
      const gt = hz.map(([h, label]) => {
        const rows = G.filter(g => g.horizon === h); if (!rows.length) return '';
        const dates = [...new Set(rows.map(g => g.given_on))].sort();
        const keys = [...new Set(rows.map(g => g.target_period + '||' + g.metric))].sort((a, b) => b.localeCompare(a));
        const evt = d => { const r = rows.find(g => g.given_on === d); return r && r.event ? r.event : ''; };
        return `<h3 style="margin-top:8px">${label}</h3><div class="tbl-wrap"><table class="dt kp-g"><thead><tr><th>Period · metric</th>${dates.map(d => `<th class="n" title="${esc(evt(d))}">${esc(d)}<div class="sub" style="text-transform:none;letter-spacing:0">${esc(evt(d)).slice(0, 28)}</div></th>`).join('')}</tr></thead><tbody>${keys.map(k => { const [tp, m] = k.split('||');
          return `<tr><td class="wrap"><b>${esc(tp)}</b> · ${esc(m)}</td>${dates.map(d => { const g = rows.find(x => x.given_on === d && x.target_period === tp && x.metric === m); return g ? `<td class="n ${cls(g.change)}" title="${esc([g.change, g.given_at, g.note].filter(Boolean).join(' · '))}">${fmtV(g)}${g.change && !/initial|reiterated/i.test(g.change) ? `<div class="sub">${esc(g.change)}</div>` : ''}</td>` : '<td class="n sub">·</td>'; }).join('')}</tr>`; }).join('')}</tbody></table></div>`;
      }).join('');
      el.innerHTML = `<section class="panel"><div class="panel-h"><h2>Revenue segmentation</h2><span class="sub">${P.fiscal_year_end ? 'FY ends ' + esc(P.fiscal_year_end) + ' · ' : ''}checked ${esc(fmtD(String(P.checked_at || '').slice(0, 10)))}</span></div>${P.summary ? `<p style="margin:0">${esc(P.summary)}</p>` : ''}<div class="kp-seg">${seg || none('No segmentation recorded.')}</div></section>` +
        `<section class="panel"><div class="panel-h"><h2>Reported KPIs</h2><span class="sub">${K.length} metrics · where and how often each is disclosed</span></div>${kt}</section>` +
        `<section class="panel"><div class="panel-h"><h2>Guidance</h2><span class="sub">each column is a date guidance was given; green raised, red lowered</span></div>${gt || none('No guidance recorded.')}</section>` +
        (arr(P.sources).length ? `<section class="panel"><details><summary>Sources</summary><ul class="b">${arr(P.sources).map(s => `<li>${s.url ? `<a class="ext" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.url)}</a>` : esc(s.title || '')}${s.date ? ' · ' + esc(fmtD(s.date)) : ''}</li>`).join('')}</ul></details></section>` : '');
    };
    if (KP.cache.has(id)) { paint(KP.cache.get(id)); return; }
    KP.ready.then(() => {
      if (!KP.db) { el.innerHTML = `<section class="panel">${none('KPIs and guidance need the page open on claude.ai.')}</section>`; return; }
      KP.db.collection('kpi_profiles').doc(id).get().then(s => { const d = s && s.exists ? s.data() : null; KP.cache.set(id, d); paint(d); })
        .catch(e => { el.innerHTML = `<section class="panel">${none('Could not load KPIs: ' + esc((e && e.code) || 'error'))}</section>`; });
    });
  }

"""


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    for n, a in [("tabs", TABS_OLD), ("disp", DISP_OLD), ("router", ROUTER), ("css", CSS_ANCHOR)]:
        if s.count(a) != 1:
            print(f"anchor {n} found {s.count(a)} times", file=sys.stderr); return 2
    s = s.replace(TABS_OLD, TABS_NEW).replace(DISP_OLD, DISP_NEW).replace(ROUTER, JS + ROUTER).replace(CSS_ANCHOR, CSS_ANCHOR + CSS)
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
