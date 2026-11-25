"""Daily moves: use FactSet for pricing whenever the comp sheet is not available (Bobby, 2026-11-25).
The Bloomberg Live sheet in the Master comps workbook now counts as unavailable when it is missing, unreadable,
or stale (not saved today ET, or saved before 16:00 ET once it is past 16:30 ET); the page then loads FactSet
closes and says why in the status line. Marker "moves-fs v1"."""
import sys
P = sys.argv[1]; s = open(P, encoding='utf-8').read()
if 'moves-fs v1' in s: print('already'); sys.exit(0)
def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old)); s = s.replace(old, new)

rep("let MCP = null;\nconst inputFor = b =>",
    "let MCP = null, FS_WHY = ''; /* moves-fs v1 */\n"
    "const etYmd = d => d.toLocaleDateString('en-CA', { timeZone: 'America/New_York' });\n"
    "const etHr = d => { const p = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hourCycle: 'h23', hour: 'numeric', minute: 'numeric' }).formatToParts(d); const g = t => +((p.find(x => x.type === t) || {}).value || 0); return g('hour') + g('minute') / 60; };\n"
    "const sheetStale = d => !d || isNaN(d) || etYmd(d) !== etYmd(new Date()) || (etHr(new Date()) >= 16.5 && etHr(d) < 16);\n"
    "const inputFor = b =>")
rep("startBbg(mcp, () => startFactSet(mcp));",
    "startBbg(mcp, () => { if (!FS_WHY) FS_WHY = 'not available'; startFactSet(mcp); });")
rep("if (!stocks.length) { if (!okOnce) fallback(); return; }\nokOnce = true;",
    "if (!stocks.length) { if (!okOnce) fallback(); return; }\n"
    "if (!okOnce) { const sv0 = f.lastModifiedDateTime ? new Date(f.lastModifiedDateTime) : null; if (sheetStale(sv0)) { FS_WHY = sv0 ? 'last saved ' + sv0.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : 'save time unknown'; fallback(); return; } }\n"
    "okOnce = true;")
rep("`FactSet closes through ${latest}${stamp ? ' · fetched '",
    "`FactSet closes through ${latest}${FS_WHY ? ' (comp sheet ' + FS_WHY + ')' : ''}${stamp ? ' · fetched '")
open(P, 'w', encoding='utf-8').write(s); print('applied')
