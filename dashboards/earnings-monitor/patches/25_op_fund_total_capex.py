"""AI one page section 9: total capex by company (FactSet consensus) with SRS AI capex for reference. Marker "op-fund-capex v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-fund-capex v1' in s: print('already'); sys.exit(0)
old = "ftab('Cash flow from operations, $bn', c => FU.cfo[c]) +\n"
assert s.count(old) == 1
new = old + """/* op-fund-capex v1 */ tbl('Total capex, $bn (FactSet consensus, calendarized)', cos.map(c => ({ l: nm[c], v: SC[c], ind: c !== 'ORCL', b: c === 'ORCL', note: c === 'MSFT' ? 'June FY; incl. finance leases' : c === 'ORCL' ? 'May FY' : '' })).concat([{ l: 'Big 4 + Oracle', v: add(...cos.map(c => SC[c])), b: 1 }, { l: 'Capex ÷ cash flow from operations, Big 4 + Oracle', v: div(add(...cos.map(c => SC[c])), add(...cos.map(c => FU.cfo[c]))), f: 'pct0', ind: 1 }, { sep: 'Of which AI capex, SRS case (AI Financings)' }], cos.map(c => ({ l: nm[c], v: srsCo[c], ind: 1, ref: 1 })))) +
"""
s = s.replace(old, new)
open(P, 'w', encoding='utf-8').write(s); print('applied')
