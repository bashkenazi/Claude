#!/usr/bin/env python3
"""Debate-agent pages (stock-debate skill / Tech Specialist Debate History) -> markdown the page can show + an index.

Usage: python3 prep_debates.py <raw_dir> <out_dir>
raw_dir  one .md per Notion page: line 1 title, line 2 url, then the page <content> exactly as notion-fetch returns it
out_dir  gets the same files with Notion toggles turned into headings (pass it to build.py --routines) and
         index.json {ticker: {ticker, title, url, date, kind, dry_run}} (pass it to build_stocks.py --debpages);
         the newest page per ticker wins.
"""
import json, re, sys
from pathlib import Path


def normalize(lines):
    out, i, tbl, skip = [], 0, 0, False
    while i < len(lines):
        l = lines[i]; s = l.strip()
        tbl += s.count('<table') - s.count('</table>')
        if skip:
            if s == '</toggle>': skip = False
            i += 1; continue
        if s == '<b>📦 Debate data</b>':  # the machine-readable JSON block
            skip = True; i += 1; continue
        m = re.match(r'<toggle heading="h([23])">\s*(.*)$', s)
        if m:
            t = m.group(2).strip()
            if not t and i + 1 < len(lines): i += 1; t = lines[i].strip()
            out.append(('##' if m.group(1) == '2' else '###') + ' ' + re.sub(r'^(\\?#)+\s*', '', re.sub(r'</?b>', '', t))); i += 1; continue
        if s in ('<toggle>', '</toggle>'): i += 1; continue
        mb = re.fullmatch(r'<b>([^<]{2,60})</b>', s)
        if mb and tbl <= 0: out.append('### ' + mb.group(1)); i += 1; continue
        mt = re.match(r'^(🔴|🟢|🟡)+\s*Debate — (\d{4}-\d{2}-\d{2})$', s)
        if mt: out.append('## Debate — ' + mt.group(2)); i += 1; continue
        out.append(l); i += 1
    return out


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True)
    idx = {}
    for f in sorted(src.glob('*.md')):
        L = f.read_text().splitlines()
        if len(L) < 3: continue
        title = re.sub(r'^(🔍\s*)+', '🔍 ', L[0].strip()); url = L[1].strip().split('?')[0]
        mt = re.search(r'\(([0-9A-Z]{3,6} (?:TT|JP|JT|KS|HK|CH))\)', title) or re.search(r'^\W*([A-Z][A-Z0-9.]{1,6})\s+—', title)
        tk = mt.group(1) if mt else ''
        date = (re.findall(r'\d{4}-\d{2}-\d{2}', title) or [''])[-1]
        (dst / f.name).write_text('\n'.join([title, url] + normalize(L[2:])) + '\n')
        rec = {'ticker': tk, 'title': title, 'url': url, 'date': date, 'kind': 'stock-debate' if 'Stock Debate' in title else 'debate-history', 'dry_run': 'dry run' in title.lower()}
        if tk and (tk not in idx or date >= idx[tk]['date']): idx[tk] = rec
    json.dump(idx, open(dst / 'index.json', 'w'), ensure_ascii=False, indent=1)
    print(len(idx), 'debate pages:', ', '.join(sorted(idx)))


if __name__ == '__main__':
    main()
