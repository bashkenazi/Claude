#!/usr/bin/env python3
"""Add universe-wide insider signal sections (10b5-1 step-outs, cessation of selling, option skimming,
plan changes, universe buys) to the Management & insiders callouts. Data comes from the page database
document insider_signals/latest, written by the "Insider signals" scheduled task.
Usage: add_insider_signals.py <in> <out>. Requires mgmt-callouts v1. Idempotent."""
import sys

MARKER = "/* insider-signals v1 */"
NEEDS = "/* mgmt-callouts v1 */"
HOOK_OLD = "    if (!body) return '';\n    return `<section class=\"panel mg-callouts\">"
HOOK_NEW = "    const body2 = body + insSignals();\n    if (!body2) return '';\n    return `<section class=\"panel mg-callouts\">"
TAIL_OLD = "Canary question sets' : ''}</span></div>${body}</section>`;"
TAIL_NEW = "Canary question sets' : ''}</span></div>${body2}</section>`;"
ROUTER = "  // ================= ROUTER ================="

JS = r"""
  """ + MARKER + r"""
  // Universe-wide insider signals from the page database (insider_signals/latest), refreshed by the
  // "Insider signals" scheduled task: 10b5-1 step-outs, cessation of selling, option skimming, plan changes.
  const INS = { doc: null, err: '' };
  if (window.claude && typeof window.claude.use === 'function') {
    window.claude.use('db').then(db => { if (!db) return;
      db.collection('insider_signals').doc('latest').onSnapshot(s => { INS.doc = s && s.exists ? s.data() : null; if ((location.hash || '').startsWith('#mgmt')) renderMgmt(); },
        e => { INS.err = (e && e.code) || 'error'; });
    }).catch(() => {});
  }
  function insSignals() {
    const S = INS.doc; if (!S) return `<p class="sub">Universe-wide insider signals (10b5-1 step-outs, cessation of selling, option skimming) load from the Insider signals task${INS.err ? ': ' + esc(INS.err) : '…'}</p>`;
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const who = x => `<b>${esc(x.insider || '')}</b>${x.title ? ` <span class="sub">(${esc(x.title)})</span>` : ''}`;
    const lk = x => x.link ? ` <a class="ext" href="${esc(x.link)}" target="_blank" rel="noopener">filing</a>` : '';
    const sec = (title, note, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${title}</div>${note ? `<p class="sub" style="margin:2px 0 4px">${note}</p>` : ''}<ul class="b">${items.join('')}</ul></div>` : '';
    const steps = arr(S.step_outs).slice(0, 8).map(x => `<li>🚪 ${tk(x.t)} ${who(x)} sold <b>${m$(x.value_usd)}</b> outside a 10b5-1 plan on ${esc(fmtD(x.date))}${x.prior_plan_sales_12m ? ` after <b>${esc(x.prior_plan_sales_12m)}</b> plan sales in 12 months` : ''}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}${lk(x)}</li>`);
    const stops = arr(S.cessations).slice(0, 8).map(x => `<li>⏸️ ${tk(x.t)} ${who(x)} has not sold for <b>${esc(x.days_since)} days</b> after <b>${esc(x.sells_prior)}</b> sales (${m$(x.value_prior_usd)}) over the prior 9 months${x.plan_note ? ` <span class="sub">· ${esc(x.plan_note)}</span>` : ''}</li>`);
    const skim = arr(S.skimming).slice(0, 8).map(x => `<li>${x.kind === 'exercise_hold' ? '🟢' : '🔻'} ${tk(x.t)} ${who(x)} ${x.kind === 'exercise_hold' ? 'exercised and <b>kept</b>' : 'exercised and sold'} ${x.shares != null ? Number(x.shares).toLocaleString() + ' sh' : ''} (<b>${m$(x.value_usd)}</b>) on ${esc(fmtD(x.date))}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}${lk(x)}</li>`);
    const plans = arr(S.plan_changes).slice(0, 8).map(x => `<li>📝 ${tk(x.t)} ${who(x)} ${esc(x.kind === 'terminated' ? 'terminated a 10b5-1 plan' : x.kind === 'modified' ? 'modified a 10b5-1 plan' : 'adopted a new 10b5-1 plan')}${x.date ? ' · ' + esc(fmtD(x.date)) : ''}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}</li>`);
    const buys = arr(S.universe_buys).slice(0, 6).map(x => `<li>🟢 ${tk(x.t)} ${who(x)} bought <b>${m$(x.value_usd)}</b> on ${esc(fmtD(x.date))}${x.note ? ` <span class="sub">· ${esc(x.note)}</span>` : ''}</li>`);
    const cov = S.coverage || {};
    return `<div class="mg-co-sec"><div class="eyebrow" style="color:var(--ink)">Across your universe${cov.us != null ? ` · ${esc(cov.us)} US-listed names (Insider Score)${cov.non_us_covered != null ? ` + ${esc(cov.non_us_covered)} of ${esc(cov.non_us)} non-US (Canary)` : ''}` : ''}${S.as_of ? ' · as of ' + esc(fmtD(S.as_of)) : ''}</div></div>` +
      sec('🚪 Stepping out of 10b5-1 plans', 'Insiders who sell on a pre-set plan and then sell outside it: a discretionary choice, so it says more than plan sales.', steps) +
      sec('⏸️ Cessation of selling', 'Regular sellers who have stopped. Often read as insiders seeing more upside (or a blackout before news).', stops) +
      sec('🔻 Option skimming', 'Options exercised and the shares sold at once, often for a small gain or well before expiry. Exercise-and-hold (🟢) is the bullish version.', skim) +
      sec('📝 10b5-1 plan changes', '', plans) +
      sec('🟢 Open-market buying beyond Tier 1–2', '', buys);
  }

"""

CSS_ANCHOR = ".mg-callouts { border-left: 3px solid var(--accent); }"
CSS = "\n.mg-callouts .mg-co-sec .eyebrow + p.sub { max-width: 110ch; }"


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    if NEEDS not in s:
        print("mgmt-callouts v1 missing", file=sys.stderr); return 2
    for n, a in [("hook", HOOK_OLD), ("tail", TAIL_OLD), ("router", ROUTER), ("css", CSS_ANCHOR)]:
        if s.count(a) != 1:
            print(f"anchor {n} found {s.count(a)} times", file=sys.stderr); return 2
    s = s.replace(HOOK_OLD, HOOK_NEW).replace(TAIL_OLD, TAIL_NEW).replace(ROUTER, JS + ROUTER).replace(CSS_ANCHOR, CSS_ANCHOR + CSS)
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
