#!/usr/bin/env python3
"""AI › Thesis by tenet: "Sort" control — Newest first, or Strongest first (within the How-far-back window).
Strength = |score| (2 strongly, 1, 0), then evidence quality (reported/company/regulator actuals above analyst
estimates, models, forecasts and opinion), then recency. Marker "tenet-strongest v1"."""
import sys
JS = 'tabs.js'; js = open(JS).read()
if 'tenet-strongest v1' in js: print('already applied'); sys.exit(0)
def rep(s, o, n):
    assert s.count(o) == 1, ('anchor', o[:70], s.count(o)); return s.replace(o, n)
js = rep(js, "Object.assign({ tenet: '', sent: [], days: '', n: '10' }, f)", "Object.assign({ tenet: '', sent: [], days: '', n: '10', sort: 'new' }, f)")
js = rep(js, "  function tnDateOk(d, asOf) {",
  "  /* tenet-strongest v1 */\n"
  "  const TN_SORT = [['new', 'Newest first'], ['strong', 'Strongest first']];\n"
  "  const tnQual = d => { const s = String((d.text || '') + ' ' + (d.src || '')); if (/\\b(est\\.?|estimates?|model|forecasts?|scenario|opinion|expects?|targets?|could|may|might|channel checks?|views?|thinks?)\\b/i.test(s)) return 0; if (/\\b(10-[QK]|filing|S-1|press release|earnings|call|reported|actual|signed|approved|issued|voted|adopted|filed|guide|mgmt|management|CFO|CEO|IR|regulator|TCEQ|ERCOT|PUCT|County|AG)\\b/.test(s)) return 2; return 1; };\n"
  "  const tnStrength = d => Math.abs(tnLvl(d)) * 10 + tnQual(d);\n"
  "  function tnDateOk(d, asOf) {")
js = rep(js, "`<span class=\"sub\">Newest first</span></div>`;", "`<label>Sort <select data-tnf=\"sort\">${opt(TN_SORT, TNF.sort)}</select></label>` +\n      `${TNF.sort === 'strong' ? '<span class=\"sub\">Strongest = strongly supports/weakens first, then reported facts over estimates, then newest</span>' : ''}</div>`;")
js = rep(js, "all = arr(t.dps).slice().sort((a, b) => String(b.date).localeCompare(String(a.date)) || (b.id || 0) - (a.id || 0));",
         "all = arr(t.dps).slice().sort((a, b) => (TNF.sort === 'strong' ? tnStrength(b) - tnStrength(a) : 0) || String(b.date).localeCompare(String(a.date)) || (b.id || 0) - (a.id || 0));")
open(JS, 'w').write(js); print('applied')
# Follow-up (2026-11-23, marker "tenet-weakest v1"): 'weak' sort option added directly in tabs.js — negatives first
# (score ascending), then evidence quality, then newest.
