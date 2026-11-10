#!/usr/bin/env python3
"""Turn a Notion company deep-dive page (fetched as Notion-flavoured markdown) into the Stocks-page deep-dive doc
(page db collection stock_deep, doc <TICKER>): tabs of blocks (heading, paragraph, list, table, toggle).
Tabs are cut at the page's '## N.' headings and mapped by TAB_MAP. Text keeps only bold and http(s) links.
Usage: build_from_notion.py <page.md> <TICKER> <notion_url> <out.json>"""
import html, json, re, sys

TAB_MAP = [  # (tab key, label, which '## ' headings go in it, datapoint regex for the live feed under the tab)
    ("sites", "Sites & build", [r"^Key takeaways", r"^1\."], r"(\bMW\b|\bGW\b|campus|site|Abilene|Shackelford|Frontier|Jupiter|Lighthouse|Port Washington|Saline|Michigan|New Mexico|Wisconsin|Stargate|permit|power)"),
    ("financing", "Financing & guarantees", [r"^2\.", r"^3\."], r"(bond|notes?\b|debt|loan|equity|ATM|convertible|financ|guarant|backstop|letter of credit|lease commit|BYOH|prepay|rating|downgrad|S&P|Moody|CDS|spread|credit)"),
    ("rpo", "RPO & contracts", [r"^4\.", r"^5\."], r"(\bRPO\b|backlog|remaining performance|OpenAI|contract|booking|prepay|BYOH|customer)"),
]

def inline(s):
    s = s.replace("\\$", "$").replace("\\~", "~").replace("\\_", "_").replace("\\[", "[").replace("\\]", "]").replace("\\*", "*")
    keep = {}
    def stash(h):
        k = f"\x00{len(keep)}\x00"; keep[k] = h; return k
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: stash(f'<a class="ext" href="{html.escape(m.group(2), True)}" target="_blank" rel="noopener">{html.escape(m.group(1))}</a>'), s)
    s = re.sub(r"<b>(.*?)</b>", lambda m: stash("<b>" + html.escape(m.group(1)) + "</b>"), s)
    s = re.sub(r"\*\*(.+?)\*\*", lambda m: stash("<b>" + html.escape(m.group(1)) + "</b>"), s)
    s = html.escape(re.sub(r"<[^>\x00]+>", "", s))
    for k, v in keep.items(): s = s.replace(html.escape(k), v).replace(k, v)
    return s.strip()

def blocks(lines):
    out, i = [], 0
    while i < len(lines):
        ln = lines[i].rstrip(); st = ln.strip()
        if not st: i += 1; continue
        if st.startswith("<toggle"):
            depth, j, body = 1, i + 1, []
            while j < len(lines) and depth:
                t = lines[j].strip()
                if t.startswith("<toggle"): depth += 1
                if t == "</toggle>": depth -= 1
                if depth: body.append(lines[j])
                j += 1
            title = next((b.strip() for b in body if b.strip()), "")
            rest = body[body.index(next(b for b in body if b.strip())) + 1:] if title else body
            out.append({"k": "toggle", "title": inline(title), "b": blocks(rest)}); i = j; continue
        if st.startswith("<callout"):
            j, body = i + 1, []
            while j < len(lines) and lines[j].strip() != "</callout>": body.append(lines[j]); j += 1
            out.append({"k": "note", "h": inline(" ".join(b.strip() for b in body))}); i = j + 1; continue
        if st.startswith("#"):
            out.append({"k": "h", "h": inline(st.lstrip("#").strip())}); i += 1; continue
        if st.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split(" | ")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells): rows.append([inline(c) for c in cells])
                i += 1
            out.append({"k": "table", "cols": rows[0], "rows": rows[1:]}); continue
        if re.match(r"^\s*[-*] ", ln):
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*] ", lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                m = re.match(r"^(\s*)[-*] (.*)", lines[i])
                if m: items.append({"d": len(m.group(1)) // 2, "h": inline(m.group(2))})
                i += 1
            out.append({"k": "ul", "items": items}); continue
        if st.startswith("<") and st.endswith(">"): i += 1; continue
        out.append({"k": "p", "h": inline(st)}); i += 1
    return out

def main(src, tk, url, dst):
    t = open(src, encoding="utf-8").read()
    t = t[t.index("<content>") + 9: t.rindex("</content>")] if "<content>" in t else t
    m = re.search(r'"title":"([^"]+)"', open(src, encoding="utf-8").read())
    parts, cur = {}, None
    for ln in t.split("\n"):
        if ln.startswith("## "): cur = ln[3:].strip(); parts[cur] = [ln]; continue
        if cur: parts[cur].append(ln)
    intro = t.split("\n## ")[0].split("\n")
    tabs = []
    for key, label, pats, rx in TAB_MAP:
        ls = [l for h, b in parts.items() if any(re.search(p, h) for p in pats) for l in b]
        tabs.append({"key": key, "label": label, "dp_rx": rx, "blocks": blocks(ls)})
    tabs[0]["blocks"] = blocks(intro) + tabs[0]["blocks"]
    doc = {"ticker": tk, "title": m.group(1) if m else tk, "source": {"kind": "notion", "url": url},
           "as_of": (re.search(r"(\d{4}-\d{2}-\d{2})\)?\s*$", m.group(1)) or [None, None])[1] if m else None, "tabs": tabs}
    open(dst, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))
    print(dst, len(json.dumps(doc)), [(x["key"], len(x["blocks"])) for x in tabs])

if __name__ == "__main__":
    main(*sys.argv[1:5])
