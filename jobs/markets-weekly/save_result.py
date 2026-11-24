"""Save one FactSet MCP result as raw JSON for the weekly overlay.
Usage: python3 -I save_result.py <tool-result file path | -> <name>
  <path>: the file the harness saved an oversized result to ('-' reads the JSON from stdin instead).
  <name>: macro -> seriesId with non-alphanumerics as '_' (US.HCSTARTS -> US_HCSTARTS); prices -> px_<batch> (px_core, px_d_core, px_tr1).
Writes data/factset_new/<name>.json and prints a one-line summary (rows, first and last date)."""
import json, sys, pathlib
src, name = sys.argv[1], sys.argv[2]
v = json.load(sys.stdin) if src == '-' else json.load(open(src))
if isinstance(v, list): v = json.loads(v[0]['text'])
elif isinstance(v, str): v = json.loads(v)
out = pathlib.Path(__file__).parent / 'data' / 'factset_new'; out.mkdir(parents=True, exist_ok=True)
json.dump(v, open(out / f'{name}.json', 'w'))
rows = []
for it in v.get('data', []):
    rows += it['items'] if isinstance(it, dict) and isinstance(it.get('items'), list) else [it]
ds = sorted(str(r.get('periodDate') or r.get('date')) for r in rows if isinstance(r, dict) and (r.get('periodDate') or r.get('date')))
print(f"{name}: {len(rows)} rows, {ds[0] if ds else '-'} -> {ds[-1] if ds else '-'}")
