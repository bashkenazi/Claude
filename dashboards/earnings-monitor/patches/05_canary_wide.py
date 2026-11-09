#!/usr/bin/env python3
"""Add the Canary wide-universe section (global Tech, Industrials, Materials; >$1bn market cap,
>$70mm average daily value traded) to the Management & insiders callouts. Data: page-database doc
insider_signals/latest, field `canary_wide`, written by the "Insider signals (universe)" task.
Usage: add_canary_wide.py <in> <out>. Requires insider-signals v1. Idempotent."""
import sys

MARKER = "/* canary-wide v1 */"
NEEDS = "/* insider-signals v1 */"
HOOK_OLD = "sec('🟢 Open-market buying beyond Tier 1–2', '', buys);"
HOOK_NEW = "sec('🟢 Open-market buying beyond Tier 1–2', '', buys) + canaryWide(S);"
ROUTER = "  // ================= ROUTER ================="

JS = r"""
  """ + MARKER + r"""
  // Canary insider flags across global Tech, Industrials and Materials names over $1bn market cap and
  // $70mm/day traded (not limited to the Companies DB). Written by the Insider signals task as S.canary_wide.
  function canaryWide(S) {
    const W = S && S.canary_wide; if (!W) return '';
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(0) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const FL = { insider_selling_large_sale: 'large sale', insider_selling_large_percent: 'large % of holding sold', insider_selling_acceleration: 'selling accelerating',
      insider_selling_commencement_buyer: 'prior buyer now selling', insider_buying: 'buying', skilled_buyer: 'skilled buyer', insider_selling_cluster: 'cluster selling', insider_buying_cluster: 'cluster buying' };
    const fl = f => esc(FL[f] || String(f || '').replace(/^insider_/, '').replace(/_/g, ' '));
    const sevDot = s => s === 'red' ? '🔴' : s === 'orange' ? '🟠' : s === 'yellow' ? '🟡' : '🟢';
    const row = x => `<li>${sevDot(x.severity)} <b>${esc(x.t || '')}</b> ${esc(x.name || '')} <span class="sub">${esc([x.country, x.sector].filter(Boolean).join(' · '))} · mcap ${m$(x.mcap_usd)} · ${m$(x.advt_usd)}/day</span> · ${arr(x.flags).map(f => `<span class="chip">${fl(f)}</span>`).join(' ')}${x.summary ? `<div class="sub" style="margin-left:22px">${esc(x.summary)}${x.latest_date ? ' · ' + esc(fmtD(x.latest_date)) : ''}</div>` : ''}</li>`;
    const sells = arr(W.sells).slice(0, 12).map(row), buys = arr(W.buys).slice(0, 10).map(row);
    const head = `<div class="mg-co-sec"><div class="eyebrow" style="color:var(--ink)">Canary · global Tech, Industrials &amp; Materials · &gt;$1bn mcap · &gt;$70mm/day traded${W.window ? ' · ' + esc(W.window) : ''}${W.as_of ? ' · as of ' + esc(fmtD(W.as_of)) : ''}</div>${W.coverage ? `<p class="sub" style="margin:2px 0 4px">${esc(W.coverage)}</p>` : ''}</div>`;
    const sec2 = (t, note, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${t}</div>${note ? `<p class="sub" style="margin:2px 0 4px">${note}</p>` : ''}<ul class="b">${items.join('')}</ul></div>` : '';
    return head + sec2('🔻 Insider selling flagged', 'Canary flags: large sales, large % of holding, accelerating selling, prior buyers turning sellers. Red and orange first.', sells) +
      sec2('🟢 Insider buying flagged', 'Canary buying and skilled-buyer flags.', buys) +
      (!sells.length && !buys.length ? '<p class="sub">No Canary insider flags in this universe for the window.</p>' : '');
  }

"""


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    if NEEDS not in s:
        print("insider-signals v1 missing", file=sys.stderr); return 2
    for n, a in [("hook", HOOK_OLD), ("router", ROUTER)]:
        if s.count(a) != 1:
            print(f"anchor {n} found {s.count(a)} times", file=sys.stderr); return 2
    s = s.replace(HOOK_OLD, HOOK_NEW).replace(ROUTER, JS + ROUTER)
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
