import json, sys
S=sys.argv[1]; d=json.load(open(S+'/load_earn/parsed.json'))
def q(v):
    if v is None: return 'null'
    if isinstance(v,(int,float)): return repr(v)
    if isinstance(v,(list,dict)): return "'"+json.dumps(v,ensure_ascii=False).replace("'","''")+"'::jsonb"
    return "'"+str(v).replace("'","''")+"'"
P=['ticker','company_name','sector','fiscal_quarter','calendar_quarter','report_date','verdict','verdict_marker','headline','summary','stock_reaction','title','local_key']
rows=[ '('+','.join(q(p[k]) for k in P)+')' for p in d['prints']]
out=[]
for i in range(0,len(rows),50):
    out.append(f"insert into public.earnings_prints ({','.join(P)}) values\n"+',\n'.join(rows[i:i+50])+
      "\non conflict (local_key) do update set "+','.join(f"{k}=excluded.{k}" for k in P if k!='local_key')+", updated_at=now();")
M=['section','metric','actual','street','bogey','vs_street_pct','vs_bogey_pct','marker']
mrows=["("+q(m['local_key'])+','+','.join(q(m[k]) for k in M)+')' for m in d['metrics']]
for i in range(0,len(mrows),400):
    out.append(f"insert into public.earnings_metrics (print_id,{','.join(M)}) select p.id,{','.join(('v.'+k+'::numeric') if k.startswith('vs_') else 'v.'+k for k in M)} from (values\n"+',\n'.join(mrows[i:i+400])+
      f"\n) v(local_key,{','.join(M)}) join public.earnings_prints p on p.local_key=v.local_key;")
for i,s in enumerate(out): open(f"{S}/load_earn/b{i:02d}.sql",'w').write(s)
print([len(s) for s in out])
