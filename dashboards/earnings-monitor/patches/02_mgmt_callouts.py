#!/usr/bin/env python3
"""Add a Callouts panel to the top of Bobby Tech Daily's Management & insiders tab.
Usage: add_mgmt_callouts.py <index.html in> <index.html out>. Idempotent. Exit 2 if an anchor is missing."""
import sys

MARKER = "/* mgmt-callouts v1 */"
NAV = '<a href="#mgmt/canary">Canary data sets</a></nav>`;'
NAV_NEW = NAV + "\n      h += mgCallouts(M, I, Q);"
ROUTER = "  // ================= ROUTER ================="

JS = r"""
  """ + MARKER + r"""
  // Callouts for the Management & insiders tab: rank what matters out of ~100 companies' insider trades and
  // the Canary question lists, so the top of the tab says what to look at first.
  function mgCallouts(M, I, Q) {
    const DAY = 864e5, now = Date.now();
    const days = d => (now - new Date(d + 'T12:00:00').getTime()) / DAY;
    const csuite = s => /\b(CEO|CFO|COO|CTO|Chief|Chair(man|woman)?|President|Founder)\b/i.test(s || '');
    const sponsor = s => /sponsor|major holder|10% owner|beneficial owner/i.test(s || '');
    const isBuy = x => /buy|purchase/i.test(x.buy_sell || x.type || '');
    const m$ = v => { if (v == null || !isFinite(v)) return '–'; const a = Math.abs(v); return (v < 0 ? '−$' : '$') + (a >= 1e9 ? (a / 1e9).toFixed(1) + 'bn' : a >= 1e6 ? (a / 1e6).toFixed(1) + 'm' : (a / 1e3).toFixed(0) + 'k'); };
    const cos = arr(I.companies);
    const trades = [];
    cos.forEach(c => arr(c.notable).forEach(x => { if (x.date) trades.push({ ...x, t: x.t || c.t, name: x.name || c.name, tier: c.tier, co: c }); }));
    // caveated rows (e.g. possible off-market transfers) never lead; they go to "verify"
    const seenV = new Set(), verify = trades.concat(arr(I.top_buys), arr(I.top_sells)).filter(x => x.caveat && !seenV.has(x.t + x.insider + x.date) && seenV.add(x.t + x.insider + x.date));
    const clean = trades.filter(x => !x.caveat);
    const score = x => (x.value_usd || 0) * (csuite(x.title) ? 3 : 1) * (x.plan_10b5_1 === false ? 1.5 : 1) * (x.tier === 1 ? 1.5 : 1);
    const buys30 = clean.filter(x => isBuy(x) && days(x.date) <= 30).sort((a, b) => score(b) - score(a));
    const sells30 = clean.filter(x => !isBuy(x) && days(x.date) <= 30 && x.plan_10b5_1 !== true && !sponsor(x.title) && csuite(x.title)).sort((a, b) => score(b) - score(a));
    // a buy below the same insider's earlier buy price = adding on weakness
    const lowerAdd = x => clean.some(y => y !== x && isBuy(y) && y.insider === x.insider && y.t === x.t && y.date < x.date && y.price && x.price && x.price < y.price * 0.9);
    const tag = x => [csuite(x.title) ? 'C-suite' : (x.title || 'insider'), x.plan_10b5_1 === false ? 'open-market' : x.plan_10b5_1 === true ? '10b5-1 plan' : '', lowerAdd(x) ? 'adding lower' : '', (x.co && x.co.buyers_6m >= 2) ? x.co.buyers_6m + ' buyers in 6M' : ''].filter(Boolean).join(' · ');
    const line = (dot, x) => `<li>${dot} ${tk(x.t)} <b>${esc(x.insider || '')}</b> ${isBuy(x) ? 'bought' : 'sold'} <b>${m$(x.value_usd)}</b>${x.price ? ' at ' + esc(x.price) : ''} <span class="sub">${esc(fmtD(x.date))} · ${esc(tag(x))}</span></li>`;
    // inflections: 30-day buying against 6-month net selling, and clusters
    const turning = cos.filter(c => (c.buys_30d || {}).value_usd > 0 && (c.net_6m_usd || 0) < 0 && !arr(c.notable).some(x => x.caveat));
    const clusters = cos.filter(c => (c.buyers_6m || 0) >= 2 && !turning.includes(c) && !arr(c.notable).some(x => x.caveat) && !arr(I.top_buys).some(x => x.caveat && x.t === c.t)).sort((a, b) => (b.buyers_6m - a.buyers_6m) || ((b.buys_6m || {}).value_usd - (a.buys_6m || {}).value_usd));
    // ask this week: covered names reporting in the next 10 days, with their first Canary question
    const qcos = arr(Q && Q.companies), up = arr((D.prep || {}).upcoming).filter(u => { const d = -days(u.date); return d >= -0.5 && d <= 10 && (u.tier || 9) <= 2; }).sort((a, b) => a.date.localeCompare(b.date));
    const key = t => String(t || '').toUpperCase().split(' ')[0];
    const ask = up.map(u => { const c = qcos.find(q => key(q.t) === key(u.ticker)); const q0 = c && arr(c.questions)[0]; return q0 ? { u, q: q0 } : null; }).filter(Boolean).slice(0, 6);
    const top = buys30.find(x => csuite(x.title)) || buys30[0];
    const sec = (title, items) => items.length ? `<div class="mg-co-sec"><div class="eyebrow">${title}</div><ul class="b">${items.join('')}</ul></div>` : '';
    const body = [
      top ? `<p class="mg-co-top">🎯 <b>Biggest signal:</b> ${tk(top.t)} ${esc(top.name || '')}: <b>${esc(top.insider || '')}</b> (${esc(top.title || 'insider')}) bought <b>${m$(top.value_usd)}</b>${top.price ? ' at ' + esc(top.price) : ''} on ${esc(fmtD(top.date))}${lowerAdd(top) ? ', adding below an earlier buy' : ''}.</p>` : '',
      sec('🟢 Insider buying, last 30 days', buys30.filter(x => x !== top).slice(0, 5).map(x => line('🟢', x))),
      sec('🔴 Discretionary C-suite selling, last 30 days', sells30.slice(0, 5).map(x => line('🔴', x))),
      sec('🔄 Inflections', turning.slice(0, 3).map(c => `<li>🔄 ${tk(c.t)} insiders buying in the last 30 days (<b>${m$((c.buys_30d || {}).value_usd)}</b>) after net selling of <b>${m$(c.net_6m_usd)}</b> over 6 months</li>`)
        .concat(clusters.slice(0, 3).map(c => `<li>👥 ${tk(c.t)} cluster: <b>${c.buyers_6m}</b> insiders bought <b>${m$((c.buys_6m || {}).value_usd)}</b> in 6 months</li>`))),
      sec('❓ Ask this week (reporting in the next 10 days)', ask.map(a => `<li>${tk(a.u.ticker)} <span class="sub">${esc(fmtD(a.u.date))}${a.u.time ? ' ' + esc(a.u.time) : ''} · ${esc(a.q.theme || '')}</span><br>${esc(String(a.q.q || '').slice(0, 260))}${String(a.q.q || '').length > 260 ? '…' : ''}</li>`)),
      sec('⚠️ Verify before acting', verify.slice(0, 3).map(x => `<li>${tk(x.t)} ${esc(x.insider || '')} ${m$(x.value_usd)} on ${esc(fmtD(x.date))}: ${esc(x.caveat)}</li>`))
    ].join('');
    if (!body) return '';
    return `<section class="panel mg-callouts"><div class="panel-h"><h2>📢 Callouts</h2><span class="sub">ranked from ${cos.length} companies' insider trades${I.as_of ? ' as of ' + esc(fmtD(I.as_of)) : ''}${qcos.length ? ' and ' + qcos.length + ' Canary question sets' : ''}</span></div>${body}</section>`;
  }

"""

CSS_ANCHOR = ".mg-q { margin: 4px 0 8px;"
CSS = """.mg-callouts { border-left: 3px solid var(--accent); }
.mg-callouts .mg-co-top { margin: 0; font-size: 14px; max-width: 110ch; }
.mg-callouts .mg-co-sec ul.b { margin-top: 4px; }
"""


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        open(dst, "w", encoding="utf-8").write(s); print("already present"); return 0
    for n, a in [("nav", NAV), ("router", ROUTER), ("css", CSS_ANCHOR)]:
        if s.count(a) != 1:
            print(f"anchor {n} found {s.count(a)} times", file=sys.stderr); return 2
    s = s.replace(NAV, NAV_NEW).replace(ROUTER, JS + ROUTER).replace(CSS_ANCHOR, CSS + CSS_ANCHOR)
    open(dst, "w", encoding="utf-8").write(s); print("added"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
