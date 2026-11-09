#!/usr/bin/env python3
"""Add the Twitter digest to the 𝕏 Feed tab of a saved copy of the Bobby Tech Daily index.html.

Usage: python3 add_twitter_tab.py <index.html in> <index.html out>

Idempotent: if the page already has the tab (marker below), it copies the file unchanged and exits 0.
The tab renders run records live from the page database (collection `twitter_runs`),
so normal runs only write a record and never republish the page.
Exits 2 if an anchor it needs is missing (the page layout changed): stop and tell Bobby.
"""
import sys

MARKER = "/* twitter-digest tab v2 */"

TWLINK_V2 = "const h = (String(u).match(/x\\.com\\/([^/]+)/) || [])[1] || 'post';\n    return `<a class=\"ext\" href=\"${esc(u)}\" target=\"_blank\" rel=\"noopener\">@${esc(h)}</a>`; }).join(' ');"
TWLINK_V2B = "const h = (String(u).match(/x\\.com\\/([^/]+)/) || [])[1];\n    const lb = h ? '@' + h : /notion\\.(so|com)/.test(String(u)) ? 'Notion page' : 'source';\n    return `<a class=\"ext\" href=\"${esc(u)}\" target=\"_blank\" rel=\"noopener\">${esc(lb)}</a>`; }).join(' ');"
CSS_ANCHOR = ".x-dp td { vertical-align: top; }"
ROUTER_ANCHOR = "// ================= ROUTER ================="
PAINT_OLD = "let h = top + `<section class=\"panel\"><div class=\"ctl\">`"
PAINT_NEW = "let h = top + twDigest() + `<section class=\"panel\"><div class=\"ctl\">`"
ALIAS_OLD = "if (v === 'themes' || v === 'pipeline') v = 'ideas';"
ALIAS_NEW = "if (v === 'themes' || v === 'pipeline') v = 'ideas'; if (v === 'twitter') v = 'x';"

CSS = """
""" + MARKER + """
#v-x .tw-runs { display: flex; flex-direction: column; gap: 14px; }
#v-x .tw-hot { border-color: var(--warn); box-shadow: inset 3px 0 0 var(--warn); }
#v-x .tw-sec h3 { display: flex; gap: 8px; align-items: baseline; }
#v-x .tw-sides { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 8px 18px; }
#v-x .tw-delta.up { color: var(--pos); } #v-x .tw-delta.dn { color: var(--neg); }
#v-x .tw-sb { font-family: var(--f-mono); font-size: 11.5px; color: var(--muted); white-space: nowrap; }
#v-x .tw-old > summary { font-size: 13px; text-transform: none; letter-spacing: 0; color: var(--accent); }
#v-x b.n { color: var(--ink); }
"""

JS = """
  """ + MARKER + """
  const TW = { list: [], ready: false, err: '' };
  if (window.claude && typeof window.claude.use === 'function') {
    window.claude.use('db').then(db => {
      if (!db) { TW.err = 'Twitter runs need the page open on claude.ai.'; return; }
      db.collection('twitter_runs').onSnapshot(snap => {
        TW.list = snap.docs.map(d => ({ id: d.id, ...d.data() })).sort((a, b) => String(b.id).localeCompare(String(a.id)));
        TW.ready = true; if ((location.hash || '').startsWith('#x')) renderX(false);
      }, err => { TW.err = 'Could not load digest runs: ' + ((err && err.code) || 'error'); if ((location.hash || '').startsWith('#x')) renderX(false); });
    }).catch(() => { TW.err = 'Twitter runs are not available in this view.'; });
  } else TW.err = 'Twitter runs need the page open on claude.ai.';
  const twDot = i => ({ very_positive: '🟢🟢', positive: '🟢', mixed: '🔵', negative: '🔴', very_negative: '🔴🔴' })[i] || '';
  const twLinks = xs => (xs || []).filter(Boolean).map(u => { const h = (String(u).match(/x\\.com\\/([^/]+)/) || [])[1];
    const lb = h ? '@' + h : /notion\\.(so|com)/.test(String(u)) ? 'Notion page' : 'source';
    return `<a class="ext" href="${esc(u)}" target="_blank" rel="noopener">${esc(lb)}</a>`; }).join(' ');
  const twTk = (t, imp) => t ? `<span class="tk-chip ${/positive/.test(imp || '') ? 'up' : /negative/.test(imp || '') ? 'dn' : ''}">${esc(t)}</span>` : '';
  const twBold = s => esc(s || '').replace(/\\*\\*(.+?)\\*\\*/g, '<b class="n">$1</b>');
  const twLine = x => `<div class="li"><div class="body">${twDot(x.impact)} ${twTk(x.tk, x.impact)} ${twBold(x.text)} ${twLinks(x.urls)}</div><div class="side">${esc(x.date || '')}</div></div>`;
  function twRun(r, open) {
    const c = r.callouts || {}, h = r.hot_topic;
    const sec = (title, inner) => inner ? `<section class="panel tw-sec"><h3>${title}</h3>${inner}</section>` : '';
    const list = xs => (xs && xs.length) ? `<div class="list">${xs.map(twLine).join('')}</div>` : '';
    const hot = h ? `<section class="panel tw-hot"><span class="eyebrow">🔥 Hot topic</span><h2>${twBold(h.title)}</h2>
      <p class="lede">${twBold(h.what)}</p>
      <div class="tw-sides"><div><b>Bull:</b> ${twBold(h.bull)}</div><div><b>Bear:</b> ${twBold(h.bear)}</div></div>
      <div>${(h.tickers || []).map(t => twTk(t.tk, t.impact)).join(' ')} <span class="muted">· why now: ${esc(h.why_now || '')} · ${esc(String(h.accounts ?? ''))} accounts${h.accounts_delta != null ? ` (${h.accounts_delta >= 0 ? '+' : ''}${esc(String(h.accounts_delta))} vs last run)` : ''}</span></div>
      <div>${twLinks(h.urls)}</div></section>` : '';
    const callouts = [c.biggest ? `<div class="eyebrow">🎯 Biggest datapoint</div>${list([c.biggest])}` : '',
      c.positive && c.positive.length ? `<div class="eyebrow">🟢 Most positive</div>${list(c.positive)}` : '',
      c.negative && c.negative.length ? `<div class="eyebrow">🔴 Most negative</div>${list(c.negative)}` : '',
      c.inflections && c.inflections.length ? `<div class="eyebrow">🔄 Inflections</div>${list(c.inflections)}` : ''].join('');
    const changing = (r.changing || []).map(x => `<div class="li"><div class="body">${twTk(x.tk, x.impact)} <b>${esc(x.what || '')}</b>: ${twBold(x.was)} → ${twBold(x.now)} ${twLinks(x.urls)}</div><div class="side">${esc(x.date || '')}</div></div>`).join('');
    const chat = r.chatter || [];
    const dl = d => d == null ? '<span class="muted">new</span>' : `<span class="tw-delta ${d > 0 ? 'up' : d < 0 ? 'dn' : ''}">${d > 0 ? '+' : ''}${d}</span>`;
    const chatT = chat.length ? `<div class="tbl-wrap"><table><thead><tr><th>Ticker / topic</th><th class="n">Mentions</th><th class="n">Accounts</th><th class="n">Δ vs last</th><th>Gist</th></tr></thead><tbody>${chat.map(x =>
      `<tr><td>${x.kind === 'ticker' ? twTk(x.key) : esc(x.key)}</td><td class="n">${esc(String(x.mentions))}</td><td class="n">${esc(String(x.accounts))}</td><td class="n">${dl(x.delta)}</td><td>${esc(x.gist || '')}</td></tr>`).join('')}</tbody></table></div>` : '';
    const themes = (r.themes || []).map(t => `<details ${open ? 'open' : ''}><summary>${esc(t.title)}</summary>
      <ul class="b"><li><b>Changing:</b> ${twBold(t.changing)}</li><li><b>Benefits:</b> ${twBold(t.benefits)}</li><li><b>Loses:</b> ${twBold(t.loses)}</li>
      <li><b>Evidence:</b> ${twBold(t.evidence)} ${twLinks(t.urls)}</li><li><b>Wrong if:</b> ${twBold(t.wrong_if)}</li></ul></details>`).join('');
    const dps = r.datapoints || [], byTk = {};
    dps.forEach(d => (byTk[d.tk || '—'] = byTk[d.tk || '—'] || []).push(d));
    const dpH = Object.keys(byTk).sort().map(t => `<details><summary>${esc(t)} · ${byTk[t].length}</summary><div class="list">${byTk[t].map(d =>
      `<div class="li"><div class="body">${twDot(d.impact)} <span class="chip">${esc(d.field_key || '')}</span> <span class="chip out">${esc(d.confidence || '')}</span> ${twBold(d.text)}<br><span class="muted">${esc(d.primary_source || '')} via ${twLinks(d.urls)}</span></div>
       <div class="side">${esc(d.date || '')}<br><span class="tw-sb">${d.sb ? 'SB #' + esc(String(d.sb)) : d.held ? 'Held: ' + esc(d.held) : 'staged'}</span></div></div>`).join('')}</div></details>`).join('');
    const sb = r.supabase || {}, inp = r.inputs || {};
    const inputs = `<details><summary>📥 Inputs</summary><ul class="b">
      ${(inp.pages || []).map(p => `<li><a class="ext" href="${esc(p.url)}" target="_blank" rel="noopener">${esc(p.title)}</a> · ${esc(String(p.posts_read ?? '?'))} read · ${esc(String(p.kept ?? '?'))} kept${p.archived ? ' · archived' : ''}</li>`).join('')}
      ${(inp.skipped || []).map(p => `<li class="muted">Skipped: ${esc(p.title)} (${esc(p.reason || '')})</li>`).join('')}
      ${(inp.notes || []).map(n => `<li>${esc(n)}</li>`).join('')}
      <li>📤 Supabase: ${esc(String(sb.loaded ?? 0))} loaded${sb.ids ? ' (' + esc(sb.ids) + ')' : ''} · ${esc(String(sb.held ?? 0))} held · ${esc(String(sb.dups ?? 0))} duplicates · ${esc(String(sb.failed ?? 0))} failed</li>
      </ul><p class="muted">${esc(r.footer || '')}</p></details>`;
    return `<div class="tw-runs">${hot}
      ${sec('📢 Callouts', callouts)}${sec('🔄 What\\'s changing', changing ? `<div class="list">${changing}</div>` : '')}
      ${sec('📈 Most talked about <span class="muted" style="font-size:12px;font-weight:400">mentions in the Grok pages this run, not all of X</span>', chatT)}
      ${sec('🧵 Key themes', themes)}${sec('📊 Datapoints <span class="muted" style="font-size:12px;font-weight:400">' + dps.length + ' kept</span>', dpH)}
      <section class="panel">${inputs}</section></div>`;
  }
  function twDigest() {
    const hd = `<div class="vh"><div class="row"><h2>🧵 Twitter digest</h2><span class="src">twitter-digest skill · filtered datapoints, what changed vs the last run, mention leaderboard</span></div></div>`;
    if (!TW.ready) return hd + `<section class="panel"><p class="sub">${esc(TW.err || 'Loading digest runs…')}</p></section>`;
    if (!TW.list.length) return hd + '<section class="panel"><p class="sub">No digest runs yet. Say "run twitter" to Claude.</p></section>';
    const [cur, ...old] = TW.list;
    const lbl = r => `${esc(String(r.id).replace(/T(\\d\\d)(\\d\\d)$/, ' $1:$2'))} ET · ${esc((r.window && r.window.start) || '')} → ${esc((r.window && r.window.end) || '')}`;
    return hd.replace('</span></div></div>', ` · latest ${lbl(cur)}</span></div></div>`) + twRun(cur, true)
      + (old.length ? `<section class="panel"><h3>Earlier digest runs</h3>${old.slice(0, 14).map(r => `<details class="tw-old"><summary>${lbl(r)}${r.hot_topic ? ' · 🔥 ' + esc(r.hot_topic.title) : ''}</summary>${twRun(r, false)}</details>`).join('')}</section>` : '')
      + `<div class="vh"><div class="row"><h2>📡 Raw run</h2><span class="src">the Grok page as written, read live from Notion</span></div></div>`;
  }

  """


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    if MARKER in s:
        fixed = s.replace(TWLINK_V2, TWLINK_V2B)
        open(dst, "w", encoding="utf-8").write(fixed)
        print("already present" + (" (link labels upgraded)" if fixed != s else ""))
        return 0
    for name, a in [("css", CSS_ANCHOR), ("router", ROUTER_ANCHOR), ("paint", PAINT_OLD), ("alias", ALIAS_OLD)]:
        if s.count(a) != 1:
            print(f"anchor '{name}' found {s.count(a)} times; page layout changed", file=sys.stderr)
            return 2
    s = s.replace(CSS_ANCHOR, CSS_ANCHOR + CSS)
    s = s.replace(ROUTER_ANCHOR, JS + ROUTER_ANCHOR)
    s = s.replace(PAINT_OLD, PAINT_NEW).replace(ALIAS_OLD, ALIAS_NEW)
    open(dst, "w", encoding="utf-8").write(s)
    print("added")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
