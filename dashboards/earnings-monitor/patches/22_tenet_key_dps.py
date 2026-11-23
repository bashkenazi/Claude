#!/usr/bin/env python3
"""AI › Thesis by tenet: datapoints flagged key (dp.key = true) sit at the top of their tenet in every sort and carry
a "Key" badge (dp.why_key as tooltip). Marker "tenet-key-dps v1"."""
import sys
JS, CSS = 'tabs.js', 'tabs.css'; js = open(JS).read(); css = open(CSS).read()
if 'tenet-key-dps v1' in js: print('already applied'); sys.exit(0)
def rep(o, n):
    global js; assert js.count(o) == 1, (o[:60], js.count(o)); js = js.replace(o, n)
rep("all = arr(t.dps).slice().sort((a, b) => (TNF.sort === 'strong'", "all = arr(t.dps).slice().sort((a, b) => ((b.key ? 1 : 0) - (a.key ? 1 : 0)) /* tenet-key-dps v1 */ || (TNF.sort === 'strong'")
rep("<div class=\"chips\"><span class=\"tk-chip\">${esc(d.t)}</span></div>${esc(d.text)}", "<div class=\"chips\">${d.key ? `<span class=\"tn-key\" title=\"${esc(d.why_key || 'Key datapoint')}\">Key</span>` : ''}<span class=\"tk-chip\">${esc(d.t)}</span></div>${esc(d.text)}")
css += "\n/* tenet-key-dps v1 */\n.tn-key { display: inline-block; font-size: 10.5px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; padding: 1px 6px; border-radius: 4px; background: var(--ink); color: var(--bg); margin-right: 4px; }\n"
open(JS, 'w').write(js); open(CSS, 'w').write(css); print('applied')
