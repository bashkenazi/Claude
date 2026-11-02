"""Convert a Notion-flavored markdown page into safe HTML sections for the Earnings tab.

Everything is HTML-escaped first; only a small whitelist of structural tags (tables, toggles,
line breaks) and basic markdown (headings, lists, bold/italic/code, http links) is turned back
into markup, with all attributes dropped. The result is split into sections at top-level
headings so the page can show each part of the review as its own collapsible block.
"""
import html
import re

ALLOWED = r"table|thead|tbody|tr|td|th|colgroup|col|details|summary|br"
TAG = re.compile(r"&lt;(/?)(" + ALLOWED + r")(?:\s(?:(?!&gt;).)*?)?\s*(/?)&gt;", re.I)
CALLOUT_OPEN = re.compile(r"&lt;callout(?:\s(?:(?!&gt;).)*?)?&gt;", re.I)
CALLOUT_CLOSE = re.compile(r"&lt;/callout&gt;", re.I)
MENTION = re.compile(r"&lt;mention-(?:page|database|user|date)(?:(?!&gt;).)*?(?:url=&quot;(https?://(?:(?!&quot;).)*?)&quot;)?(?:(?!&gt;).)*?&gt;(.*?)&lt;/mention-[a-z]+&gt;", re.I)
SELF_CLOSING_JUNK = re.compile(r"&lt;(?:empty-block|page|database|mention-[a-z]+)(?:(?!&gt;).)*?/&gt;", re.I)
OTHER_TAG = re.compile(r"&lt;/?[a-z][a-z0-9-]*(?:\s(?:(?!&gt;).)*?)?/?&gt;", re.I)
ATTR_BRACES = re.compile(r"\s*\{[a-zA-Z]+=&quot;(?:(?!&quot;).)*?&quot;\}")
BOLD = re.compile(r"\*\*(.+?)\*\*")
ITAL = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
NUM = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")


UNESC = re.compile(r"\\([$~_*#\[\]()|>`.!+-])")


def _inline(s):
    s = ATTR_BRACES.sub("", s)
    s = UNESC.sub(r"\1", s)
    s = MENTION.sub(lambda m: (f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(2)}</a>'
                               if m.group(1) else m.group(2)), s)
    s = SELF_CLOSING_JUNK.sub("", s)
    s = CALLOUT_OPEN.sub('<div class="fr-callout">', s)
    s = CALLOUT_CLOSE.sub("</div>", s)
    s = TAG.sub(lambda m: f"<{m.group(1)}{m.group(2).lower()}{' /' if m.group(3) else ''}>", s)
    s = OTHER_TAG.sub("", s)
    s = LINK.sub(lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    s = CODE.sub(r"<code>\1</code>", s)
    s = BOLD.sub(r"<b>\1</b>", s)
    s = ITAL.sub(r"<i>\1</i>", s)
    return s


def _blocks(lines):
    """Turn escaped lines into HTML, handling nested lists by indentation."""
    out, stack = [], []  # stack of (indent, tag)

    def close_to(indent):
        while stack and stack[-1][0] >= indent:
            out.append(f"</li></{stack.pop()[1]}>")

    for raw in lines:
        line = raw.replace("\t", "    ")
        if not line.strip():
            continue
        m = BULLET.match(line) or NUM.match(line)
        if m and not line.lstrip().startswith(("&lt;", "<")):
            indent = len(m.group(1))
            tag = "ol" if NUM.match(line) and not BULLET.match(line) else "ul"
            if stack and stack[-1][0] == indent:
                out.append("</li><li>")
            elif stack and stack[-1][0] > indent:
                close_to(indent + 1)
                if stack and stack[-1][0] == indent:
                    out.append("</li><li>")
                else:
                    out.append(f"<{tag}><li>"); stack.append((indent, tag))
            else:
                out.append(f"<{tag}><li>"); stack.append((indent, tag))
            out.append(_inline(m.group(2)))
            continue
        close_to(0)
        h = HEAD.match(line.strip())
        if h:
            lvl = min(len(h.group(1)) + 3, 6)
            out.append(f"<h{lvl}>{_inline(h.group(2))}</h{lvl}>")
            continue
        s = _inline(line.strip())
        if re.match(r"^</?(table|thead|tbody|tr|td|th|colgroup|col|details|summary|div)", s) or s.startswith("</div"):
            out.append(s)
        else:
            out.append(f"<p>{s}</p>")
    close_to(0)
    return "\n".join(out)


def _split(esc, level):
    """Split escaped lines at headings of exactly `level`; returns [(title, lines)]."""
    out, cur_t, cur = [], "Overview", []
    for l in esc:
        h = HEAD.match(l.strip())
        if h and len(h.group(1)) == level:
            if any(x.strip() for x in cur):
                out.append((cur_t, cur))
            cur_t, cur = _inline(h.group(2)), []
            continue
        cur.append(l)
    if any(x.strip() for x in cur):
        out.append((cur_t, cur))
    return out


def convert(md_text):
    """Return (title, url, sections); a section is {"title","html"} or {"title","subs":[...]}."""
    lines = md_text.splitlines()
    title = lines[0].strip().lstrip("#").strip() if lines else ""
    url = lines[1].strip() if len(lines) > 1 and lines[1].strip().startswith("http") else ""
    body = lines[2:] if url else lines[1:]
    esc = [html.escape(l, quote=True) for l in body]
    levels = sorted({len(m.group(1)) for m in (HEAD.match(l.strip()) for l in esc) if m})
    if not levels:
        return title, url, [{"title": "Review", "html": _blocks(esc)}]
    top = levels[0]
    tops = _split(esc, top)
    nest = len(levels) > 1 and len([t for t, _ in tops if t != "Overview"]) <= 4
    sections = []
    for t, ls in tops:
        if nest:
            subs = _split(ls, levels[1])
            if len(subs) > 1 or (subs and subs[0][0] != "Overview"):
                sections.append({"title": t, "subs": [{"title": st, "html": _blocks(sl)} for st, sl in subs]})
                continue
        sections.append({"title": t, "html": _blocks(ls)})
    return title, url, sections


if __name__ == "__main__":
    import sys, json
    t, u, s = convert(open(sys.argv[1]).read())
    print(t, u, len(s))
    print(json.dumps([[x["title"], [y["title"] for y in x.get("subs", [])]] for x in s], ensure_ascii=False)[:600])
