"""Section 10: pools-of-capital table (outstanding, issuance, AI draw, Tomorrow X panel) from page db ai/one_page.pools. Marker "op-pools v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-pools v1' in s: print('already'); sys.exit(0)
old = "h += sec('mkt', '10 · Size of the debt markets', 'SIFMA, PFI, White & Case, T. Rowe Price, Barclays via SFA',\n`"
assert s.count(old) == 1
new = """/* op-pools v1 */ const PO = d.pools;
h += sec('mkt', '10 · Pools of capital and the size of the debt markets', 'Broker research via AlphaSense (Nov 2026), SIFMA, AIMA, Fed, Apollo; Tomorrow X AI credit panel',
(PO ? `<h3>Pools of capital: how big each is and how much AI draws</h3><div class="tbl-wrap"><table class="op-t op-pools"><thead><tr>${PO.cols.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${PO.rows.map(r => { const c = Array.isArray(r) ? r : r.c, b = !Array.isArray(r) && r.b; return `<tr${b ? ' class="th-b"' : ''}>${c.map((x, i) => `<td${i === c.length - 1 ? ' class="note"' : ''}>${i === 0 ? '<b>' + esc(x) + '</b>' : esc(x)}</td>`).join('')}</tr>`; }).join('')}</tbody></table></div>
<p class="op-call">${esc(PO.note)}</p>${PO.panel ? `<div class="op-watch" style="border-left-color:var(--accent)"><b>${esc(PO.panel.title)}</b><ul>${PO.panel.points.map(p => `<li>${esc(p)}</li>`).join('')}</ul><span class="sub">${esc(PO.panel.src)}</span></div>` : ''}<h3>Debt market history</h3>` : '') +
`"""
s = s.replace(old, new)
css = """
/* op-pools v1 */
table.op-pools td { white-space: normal; min-width: 150px; max-width: 280px; font-size: 12px; line-height: 1.4; vertical-align: top; }
table.op-pools td:first-child { min-width: 170px; }
"""
i = s.find('/* op-layout v1 */\n.op-sec-h'); assert i > 0; s = s[:i] + css + s[i:]
open(P, 'w', encoding='utf-8').write(s); print('applied')
