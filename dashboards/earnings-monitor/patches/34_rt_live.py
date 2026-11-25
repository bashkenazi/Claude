"""Routines tab: show every run's full output, including runs written after the morning build.
- Newer run pages (e.g. 13:20 PM digests) are found live in Notion and added to the run picker.
- A run whose full page is not in the build is fetched live from Notion and rendered in full.
Uses the page's existing Notion connector (mcp) and the X-feed markdown renderer (xParse/xInline/xHtml).
Marker "rt-live v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'rt-live v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)

JS = r"""/* rt-live v1: newer runs and full run pages live from Notion (anything written after the morning build) */
const RTX = { mcp: undefined, mp: null, runs: new Map(), pages: new Map() };
const rtxId = u => (String(u || '').match(/([0-9a-f]{32})/i) || [])[1] || '';
function rtxMcp() {
  if (RTX.mcp !== undefined) return Promise.resolve(RTX.mcp);
  if (!RTX.mp) RTX.mp = (window.claude && typeof window.claude.use === 'function' ? window.claude.use('mcp').catch(() => null) : Promise.resolve(null)).then(m => (RTX.mcp = m || null));
  return RTX.mp;
}
const rtxCall = (m, tool, input) => m.callTool('Notion', tool, input, { cache: { staleTime: 5 * 60e3, gcTime: 864e5 } }).then(r => r.payload);
const rtxPrefix = t => String(t || '').replace(/^[^\w]+/u, '').split(/\s+[—–]\s+|\s+-\s+\d{4}-|\s*\(\d{4}-|\s+\d{4}-\d\d-\d\d/)[0].trim();
const rtxET = ts => { try { return new Date(ts).toLocaleString('sv-SE', { timeZone: 'America/New_York' }).replace(' ', 'T').slice(0, 16); } catch (e) { return ''; } };
function rtxRe() { if ((location.hash || '').startsWith('#routines')) renderRoutines(); }
function rtxRuns(cur) {
  const base = arr(cur.runs); if (!base.length) return base;
  const k = cur.key;
  if (!RTX.runs.has(k)) {
    RTX.runs.set(k, null);
    const pre = rtxPrefix(base[0].title), d0 = String(base[0].date || '').slice(0, 10), have = new Set(base.map(r => rtxId(r.url)));
    rtxMcp().then(m => (m && pre && d0) ? rtxCall(m, 'notion-search', { query: pre, query_type: 'internal', page_size: 10, max_highlight_length: 0, filters: { created_date_range: { start_date: d0 } } }) : null)
      .then(r => {
        const add = arr(r && r.results).filter(p => (p.type || 'page') === 'page' && rtxPrefix(p.title) === pre && rtxId(p.url) && !have.has(rtxId(p.url)))
          .map(p => { const et = rtxET(p.timestamp); return { title: String(p.title || '').replace(/^[^\w]+/u, ''), url: p.url, date: (String(p.title || '').match(/\d{4}-\d\d-\d\d/) || [et.slice(0, 10)])[0], created: et, window: 'Written after the morning build · loaded live from Notion', live: true }; })
          .filter(x => x.date >= d0);
        RTX.runs.set(k, add); if (add.length) rtxRe();
      }).catch(() => RTX.runs.set(k, []));
  }
  const extra = RTX.runs.get(k) || [];
  return extra.length ? extra.concat(base).sort((a, b) => String(b.created || b.date).localeCompare(String(a.created || a.date))) : base;
}
function rtxSections(md) {
  const tree = xParse(md), secs = []; let cur = null;
  tree.forEach(b => {
    if (b.t === 'h' && b.lvl <= 2) { cur = { title: xInline(b.text), blocks: [] }; secs.push(cur); return; }
    if (b.t === 'toggle') { secs.push({ title: xInline(b.title), blocks: b.kids }); cur = null; return; }
    if (!cur) { const last = secs[secs.length - 1]; if (last && last.tail) cur = last; else { cur = { title: secs.length ? 'More' : 'Summary', blocks: [], tail: true }; secs.push(cur); } }
    cur.blocks.push(b);
  });
  return secs.filter(x => x.blocks.length).map(x => ({ title: x.title, html: xHtml(x.blocks) }));
}
function rtxFull(sel) {
  const id = rtxId(sel && sel.url); if (!id) return null;
  if (RTX.pages.has(id)) return RTX.pages.get(id);
  RTX.pages.set(id, null);
  rtxMcp().then(m => m ? rtxCall(m, 'notion-fetch', { id }) : Promise.reject(new Error('no connector'))).then(r => {
    let txt = typeof r === 'string' ? r : (r && (r.text || r.content || r.markdown)) || '';
    const mm = txt.match(/<content>([\s\S]*?)<\/content>/); if (mm) txt = mm[1];
    txt = txt.replace(/<toggle\s+heading="h\d"[^>]*>/g, '<toggle>');
    const secs = rtxSections(txt);
    RTX.pages.set(id, secs.length ? { title: String((r && r.title) || sel.title || ''), sections: secs, live: true } : false); rtxRe();
  }).catch(() => { RTX.pages.set(id, false); rtxRe(); });
  return null;
}
function renderRoutines() {"""
rep("function renderRoutines() {", JS)
rep("const runs = lim(arr(cur.runs).filter(r => inWin(r.date, null)), 14);",
    "const runs = lim(rtxRuns(cur).filter(r => inWin(r.date, null)), 14);")
rep("const FULL = window.__FULL || {}, fp = sel && FULL[String(sel.url || '').split('?')[0]];",
    "const FULL = window.__FULL || {}, fp = (sel && (FULL[String(sel.url || '').split('?')[0]] || (window.__FULL ? rtxFull(sel) : null))) || null;")
rep(": (window.__FULL ? `<section class=\"panel\">${none('The full page for this run is not in this build yet.')}${link(sel.url, 'Open in Notion')}</section>` : `<section class=\"panel\"><p class=\"sub\">Loading the full page…</p></section>`);",
    ": (window.__FULL && RTX.pages.get(rtxId(sel.url)) === false ? `<section class=\"panel\">${none('Could not load this run from Notion here (open the page on claude.ai with your Notion connector allowed).')}${link(sel.url, 'Open in Notion')}</section>` : `<section class=\"panel\"><p class=\"sub\">Loading the full page${window.__FULL ? ' from Notion' : ''}…</p></section>`);")
rep("${esc(fmtD(r.date))}${r.created ? ' <span class=\"sub\">' + esc(String(r.created).slice(11, 16)) + '</span>' : ''}</a>`).join('')}</div>` : '';",
    "${esc(fmtD(r.date))}${r.created ? ' <span class=\"sub\">' + esc(String(r.created).slice(11, 16)) + (r.live ? ' · new' : '') + '</span>' : ''}</a>`).join('')}</div>` : '';")
open(P, 'w', encoding='utf-8').write(s); print('applied')
