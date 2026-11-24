"""Section 8: Anthropic consensus revenue + ARR rows. Marker op-anth-cons v1."""
import sys
P=sys.argv[1]; s=open(P,encoding="utf-8").read()
if "op-anth-cons v1" in s: sys.exit(0)
old="{ l: 'OpenAI + Anthropic revenue (memo)', v: R.lab_rev, ref: 1 },"
new="{ l: 'OpenAI + Anthropic revenue (memo)', v: R.lab_rev, ref: 1 }, /* op-anth-cons v1 */ ...(d.anth_cons ? [{ sep: 'Anthropic: Street consensus (FactSet, ANT)' }, { l: 'Anthropic revenue, consensus', v: d.anth_cons.rev, ind: 1, note: `Mean of ${d.anth_cons.n_rev[Y.indexOf(2027)] || ''} estimates (2027E)` }, { l: 'Anthropic ARR, year-end, consensus', v: d.anth_cons.arr, ind: 1, note: '2 estimates' }, { l: 'Anthropic consensus revenue as % of SRS OpenAI + Anthropic revenue', v: div(d.anth_cons.rev, R.lab_rev), f: 'pct0', ind: 1 }, { l: 'Consensus ARR ÷ next-year consensus revenue', v: Y.map((_, i) => nv(d.anth_cons.arr[i]) == null || nv(d.anth_cons.rev[i + 1]) == null ? null : d.anth_cons.arr[i] / d.anth_cons.rev[i + 1]), f: 'x', ind: 1, note: 'Above 1x = exit run-rate higher than next year\\'s revenue' }, { sep: 'Revenue reaching infrastructure' }] : []),"
assert s.count(old)==1; open(P,"w",encoding="utf-8").write(s.replace(old,new)); print("applied")
