#!/usr/bin/env python3
"""AI thesis tab: add an 'Overview | By tenet' switch. 'By tenet' shows each tenet with its status, Bobby's view,
fact checks (claim, verdict, what we found, sources) and linked datapoints. Data: page-database doc
thesis/ai_tenets, a mirror of Supabase thesis_tenets + thesis_tenet_evidence (datapoints live in research_evidence).
Usage: 06_ai_tenets.py <in> <out>. Works on tabs.js(+css) or the built page. Idempotent."""
import sys

MARKER = "/* ai-tenets v1 */"
SNAP_OLD = "const d = snap.docs.find(x => x.id === 'ai'); TH.doc = d ? JSON.parse(JSON.stringify(d.data())) : null;"
SNAP_NEW = SNAP_OLD + " const dt = snap.docs.find(x => x.id === 'ai_tenets'); TH.tenets = dt ? JSON.parse(JSON.stringify(dt.data())) : null;"
VIEW_OLD = "    if (!T) { host.innerHTML = h + `<section class=\"panel\">${none(esc(TH.err || 'Loading the thesis…'))}</section>`; return; }\n"
VIEW_NEW = VIEW_OLD + "    h += thViewSeg();\n    if (thView() === 'tenets') { host.innerHTML = h + thTenets(); thSegBind(host); return; }\n"
BIND_OLD = "    host.querySelectorAll('[data-ths]').forEach(b => b.addEventListener('click', () => { TH.show = b.dataset.ths; renderThesis(); }));"
BIND_NEW = "    thSegBind(host);\n" + BIND_OLD
ST_OLD = "no_read: ['out', 'No new read'] };"
ST_NEW = "no_read: ['out', 'No new read'], new: ['a-split', 'New tenet'] };"
ANCHOR = "  function thStart() {"
CSS_ANCHOR = "#v-thesis h3 { margin-top: 6px; }"
CSS = """
.th-vs { margin: 2px 0 4px; }
.tn-strip { display: grid; gap: 6px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 230px), 1fr)); }
.tn-strip a { display: flex; flex-direction: column; gap: 4px; padding: 8px 10px; border: 1px solid var(--rule); border-radius: 6px; text-decoration: none; color: var(--ink); background: var(--surface); font-size: 13px; }
.tn-strip a:hover { border-color: var(--accent); }
.tn-view { margin: 0; padding: 8px 10px; background: var(--accent-wash); border-radius: 6px; font-size: 13px; max-width: 110ch; }
table.tn-fc td.wrap { min-width: 280px; max-width: 640px; }
table.tn-fc td:first-child { min-width: 180px; }
.tn-stage { border: 1px dashed var(--rule-2); border-radius: 6px; padding: 8px 10px; font-size: 13px; }
#v-thesis section.tn[id] { scroll-margin-top: calc(var(--mast-h, 53px) + 12px); }
"""

JS = r"""
  """ + MARKER + r"""
  // AI thesis › By tenet. Doc thesis/ai_tenets mirrors Supabase thesis_tenets (tenets, Bobby's view, fact checks)
  // and thesis_tenet_evidence (links to research_evidence rows, with stance supports / challenges / mixed).
  const TN_V = { confirmed: ['s-positive', 'Confirmed'], supported: ['s-positive', 'Supported'], mostly: ['a-aligned', 'Mostly right'], partly: ['s-mixed', 'Partly right'],
    reported: ['a-aligned', 'Reported'], unverified: ['out', 'Unverified'], not_supported: ['s-negative', 'Not supported'], inference: ['out', 'SRS inference'] };
  const TN_SD = { supports: ['pos', 'Supports'], challenges: ['neg', 'Challenges'], mixed: ['mix', 'Mixed'] };
  const thView = () => { if ((location.hash || '').startsWith('#thesis/tenets')) return 'tenets'; if (TH.view) return TH.view; try { return localStorage.getItem('th-view') || 'overview'; } catch (e) { return 'overview'; } };
  const thViewSeg = () => { const v = thView(); return `<div class="seg th-vs" role="group" aria-label="Thesis view"><button type="button" data-thv="overview" aria-pressed="${v === 'overview'}">Overview</button><button type="button" data-thv="tenets" aria-pressed="${v === 'tenets'}">By tenet</button></div>`; };
  function thSegBind(host) {
    host.querySelectorAll('[data-thv]').forEach(b => b.addEventListener('click', () => { TH.view = b.dataset.thv; try { localStorage.setItem('th-view', TH.view); } catch (e) {} if ((location.hash || '').startsWith('#thesis/')) history.replaceState(null, '', '#thesis'); renderThesis(); }));
    host.querySelectorAll('[data-tn]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const t = document.getElementById('tn-' + a.dataset.tn); if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }));
  }
  function thTenets() {
    const D2 = TH.tenets; if (!D2) return `<section class="panel">${none('No tenet breakdown saved yet.')}</section>`;
    const TS = arr(D2.tenets).slice().sort((a, b) => (a.sort || 0) - (b.sort || 0));
    const strip = `<section class="panel"><div class="panel-h"><h2>Tenets</h2><span class="muted">updated ${esc(fmtD(String(D2.updated_at || '').slice(0, 10)))}</span></div>` +
      `<div class="tn-strip">${TS.map(t => { const n = arr(t.dps), c = n.filter(d => d.stance === 'challenges').length, s = n.filter(d => d.stance === 'supports').length; return `<a href="#thesis" data-tn="${esc(t.key)}"><span class="chips">${thChip(t.status)}</span><b>${esc(t.title)}</b><span class="sub">${n.length} datapoints${n.length ? ` · ${s} support · ${c} challenge` : ''}${arr(t.checks).length ? ` · ${arr(t.checks).length} fact check${arr(t.checks).length > 1 ? 's' : ''}` : ''}</span></a>`; }).join('')}</div>` +
      (D2.storage ? `<p class="sub">${esc(D2.storage)}</p>` : '') + `</section>`;
    const src = xs => arr(xs).map(([t, u]) => u ? `<a class="ext" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t)).join('<br>');
    const body = TS.map(t => {
      const FC = arr(t.checks), DP = arr(t.dps).slice().sort((a, b) => String(b.date).localeCompare(String(a.date))), SG = arr(t.staged);
      return `<section class="panel tn" id="tn-${esc(t.key)}"><div class="panel-h"><h2>${esc(t.title)}</h2><span class="chips">${thChip(t.status)}</span></div>` +
        (t.claim ? `<p class="lede">${esc(t.claim)}</p>` : '') +
        (t.srs_view ? `<p class="tn-view"><b>SRS view:</b> ${esc(t.srs_view)}</p>` : '') +
        (FC.length ? `<h3>Fact check</h3><div class="tbl-wrap"><table class="dt tn-fc"><thead><tr><th>Claim</th><th>Verdict</th><th>What we found</th><th>Sources</th></tr></thead><tbody>${FC.map(f => `<tr><td class="wrap"><b>${esc(f.claim)}</b></td><td>${thChip(f.verdict, TN_V)}</td><td class="wrap">${esc(f.text)}</td><td class="wrap">${src(f.sources)}</td></tr>`).join('')}</tbody></table></div>` : '') +
        (DP.length ? `<h3>Datapoints <span class="muted">${DP.length}</span></h3><div class="list">${DP.map(d => { const s = TN_SD[d.stance] || ['', '']; return `<div class="li"><span class="stripe ${s[0]}"></span><div class="body"><div class="chips"><span class="tk-chip">${esc(d.t)}</span><span class="chip">${esc(s[1])}</span></div>${esc(d.text)}<div class="srcl"><span>Source</span>${esc(d.src || '')} · SB #${esc(d.id)}</div></div><div class="side">${esc(fmtD(d.date))}</div></div>`; }).join('')}</div>` : (t.note ? `<p class="sub">${esc(t.note)}</p>` : none('No datapoints linked yet.'))) +
        (SG.length ? `<h3>Staged, not yet in Supabase</h3>${SG.map(g => `<div class="tn-stage"><div class="chips"><span class="tk-chip">${esc(g.t)}</span><span class="chip out">${esc(g.field_key)} · ${esc(g.confidence)}</span><span class="sub">${esc(fmtD(g.date))}</span></div>${esc(g.text)}<div class="srcl"><span>Source</span>${esc(g.primary)}${g.secondary ? ' via ' + esc(g.secondary) : ''}</div>${g.why ? `<div class="sub">${esc(g.why)}</div>` : ''}</div>`).join('')}` : '') +
        `</section>`;
    }).join('');
    return strip + body;
  }

"""


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    for n, a in [("snap", SNAP_OLD), ("view", VIEW_OLD), ("bind", BIND_OLD), ("status", ST_OLD), ("anchor", ANCHOR), ("css", CSS_ANCHOR)]:
        if s.count(a) != 1:
            print(f"anchor {n} found {s.count(a)} times", file=sys.stderr); return 2
    s = (s.replace(SNAP_OLD, SNAP_NEW).replace(VIEW_OLD, VIEW_NEW).replace(BIND_OLD, BIND_NEW).replace(ST_OLD, ST_NEW)
          .replace(ANCHOR, JS + ANCHOR).replace(CSS_ANCHOR, CSS_ANCHOR + CSS))
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
