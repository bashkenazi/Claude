"""AI one page section 12: siting and permitting pushback tracker (project rows, aggregate vs SRS US base by year,
amber/red flags, policy and Street estimates). Data: page db ai/one_page.dc_pushback. Marker "op-push v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'op-push v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)
rep("['states','11 States']", "['states','11 States'],['push','12 Pushback']") if "['states','11 States']" in s else None
JS = r"""
/* op-push v1: is local and state pushback adding up? */
const PB = d.dc_pushback;
if (PB) {
  const cls = st => ({ cancelled: 'lost', denied: 'lost', relocated: 'lost', delayed: 'delayed', at_risk: 'risk' })[st] || null;
  const yrs = Object.keys(PB.us_base).map(Number).sort();
  const agg = {}; yrs.forEach(y => { agg[y] = { lost: 0, delayed: 0, risk: 0, n: 0 }; });
  PB.projects.forEach(p => { const k = cls(p.status); if (!k || !agg[p.year]) return; agg[p.year].n++; if (p.mw) agg[p.year][k] += p.mw / 1000; });
  const T = PB.thresholds, flag = sh => sh >= T.red ? ['🔴', 'Red'] : sh >= T.amber ? ['🟠', 'Amber'] : ['🟢', 'Green'];
  const f1 = v => v ? v.toFixed(1) : '–', pc = v => (v * 100).toFixed(1) + '%';
  const aggRows = yrs.map(y => { const a = agg[y], b = PB.us_base[y], hit = a.lost + a.delayed, sh = b ? hit / b : 0, [dot, word] = flag(sh);
    return `<tr><td><b>${y}</b></td><td class="n">${b}</td><td class="n">${PB.us_bear[y] ?? '–'}</td><td class="n">${f1(a.lost)}</td><td class="n">${f1(a.delayed)}</td><td class="n"><b>${f1(hit)}</b></td><td class="n">${b ? pc(sh) : '–'}</td><td class="n">${f1(a.risk)}</td><td class="n">${b ? pc((hit + a.risk) / b) : '–'}</td><td>${dot} ${word}</td></tr>`; }).join('');
  const ST_ORD = { cancelled: 0, denied: 1, relocated: 2, delayed: 3, paused: 4, at_risk: 5, cleared: 6 };
  const stLbl = { cancelled: '🔴🔴 Cancelled', denied: '🔴🔴 Denied', relocated: '🔴 Withdrawn / relocating', delayed: '🔴 Delayed', paused: '🟠 Paused (short)', at_risk: '🟠 At risk', cleared: '🟢 Cleared' };
  const projRows = PB.projects.slice().sort((a, b) => b.date.localeCompare(a.date) || ST_ORD[a.status] - ST_ORD[b.status]).map(p => `<tr><td class="n">${esc(p.date)}</td><td><b>${esc(p.project)}</b><br><span class="sub">${esc(p.owner || '')}</span></td><td>${esc(p.state)}</td><td class="n">${p.mw ? p.mw.toLocaleString('en-US') : 'n/d'}<br><span class="sub">${esc(p.basis || '')}</span></td><td>${stLbl[p.status] || esc(p.status)}</td><td class="n">${p.year}</td><td>${esc(p.event)}</td><td>${esc(p.view || '')}</td><td class="note">${esc(p.src)}</td></tr>`).join('');
  h += sec('push', '12 · Siting and permitting pushback: is it adding up?', 'Project tracker (news, court and utility filings, SemiAnalysis, Supabase datapoints); SRS US base case',
  `<p class="op-call">${esc(PB.view)}</p>
<h3>Aggregate vs our US base case, GW</h3><div class="tbl-wrap"><table class="op-t"><thead><tr><th>Year first power was due</th><th class="n">SRS US base</th><th class="n">SRS bear</th><th class="n">Lost</th><th class="n">Delayed</th><th class="n">Lost + delayed</th><th class="n">% of base</th><th class="n">At risk</th><th class="n">% incl. at risk</th><th>Flag</th></tr></thead><tbody>${aggRows}</tbody></table></div>
<p class="sub">Flag on lost + delayed as a share of the SRS US base: green under ${pc(T.amber)}, amber ${pc(T.amber)}–${pc(T.red)}, red above ${pc(T.red)}. The bear case already assumes heavy political cuts, so red means tracked events are running toward it. ${esc(PB.rules)}</p>
<h3>Projects</h3><div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Project</th><th>State</th><th class="n">MW</th><th>Status</th><th class="n">Year</th><th>What happened</th><th>Our view</th><th>Source</th></tr></thead><tbody>${projRows}</tbody></table></div>
<h3>Policy actions</h3><div class="tbl-wrap"><table class="op-t op-push"><thead><tr><th class="n">Date</th><th>Where</th><th>Action</th><th>Level</th><th>Source</th></tr></thead><tbody>${PB.policy.map(r => `<tr><td class="n">${esc(r[0])}</td><td><b>${esc(r[1])}</b></td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td class="note">${esc(r[4])}</td></tr>`).join('')}</tbody></table></div>
<h3>Street estimates of the aggregate hit</h3><ul class="b">${PB.street.map(r => `<li><b>${esc(r[0])}:</b> ${esc(r[1])} <span class="sub">(${esc(r[2])})</span></li>`).join('')}</ul>
<p class="sub">As of ${esc(PB.as_of)}. Rows are added as datapoints and news come in; tell Claude about a new project event and it goes in this table.</p>`);
}
"""
rep("h += `<p class=\"aim-src\">Sources: ${esc(d.sources)}</p>`;", JS + "h += `<p class=\"aim-src\">Sources: ${esc(d.sources)}</p>`;")
css = """
/* op-push v1 */
table.op-push td { white-space: normal; font-size: 12px; line-height: 1.4; vertical-align: top; min-width: 70px; max-width: 300px; }
table.op-push td:nth-child(2) { min-width: 160px; }
"""
i = s.find('/* op-pools v1 */\ntable'); assert i > 0; s = s[:i] + css + s[i:]
open(P, 'w', encoding='utf-8').write(s); print('applied')
