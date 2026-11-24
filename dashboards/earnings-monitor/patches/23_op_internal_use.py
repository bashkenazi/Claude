"""AI one page: rentable GW = installed GW less per-company internal use, with a toggle and % per company
(Meta, Google, Microsoft, Amazon, SpaceX/xAI). Marker "op-internal-use v1". Applies to a page html or tabs.js."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-internal-use v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:90], s.count(old)); s = s.replace(old, new)

rep("const cumRent = Y.map((y, i) => i === 0 ? 1.625 : S.gw_cum[i] - (E.meta[i] || 0) - gp * (E.google_cum[i] || 0) - (E.amzn[i] || 0) - (E.msft[i] || 0));",
"""/* op-internal-use v1: GW kept for a company's own workloads are not rentable */
const IU = [['META', 'Meta', 100, 'All internal'], ['GOOGL', 'Google', 75, 'Mostly internal (DeepMind, Search, YouTube); split not disclosed'], ['MSFT', 'Microsoft', 20, '~20% internal (Copilot, M365); rest rented incl. OpenAI'], ['AMZN', 'Amazon', 20, '~20% internal (retail, Alexa); rest rented incl. Anthropic'], ['SPCX', 'SpaceX / xAI', 50, 'SpaceX says ~50% internal (Grok); unverified']];
const iuCo = k => { const c = [].concat((d.co && d.co.hs) || [], (d.co && d.co.neo) || []).find(x => x.k === k); return c ? (c.cum_m || c.cum_sa || Z()) : Z(); };
const iuOn = k => I['iu_on_' + k] == null ? 1 : +I['iu_on_' + k];
const iuPct = (k, def) => { const v = I['iu_pct_' + k]; return v == null || v === '' || isNaN(v) ? def : +v; };
const iuCum = {}; IU.forEach(([k, , def]) => { iuCum[k] = iuCo(k).map(v => nv(v) == null ? 0 : v * iuOn(k) * iuPct(k, def) / 100); });
const iuTot = Y.map((_, i) => IU.reduce((s, [k]) => s + (iuCum[k][i] || 0), 0));
const cumRent = Y.map((y, i) => i === 0 ? 1.625 : S.gw_cum[i] - iuTot[i]);""")
rep("const exMeta = exAmt(E.meta), exGoog = exAmt(E.google_cum.map(v => v * gp)), exAmzn = exAmt(E.amzn), exMsft = exAmt(E.msft);",
    "const exBy = {}; IU.forEach(([k]) => { exBy[k] = exAmt(iuCum[k]); });")
rep("""{ l: '(−) Meta, all internal', v: exMeta, ind: 1 }, { l: `(−) Google internal (${Math.round(gp * 100)}% of Google GW)`, v: exGoog, ind: 1, note: 'Model\\'s DeepMind GW ≈ 40-57%' },
{ l: '(−) Amazon internal (~15% of compute)', v: exAmzn, ind: 1 }, { l: '(−) Microsoft internal (~35% of compute)', v: exMsft, ind: 1 },""",
"""...IU.map(([k, nm, def]) => ({ l: `(−) ${nm} internal (${iuOn(k) ? iuPct(k, def) + '% of its GW' : 'off'})`, v: exBy[k], ind: 1, note: 'Inputs in section 6' })),""")
# top bar: Google input moves to section 6
rep("""${inp('google_pct', 'Google capex used internally', '%', 'Share of Google GW treated as internal (DeepMind/first-party) and taken out of the ROI capex base')}
""", "")
# section 6 controls + rows
rep("""${rin('rent_life_y', 'Rental life', I.rent_life_y || 6, 'yrs', 'Years each vintage earns rent; AI Economics uses 6')}</div>` +""",
"""${rin('rent_life_y', 'Rental life', I.rent_life_y || 6, 'yrs', 'Years each vintage earns rent; AI Economics uses 6')}</div>` +
  `<div class="op-bar op-iu" role="group" aria-label="Internal use by company: GW not available for rent"><span class="op-iu-h">Not for rent (internal use)</span>${IU.map(([k, nm, def, help]) => `<label class="op-l op-ck" title="${esc(help)}"><input type="checkbox" data-op="iu_on_${k}"${iuOn(k) ? ' checked' : ''}>${esc(nm)}</label><label class="op-l op-iu-p" title="${esc(help)}"><span><input class="op-in" type="number" inputmode="decimal" step="any" min="0" max="100" data-op="iu_pct_${k}" data-opt="1" placeholder="${def}" aria-label="${esc(nm)} internal share" value="${esc(I['iu_pct_' + k] == null ? '' : String(I['iu_pct_' + k]))}"${iuOn(k) ? '' : ' disabled'}>%</span></label>`).join('')}</div>` +""")
rep("""  { sep: 'Rentable GW only (excludes Meta, Google internal, Amazon and Microsoft internal use; inputs at top)' },
  { l: 'Rentable GW deployed in year', v: incRent, f: 'gw', ind: 1 },""",
"""  { sep: 'Not every GW is for rent: internal use by company (cumulative GW, AI Master capacity by host × internal %)' }].concat(IU.map(([k, nm, def, help]) => ({ l: `${nm}${iuOn(k) ? ` (${iuPct(k, def)}%)` : ' (off)'}`, v: iuCum[k], f: 'gw', ind: 1, note: esc(help) })), [
  { l: 'Internal GW, end of year', v: iuTot, f: 'gw', b: 1 }, { l: 'Rentable GW, end of year', v: cumRent, f: 'gw', b: 1, note: 'Installed less internal' }, { l: 'Rentable share of installed GW', v: div(cumRent, S.gw_cum), f: 'pct0', ind: 1 },
  { sep: 'Rental revenue, rentable GW only' },
  { l: 'Rentable GW deployed in year', v: incRent, f: 'gw', ind: 1 },""")
# close the extra concat: the rows array after this point ends with ']))' ; add one more ']' via a marker on the Coverage row
rep("""{ l: 'Coverage', v: div(aiRev, rentRev), f: 'pct0', ind: 1 }])) +""",
    """{ l: 'Coverage', v: div(aiRev, rentRev), f: 'pct0', ind: 1 }]))) +""")
# css
css = """
/* op-internal-use v1 */
.op-iu { align-items: center; }
.op-iu-h { font-weight: 600; margin-right: 4px; }
.op-iu-p { max-width: 80px; margin-right: 8px; }
.op-iu-p input { width: 56px; }
"""
if '</style>' in s and P.endswith('.html'):
    i = s.find('</style>', s.find('/* Layout: earnings ledger')); s = s[:i] + css + s[i:]
open(P, 'w', encoding='utf-8').write(s); print('applied')
