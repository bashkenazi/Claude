#!/usr/bin/env python3
"""AI thesis › By tenet v2 (Bobby, 2026-11-10): five-level score dots per datapoint against the AI bull thesis
(two green, one green, blue neutral, one red, two red), a filter bar (tenet, sentiment, how far back, how many),
newest first, and an optional GW table per tenet. Replaces thTenets() from 06_ai_tenets. Requires ai-tenets v1.
Usage: 07_ai_tenets_v2.py <in> <out>. Idempotent."""
import sys

MARKER = "/* ai-tenets v2 */"
NEEDS = "/* ai-tenets v1 */"
START = "  function thTenets() {"
END = "\n  function thStart() {"
CSS_ANCHOR = "#v-thesis section.tn[id] {"
CSS = """.tn-dots { display: inline-flex; gap: 2px; align-items: center; flex: none; min-width: 20px; }
.tn-dots i { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.tn-dots.g i { background: var(--pos); } .tn-dots.r i { background: var(--neg); } .tn-dots.b i { background: var(--accent); }
.tn-bar { display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; font-size: 12.5px; position: sticky; top: calc(env(safe-area-inset-top, 0px) + var(--mast-h, 53px)); z-index: 8; background: var(--bg); padding: 8px 0; border-bottom: 1px solid var(--rule); }
.tn-bar label { display: inline-flex; gap: 6px; align-items: center; color: var(--muted); min-width: 0; max-width: 100%; }
.tn-bar select { min-width: 0; max-width: min(100%, 320px); }
table.tn-gw td { white-space: normal; min-width: 90px; max-width: 280px; }
.tn-key { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12px; color: var(--ink-2); }
.tn-key span { display: inline-flex; gap: 5px; align-items: center; }
.tn-bal { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: var(--surface-2); }
.tn-bal i { display: block; height: 100%; } .tn-bal i.g { background: var(--pos); } .tn-bal i.b { background: var(--accent); } .tn-bal i.r { background: var(--neg); }
"""

JS = r"""  """ + MARKER + r"""
  const TNF = (() => { let f = {}; try { f = JSON.parse(localStorage.getItem('tn-filt') || '{}'); } catch (e) {} return Object.assign({ tenet: '', sent: '', days: '', n: '10' }, f); })();
  const tnSave = () => { try { localStorage.setItem('tn-filt', JSON.stringify(TNF)); } catch (e) {} };
  const tnScore = d => d.score != null ? Number(d.score) : (d.stance === 'supports' ? 1 : d.stance === 'challenges' ? -1 : 0);
  const tnDots = s => { const c = s > 0 ? 'g' : s < 0 ? 'r' : 'b', n = Math.abs(s) === 2 ? 2 : 1, lab = s === 2 ? 'Strongly supports' : s === 1 ? 'Supports' : s === 0 ? 'Neutral' : s === -1 ? 'Weakens' : 'Strongly weakens'; return `<span class="tn-dots ${c}" title="${lab} the thesis" aria-label="${lab}">${'<i></i>'.repeat(n)}</span>`; };
  const TN_SENT = [['', 'All sentiment'], ['g', 'All supportive (green)'], ['2', '●● Strongly supports'], ['1', '● Supports'], ['0', '● Neutral (blue)'], ['-1', '● Weakens'], ['-2', '●● Strongly weakens'], ['r', 'All weakening (red)']];
  const TN_DAYS = [['', 'All dates'], ['7', 'Last week'], ['14', 'Last 2 weeks'], ['30', 'Last month'], ['90', 'Last 3 months']];
  const TN_N = [['5', '5 per tenet'], ['10', '10 per tenet'], ['25', '25 per tenet'], ['', 'All']];
  function tnPass(d, asOf) {
    const s = tnScore(d), f = TNF.sent;
    if (f === 'g' && !(s > 0)) return false; if (f === 'r' && !(s < 0)) return false;
    if (f !== '' && f !== 'g' && f !== 'r' && s !== Number(f)) return false;
    if (TNF.days) { const lim = new Date(asOf); lim.setDate(lim.getDate() - Number(TNF.days)); if (new Date(d.date) < lim) return false; }
    return true;
  }
  function thTenets() {
    const D2 = TH.tenets; if (!D2) return `<section class="panel">${none('No tenet breakdown saved yet.')}</section>`;
    const TS = arr(D2.tenets).slice().sort((a, b) => (a.sort || 0) - (b.sort || 0));
    const asOf = String(D2.updated_at || new Date().toISOString()).slice(0, 10);
    const opt = (xs, v) => xs.map(([k, l]) => `<option value="${esc(k)}"${String(v) === k ? ' selected' : ''}>${esc(l)}</option>`).join('');
    const bar = `<div class="tn-bar" role="group" aria-label="Datapoint filters">` +
      `<label>Tenet <select data-tnf="tenet"><option value="">All tenets</option>${TS.map(t => `<option value="${esc(t.key)}"${TNF.tenet === t.key ? ' selected' : ''}>${esc(t.title)}</option>`).join('')}</select></label>` +
      `<label>Sentiment <select data-tnf="sent">${opt(TN_SENT, TNF.sent)}</select></label>` +
      `<label>How far back <select data-tnf="days">${opt(TN_DAYS, TNF.days)}</select></label>` +
      `<label>How many <select data-tnf="n">${opt(TN_N, TNF.n)}</select></label>` +
      `<span class="sub">Newest first</span></div>`;
    const key = `<div class="tn-key">${[[2, 'Strongly supports'], [1, 'Supports'], [0, 'Neutral or mixed'], [-1, 'Weakens'], [-2, 'Strongly weakens']].map(([s, l]) => `<span>${tnDots(s)}${esc(l)}</span>`).join('')}<span class="sub">scored against the AI bull thesis</span></div>`;
    const bal = ds => { const g = ds.filter(d => tnScore(d) > 0).length, r = ds.filter(d => tnScore(d) < 0).length, b = ds.length - g - r, n = ds.length || 1; return `<div class="tn-bal" title="${g} green · ${b} blue · ${r} red"><i class="g" style="width:${g / n * 100}%"></i><i class="b" style="width:${b / n * 100}%"></i><i class="r" style="width:${r / n * 100}%"></i></div>`; };
    const strip = `<section class="panel"><div class="panel-h"><h2>Tenets</h2><span class="muted">updated ${esc(fmtD(asOf))}</span></div>${key}` +
      `<div class="tn-strip">${TS.map(t => { const n = arr(t.dps), g = n.filter(d => tnScore(d) > 0).length, r = n.filter(d => tnScore(d) < 0).length; return `<a href="#thesis" data-tn="${esc(t.key)}"><span class="chips">${thChip(t.status)}</span><b>${esc(t.title)}</b>${n.length ? bal(n) : ''}<span class="sub">${n.length} datapoints${n.length ? ` · ${g} green · ${r} red` : ''}${arr(t.checks).length ? ` · ${arr(t.checks).length} fact check${arr(t.checks).length > 1 ? 's' : ''}` : ''}</span></a>`; }).join('')}</div>` +
      (D2.storage ? `<p class="sub">${esc(D2.storage)}</p>` : '') + `</section>`;
    const src = xs => arr(xs).map(([t, u]) => u ? `<a class="ext" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>` : esc(t)).join('<br>');
    const lim = TNF.n ? Number(TNF.n) : Infinity;
    const body = TS.filter(t => !TNF.tenet || t.key === TNF.tenet).map(t => {
      const FC = arr(t.checks), all = arr(t.dps).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)) || (b.id || 0) - (a.id || 0));
      const pass = all.filter(d => tnPass(d, asOf)), DP = pass.slice(0, lim), G = t.gw;
      return `<section class="panel tn" id="tn-${esc(t.key)}"><div class="panel-h"><h2>${esc(t.title)}</h2><span class="chips">${thChip(t.status)}</span></div>` +
        (t.claim ? `<p class="lede">${esc(t.claim)}</p>` : '') +
        (t.srs_view ? `<p class="tn-view"><b>SRS view:</b> ${esc(t.srs_view)}</p>` : '') +
        (G && arr(G.rows).length ? `<h3>${esc(G.title || 'GW deployed')}</h3><div class="tbl-wrap"><table class="dt tn-gw"><thead><tr>${arr(G.cols).map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${arr(G.rows).map(r => `<tr>${arr(r).map((c, i) => `<td class="${i > 1 ? 'wrap' : ''}">${i === 1 ? esc(fmtD(c)) : esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${G.note ? `<p class="sub">${esc(G.note)}</p>` : ''}` : '') +
        (FC.length ? `<h3>Fact check</h3><div class="tbl-wrap"><table class="dt tn-fc"><thead><tr><th>Claim</th><th>Verdict</th><th>What we found</th><th>Sources</th></tr></thead><tbody>${FC.map(f => `<tr><td class="wrap"><b>${esc(f.claim)}</b></td><td>${thChip(f.verdict, TN_V)}</td><td class="wrap">${esc(f.text)}</td><td class="wrap">${src(f.sources)}</td></tr>`).join('')}</tbody></table></div>` : '') +
        `<h3>Datapoints <span class="muted">${DP.length} of ${pass.length}${pass.length !== all.length ? ` matching (${all.length} total)` : ''}</span></h3>` +
        (DP.length ? `<div class="list">${DP.map(d => `<div class="li">${tnDots(tnScore(d))}<div class="body"><div class="chips"><span class="tk-chip">${esc(d.t)}</span></div>${esc(d.text)}<div class="srcl"><span>Source</span>${esc(d.src || '')} · SB #${esc(d.id)}</div></div><div class="side">${esc(fmtD(d.date))}</div></div>`).join('')}</div>` : none(all.length ? 'No datapoints match these filters.' : 'No datapoints linked yet.')) +
        (arr(t.staged).length ? `<h3>Staged, not yet in Supabase</h3>${arr(t.staged).map(g => `<div class="tn-stage"><div class="chips"><span class="tk-chip">${esc(g.t)}</span><span class="sub">${esc(fmtD(g.date))}</span></div>${esc(g.text)}<div class="srcl"><span>Source</span>${esc(g.primary)}${g.secondary ? ' via ' + esc(g.secondary) : ''}</div></div>`).join('')}` : '') +
        `</section>`;
    }).join('');
    setTimeout(() => document.querySelectorAll('#v-thesis [data-tnf]').forEach(s => s.addEventListener('change', () => { TNF[s.dataset.tnf] = s.value; tnSave(); renderThesis(); })), 0);
    return strip + bar + body;
  }
"""


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    if NEEDS not in s:
        print("ai-tenets v1 missing", file=sys.stderr); return 2
    if s.count(START) != 1 or s.count(CSS_ANCHOR) != 1:
        print("anchors not unique", s.count(START), s.count(CSS_ANCHOR), file=sys.stderr); return 2
    i = s.index(START); j = s.index(END, i)
    s = s[:i] + JS + s[j:]
    k = s.index(CSS_ANCHOR); s = s[:k] + CSS + s[k:]
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
