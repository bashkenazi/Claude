import json,sys,datetime,collections,os
# usage: plan_week.py <week_index>  (12 = newest: 2026-11-05..11-10)
wi=int(sys.argv[1]); cap=int(sys.argv[2]) if len(sys.argv)>2 else 12
start=datetime.date(2026,8,13)+datetime.timedelta(days=7*wi); end=min(start+datetime.timedelta(days=6),datetime.date(2026,11,10))
rel=[c for c in json.load(open(sys.argv[3] if len(sys.argv)>3 else 'calls_all.json'))['relevant'] if start.isoformat()<=c['released'][:10]<=end.isoformat()]
g=collections.defaultdict(list)
for c in rel: g[c['ticker']].append(c)
groups=sorted(g.values(),key=lambda x:(-len(x)))
bins=[]
for grp in groups:
    for b in bins:
        if len(b)+len(grp)<=cap: b.extend(grp); break
    else: bins.append(list(grp))
wd=f'chunks/w{wi:02d}'; os.makedirs(wd+'/batches',exist_ok=True)
out=[]
for i,b in enumerate(bins,1):
    b.sort(key=lambda c:(c['tier'],c['ticker'],c['released']))
    json.dump(b,open(f'{wd}/batches/worker-{i}.json','w'),indent=1)
    out.append({'worker':i,'n':len(b),'tickers':sorted({c['ticker'] for c in b})})
json.dump({'week':wi,'start':str(start),'end':str(end),'calls':len(rel),'workers':out},open(f'{wd}/plan.json','w'),indent=1)
print(start,end,len(rel),'calls',len(bins),'workers',[w['n'] for w in out])
