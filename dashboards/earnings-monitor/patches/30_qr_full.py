"""Quarterly review tab: the default build carries every revenue segment, the company's operating KPIs
(backlog, orders/bookings, RPO, ARR, units, ASP, customers...) and profitability by division; saved reviews
get any missing rows merged in on load. Marker "qr-full v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'qr-full v1' in s: print('already'); sys.exit(0)
a = s.index("const common = await list(null);")
b_tok = "return { va_company_id: id, va_ticker: vt, rows, nq: 12, auto: true };"
b = s.index(b_tok, a) + len(b_tok)
NEW = r"""/* qr-full v1: segments, operating KPIs and profitability by division in every review */
const uniq = xs => { const m = new Map(); xs.forEach(k => { if (k && k.kpi_id && !m.has(k.kpi_id)) m.set(k.kpi_id, k); }); return [...m.values()]; };
const many = async kws => uniq((await Promise.all(kws.map(k => list(k)))).flat());
const common = await list(null);
const BAD = /cost|expense|tax|share(s|holder)?\b|stock|cash|debt|lease|amorti|depreci|payable|receivable|inventor|goodwill|adjust|growth|guidance|deferred|impair|restructur|interest|dividend|repurchase|gain|loss on|fx|currency|accumulated|retained|change in|% |percent|y\/y|yoy|q\/q|mix\b/i;
const rows = [], add = (k, extra) => { if (k && !rows.some(x => x.kind === 'kpi' && x.kpi_id === k.kpi_id)) rows.push(Object.assign({ kind: 'kpi', kpi_id: k.kpi_id, name: k.kpi_name, label: k.kpi_name }, extra || {})); };
const revPool = uniq(common.concat(await many(['Revenue', 'Net sales', 'Sales'])));
const rev = revPool.find(k => /^(total )?(net )?(revenues?|sales)( - operating)?$/i.test(k.kpi_name)) || revPool.find(k => /revenue|sales/i.test(k.kpi_name) && !/ - |mix|cost|deferred/i.test(k.kpi_name));
add(rev, { role: 'rev', label: 'Total revenue' });
// 1. revenue segments named "Revenue - X" / "Net sales - X"
const segRx = /^(total )?(net )?(revenues?|sales) ?- ?(?!operating$)(.+)$/i;
const segK = revPool.filter(k => segRx.test(k.kpi_name) && !BAD.test(k.kpi_name) && !/miscellaneous|^other$|eliminat|intersegment|unallocated|corporate/i.test(k.kpi_name.replace(segRx, '$4')))
  .sort((x, y) => (y.is_common - x.is_common) || (y.period_count - x.period_count)).slice(0, 16);
segK.forEach(k => add(k, { seg: true, label: k.kpi_name.replace(segRx, '$4') }));
// 2. profitability by division (operating income / segment profit / EBIT / gross profit / margins with a " - <segment>" suffix)
const profPool = await many(['Operating income', 'Operating profit', 'Segment', 'EBIT', 'Gross profit', 'Operating margin', 'Contribution']);
const SKIP = /^(operating|unallocated.*|corporate.*|other.*|eliminations?|total|reconcil.*|intersegment.*)$/i;
const sufOf = n => { const p = n.split(' - ').map(x => x.trim()); const last = p[p.length - 1]; return p.length > 1 && !SKIP.test(last) ? last : null; };
const bySeg = new Map();
profPool.filter(k => !/adjust|total adjust|sbc|amorti|tax|non-?operating/i.test(k.kpi_name)).forEach(k => { const sfx = sufOf(k.kpi_name); if (!sfx) return; const isM = /margin/i.test(k.kpi_name), isGP = /gross/i.test(k.kpi_name), op = / - operating - /i.test(k.kpi_name) ? 1 : 0;
  const o = bySeg.get(sfx) || {}; const slot = isGP ? (isM ? 'gm' : 'gp') : (isM ? 'om' : 'oi'); if (!o[slot] || op > (o[slot].op || 0)) o[slot] = Object.assign({ op }, k); bySeg.set(sfx, o); });
// segments that only appear as bare names (e.g. "Infrastructure solutions group (ISG)"): find their revenue KPI
const segRev = new Map(rows.filter(r => r.seg).map(r => [r.label.toLowerCase(), r]));
const findRev = async sfx => { const hit = [...segRev.entries()].find(([l]) => l === sfx.toLowerCase() || l.includes('(' + sfx.toLowerCase() + ')')); if (hit) return hit[1];
  const c = (await list(sfx)).filter(k => !BAD.test(k.kpi_name) && !/income|profit|margin|ebit|asp|units|price/i.test(k.kpi_name) && (k.kpi_name.toLowerCase() === sfx.toLowerCase() || k.kpi_name.includes('(' + sfx + ')')));
  if (!c.length) return null; add(c[0], { seg: true, label: sfx }); const r = rows[rows.length - 1]; segRev.set(sfx.toLowerCase(), r); return r; };
const divRows = [];
for (const [sfx, o] of [...bySeg.entries()].slice(0, 8)) {
  const sr = await findRev(sfx);
  if (o.oi) { divRows.push({ kind: 'kpi', kpi_id: o.oi.kpi_id, name: o.oi.kpi_name, label: 'EBIT · ' + sfx }); if (sr) divRows.push({ kind: 'ratio', num: o.oi.kpi_id, den: sr.kpi_id, label: 'EBIT margin · ' + sfx }); else if (o.om) divRows.push({ kind: 'kpi', kpi_id: o.om.kpi_id, name: o.om.kpi_name, label: 'EBIT margin · ' + sfx }); }
  else if (o.om) divRows.push({ kind: 'kpi', kpi_id: o.om.kpi_id, name: o.om.kpi_name, label: 'EBIT margin · ' + sfx });
  if (o.gm && !o.oi && !o.om) divRows.push({ kind: 'kpi', kpi_id: o.gm.kpi_id, name: o.gm.kpi_name, label: 'Gross margin · ' + sfx });
}
// sub-segments that only show up through their unit or ASP KPIs (e.g. "Units - Commercial" -> "Commercial")
const subSfx = [...new Set(uniq(common.concat(await many(['Units', 'ASP']))).map(k => (k.kpi_name.match(/^(?:blended )?(?:units|asp|shipments)\s*-\s*(.+)$/i) || [])[1]).filter(Boolean))].slice(0, 10);
for (const sfx of subSfx) { if (!bySeg.has(sfx)) await findRev(sfx); }
// 3. operating KPIs the company reports
const KW = ['backlog', 'orders', 'bookings', 'book-to-bill', 'RPO', 'remaining performance', 'ARR', 'recurring', 'retention', 'customers', 'subscribers', 'users', 'units', 'shipments', 'ASP', 'GMV', 'utilization', 'bit'];
const kpiK = (await many(KW)).filter(k => !BAD.test(k.kpi_name) && !rows.some(r => r.kpi_id === k.kpi_id) && !/income|profit|margin|ebit|eps\b/i.test(k.kpi_name))
  .sort((x, y) => (/backlog|order|booking|rpo|remaining performance|arr\b|recurring/i.test(y.kpi_name) - /backlog|order|booking|rpo|remaining performance|arr\b|recurring/i.test(x.kpi_name)) || (y.is_common - x.is_common) || (y.period_count - x.period_count)).slice(0, 14);
const kpiRows = kpiK.map(k => ({ kind: 'kpi', kpi_id: k.kpi_id, name: k.kpi_name, label: k.kpi_name, kpi: true }));
rows.push(...kpiRows);
// 4. company profitability
const pick = (xs, pref) => xs.find(k => pref.test(k.kpi_name)) || xs[0];
const gp = pick(profPool.filter(k => /gross profit/i.test(k.kpi_name) && !/mix|margin|adjust|segment|product|service/i.test(k.kpi_name) && !sufOf(k.kpi_name.replace(/ - Operating$/i, ''))), / - Operating$/i);
if (gp) { add(gp, { role: 'gp', label: 'Gross profit' }); if (rev) rows.push({ kind: 'ratio', num: gp.kpi_id, den: rev.kpi_id, label: 'Gross margin' }); }
rows.push(...divRows.filter(r => r.kind === 'ratio' || !rows.some(x => x.kpi_id === r.kpi_id)));
const oi = pick(profPool.filter(k => /operating income|operating profit/i.test(k.kpi_name) && !/mix|margin|adjust|segment|non-?operating/i.test(k.kpi_name) && !sufOf(k.kpi_name.replace(/ - Operating$/i, ''))), / - Operating$/i) || pick(profPool.filter(k => /^EBIT\b/i.test(k.kpi_name) && !/margin|mix/i.test(k.kpi_name) && !sufOf(k.kpi_name.replace(/ - Operating$/i, ''))), /^EBIT( - Operating)?$/i);
if (oi) { add(oi, { role: 'oi', label: 'Operating income' }); if (rev) rows.push({ kind: 'ratio', num: oi.kpi_id, den: rev.kpi_id, label: 'Operating margin' }); }
const eb = pick((await list('EBITDA')).filter(k => /^(adjusted )?EBITDA/i.test(k.kpi_name) && !/margin|mix|adjust(ments)? in/i.test(k.kpi_name) && !sufOf(k.kpi_name.replace(/ - Operating$/i, ''))), / - Operating$/i);
if (eb) { add(eb, { label: 'EBITDA' }); if (rev) rows.push({ kind: 'ratio', num: eb.kpi_id, den: rev.kpi_id, label: 'EBITDA margin' }); }
const eps = pick((await list('EPS')).filter(k => /diluted/i.test(k.kpi_name)), / - Operating$/i);
if (eps) add(eps, { role: 'eps', label: 'EPS (diluted)' });
return { va_company_id: id, va_ticker: vt, rows, nq: 12, auto: true, qr_full: 1 };"""
s = s[:a] + NEW + s[b:]
# merge into saved reviews on load
old = "if (!cfg) cfg = await qrDefault(co, false);"
assert s.count(old) == 1
s = s.replace(old, """if (!cfg) cfg = await qrDefault(co, false);
else if (!cfg.qr_full) { try { const d = await qrDefault(co, false); if (d.va_company_id === cfg.va_company_id) { /* qr-full v1: add missing segments, KPIs and division profitability to a saved review */
  const has = r => cfg.rows.some(x => r.kind === 'ratio' ? (x.kind === 'ratio' && x.num === r.num && x.den === r.den) : (x.kind === 'kpi' && x.kpi_id === r.kpi_id));
  const ins = (r, after) => { let i = -1; cfg.rows.forEach((x, j) => { if (after(x)) i = j; }); if (i < 0) i = cfg.rows.findIndex(x => x.role === 'eps') - 1; if (i < -1) i = cfg.rows.length - 1; cfg.rows.splice(i + 1, 0, Object.assign({ added: 'qr-full' }, r)); };
  d.rows.filter(r => !r.role && !has(r)).forEach(r => {
    if (r.seg) ins(r, x => x.seg || x.role === 'rev');
    else if (r.kpi) ins(r, x => x.seg || x.kpi || x.role === 'rev');
    else if (/^(EBIT|Gross margin) ·|^EBIT margin ·/.test(r.label || '')) ins(r, x => /^(EBIT|OM|Gross margin)\\b|·/.test(x.label || '') && !x.seg || x.role === 'gp' || (x.kind === 'ratio' && /gross margin/i.test(x.label || '')));
    else ins(r, x => x.role === 'oi' || x.role === 'gp');
  });
  cfg.qr_full = 1; } } catch (e) {} }""")
open(P, 'w', encoding='utf-8').write(s); print('applied')
