import json,re,math,collections,datetime as dt
D=dt.date.fromisoformat
rows=json.load(open('rows.json'))
# row: id,rid,fk,date,impact,stype,conf,psrc,ticker,company
BROKERS=[(r'^morgan stanley|^morgan$|^ms research|^morgan stanley mufg','Morgan Stanley'),(r'^goldman','Goldman Sachs'),
 (r'^bofa|^bank of america|^merrill|^boa\b','BofA Securities'),(r'^j\.? ?p\.? ?morgan|^jpm','J.P. Morgan'),(r'^citi','Citi'),(r'^ubs','UBS'),
 (r'^mizuho','Mizuho'),(r'^wells fargo','Wells Fargo'),(r'^barclays','Barclays'),(r'^nomura','Nomura'),(r'^deutsche','Deutsche Bank'),
 (r'^jefferies','Jefferies'),(r'^evercore','Evercore ISI'),(r'^(td )?cowen','TD Cowen'),(r'^needham','Needham'),(r'^stifel','Stifel'),
 (r'^wolfe','Wolfe Research'),(r'^clsa','CLSA'),(r'^william blair','William Blair'),(r'^oppenheimer','Oppenheimer'),(r'^keybanc','KeyBanc'),
 (r'^rbc','RBC Capital Markets'),(r'^macquarie','Macquarie'),(r'^wedbush','Wedbush'),(r'^bernstein','Bernstein'),(r'^piper','Piper Sandler'),
 (r'^raymond james','Raymond James'),(r'^truist','Truist'),(r'^baird','Baird'),(r'^rosenblatt','Rosenblatt'),(r'^loop capital','Loop Capital'),
 (r'^hsbc','HSBC'),(r'^daiwa','Daiwa'),(r'^mufg','MUFG'),(r'^bnp','BNP Paribas'),(r'^kgi','KGI'),(r'^jp morgan','J.P. Morgan'),(r'^susquehanna|^sig\b','Susquehanna'),
 (r'^benchmark','Benchmark'),(r'^northland','Northland'),(r'^cantor','Cantor Fitzgerald'),(r'^btig','BTIG'),(r'^guggenheim','Guggenheim'),
 (r'^redburn','Redburn'),(r'^arete','Arete'),(r'^new street','New Street Research'),(r'^melius','Melius'),(r'^bnp paribas','BNP Paribas')]
INDEP=[(r'^cleveland','Cleveland Research'),(r'^edgewater','Edgewater Research'),(r'^bluefin','BlueFin Research')]
EXPERT=[(r'^third bridge','Third Bridge'),(r'^tegus','Tegus'),(r'^bwg','BWG Global'),(r'^alphasights','AlphaSights'),(r'^glg|^gerson','GLG'),(r'^fundaai|^funda\b','FundaAI')]
INDUS=[(r'^trendforce','TrendForce'),(r'^counterpoint','Counterpoint Research'),(r'^lightcounting','LightCounting'),(r'^idc\b','IDC'),
 (r"^dell.oro","Dell'Oro"),(r'^techno system','Techno System Research'),(r'^cru\b','CRU'),(r'^omdia','Omdia'),(r'^gartner','Gartner'),
 (r'^semi\b','SEMI'),(r'^650 group','650 Group'),(r'^yole','Yole'),(r'^canalys','Canalys'),(r'^dramexchange','TrendForce'),(r'^inspectrum','Inspectrum')]
OTHERNAMED=[(r'^semianalysis|^semi analysis|^dylan patel','SemiAnalysis'),(r'^nuttycld','NuttyCLD'),(r'^latent space','Latent Space'),
 (r'^digitimes','DigiTimes'),(r'^reuters','Reuters'),(r'^bloomberg','Bloomberg'),(r'^the information','The Information'),(r'^tmt breakout','TMT Breakout'),
 (r'^financial times|^ft\b','Financial Times'),(r'^wsj|^wall street journal','WSJ'),(r'^nikkei','Nikkei'),(r'^stratechery','Stratechery'),(r'^chipstrat','Chipstrat')]
TYPE_PRIOR={'filing':5.0,'press_release':4.6,'management':4.0,'independent_research':3.6,'expert_call':3.2,'sell_side':3.2,
 'industry_data':3.5,'news':3.1,'substack':2.8,'social':2.2,'other':3.0}
ST_TYPE={'sell_side':'sell_side','company':'management','independent_research':'independent_research','news':'news','twitter':'social',
 'reddit':'social','substack':'substack','email':'other','evernote':'other','fintool':'other',None:'other'}
SPLIT=re.compile(r' – | — | - |\(|,| / |;')
MGMT=re.compile(r'\b(mgmt|management)\b',re.I)
def match(tbl,s):
    l=s.lower()
    for p,n in tbl:
        if re.search(p,l): return n
    return None
def clean_co(n):
    n=re.sub(r'(,? (Inc\.?|Corporation|Corp\.?|Ltd\.?|Limited|plc|N\.V\.|S\.A\.|SE|AG|Co\., Ltd\.|Co\.|Holdings|Holding|Group|Incorporated|Oyj))+\s*$','',n.strip())
    return n.strip() or n
CUT=re.compile(r"\b(F?[1-4]Q|Q[1-4]|FQ[1-4]|FY\d*|earnings|investor|management|mgmt|press|IR|CEO|CFO|CTO|COO|president|founder|chair\w*|blog|keynote|conference|meeting|annual|transcript|presentation|call|shareholder|analyst|official|website|announcement|statement|guidance|results|report|newsroom|SEC|10-K|10-Q|8-K|20-F|filing|disclosure|prepared|letter|event|(19|20)\d\d|january|february|march|april|may|june|july|august|september|october|november|december)\b",re.I)
def src_key(raw,stype,company):
    """returns (key,row_type)"""
    if not raw: return ('(no source)','other')
    s=raw.strip()
    if s.startswith('/Users') or s.startswith('Obsidian') or s.startswith('Pasted text'):
        return ('SRS internal file / paste','other')
    if s.lower().startswith('srs ba call notes'):
        if re.search(r'— Company\b|— company\b',s) or stype=='company':
            return (f'{clean_co(company)} (management)','management')
        return ('SRS BA Call Notes','other')
    m=re.match(r'@(\w+)',s)
    if m: return ('@'+m.group(1),'social')
    if 'reddit.com' in s: return ('Reddit','social')
    m=re.match(r'https?://(www\.)?([^/]+)',s)
    if m:
        dom=m.group(2).lower()
        for k,v in (('semianalysis','SemiAnalysis'),('reuters','Reuters'),('bloomberg','Bloomberg'),('trendforce','TrendForce'),('digitimes','DigiTimes')):
            if k in dom: s=v;break
        else: return (dom,ST_TYPE.get(stype,'other'))
    if s.lower().startswith('bernstein') and re.search(r'check',s,re.I): return ('Bernstein (channel checks)','independent_research')
    if s.lower().startswith('broker'): return ('Broker (unattributed)','sell_side')
    head=SPLIT.split(s)[0].strip()
    head=MGMT.sub('',head).strip(' .:/')
    for tbl,t in ((INDEP,'independent_research'),(EXPERT,'expert_call'),(INDUS,'industry_data')):
        n=match(tbl,s)
        if n: return (n,t)
    n=match(BROKERS,s)
    if n: return (n,'sell_side')
    n=match(OTHERNAMED,s)
    if n:
        t=ST_TYPE.get(stype,'other')
        if t=='management': t='other'
        return (n,t)
    if stype=='company':
        kind='management'
        if re.search(r'\b(10-K|10-Q|8-K|20-F|6-K|S-1|F-1|proxy|annual report|filing|SEC|exchange disclosure|board disclosure)\b',s,re.I): kind='filing'
        elif re.search(r'press release|newsroom|\bPR\b|announcement',s,re.I): kind='press_release'
        cand=CUT.split(head)[0].strip(' .:/-—–\'"')
        co=clean_co(company)
        if len(cand)<2: name=co
        else:
            w=cand.split()[0].lower().strip("'’s")
            if len(w)>=3 and (w in co.lower() or w==str(company).lower()): name=co
            else: name=clean_co(cand)
        lab={'management':'management','filing':'filing','press_release':'press release'}[kind]
        return (f'{name} ({lab})',kind)
    if not head: head=s[:40]
    return (head,ST_TYPE.get(stype,'other'))

rawmap={}; R=[]
for r in rows:
    i,rid,fk,d,imp,st,cf,ps,tk,co=r
    k,t=src_key(ps,st,co or tk or str(rid))
    rawmap.setdefault(ps or '',k)
    R.append(dict(id=i,rid=rid,fk=fk,d=D(d),dir={'positive':1,'negative':-1}.get(imp,0),imp=imp,conf=cf,key=k,t=t,tk=tk,co=co))
# main type per key = mode of row types
kt=collections.defaultdict(collections.Counter)
for x in R: kt[x['key']][x['t']]+=1
main={k:c.most_common(1)[0][0] for k,c in kt.items()}
prior={k:TYPE_PRIOR[main[k]] for k in main}
# confirm / refute
grp=collections.defaultdict(list)
for x in R: grp[(x['rid'],x['fk'])].append(x)
hits=collections.Counter(); miss=collections.Counter(); seen=set()
for g in grp.values():
    g.sort(key=lambda x:x['d'])
    for a in g:
        if a['dir']==0: continue
        pa=prior[a['key']]; end=a['d']+dt.timedelta(days=120); same=opp=0
        for b in g:
            if b['d']<=a['d'] or b['d']>end: continue
            if b['key']==a['key'] or prior[b['key']]<pa or b['dir']==0: continue
            if b['dir']==a['dir']: same+=1
            else: opp+=1
        ev=(a['key'],a['rid'],a['fk'],a['d'].strftime('%Y-%m'))
        if ev in seen or not (same or opp): continue
        seen.add(ev)
        if same and not opp: hits[a['key']]+=1
        elif opp>same: miss[a['key']]+=1
def logit(p): return math.log(p/(1-p))
def sig(z): return 1/(1+math.exp(-z))
TH=sum(hits.values()); TM=sum(miss.values()); BASE=TH/max(TH+TM,1)
cred={}
for k in main:
    h,m=hits[k],miss[k]; p=prior[k]
    if h+m==0: cred[k]=p
    else:
        q=min(max((p-1)/4,0.001),0.999)
        cred[k]=1+4*sig(logit(q)+0.9*(h-BASE*(h+m))/math.sqrt(h+m))
nk=collections.Counter(x['key'] for x in R)
sources=[dict(source=k,main_type=main[k],n=n,prior=prior[k],hits=hits[k],misses=miss[k],cred=round(cred[k],3)) for k,n in nk.most_common() if n>=3]
json.dump(sources,open('sources.json','w'),indent=0)
json.dump(rawmap,open('source_key_map.json','w'),ensure_ascii=False)
# signals
CW={'high':1.0,'medium':0.7,'low':0.4,None:0.7}
for x in R: x['w']=cred[x['key']]/5*CW[x['conf']]; x['s']=x['dir']*x['w']
AS_OF=D('2026-11-02'); START=D('2024-10-18'); END=D('2026-10-30'); HL=365.25*0.75
def strength(xs,asof):
    byf=collections.defaultdict(lambda:[0,0.0,0.0])
    for x in xs:
        if x['d']>asof: continue
        dec=0.5**(max((asof-x['d']).days,0)/HL); f=byf[x['fk']]; f[0]+=1
        if x['dir']==1: f[1]+=x['w']*dec
        elif x['dir']==-1: f[2]+=x['w']*dec
        else: f[1]+=0.5*x['w']*dec; f[2]+=0.5*x['w']*dec
    out=[]
    for fk,(n,p,ng) in sorted(byf.items(),key=lambda z:-z[1][0]):
        out.append(dict(field_key=fk,n=n,bull=round(100*p/(p+ng+2),1),bear=round(100*ng/(p+ng+2),1)))
    N=sum(o['n'] for o in out)
    if not N: return out,None,None
    b=sum(o['n']*o['bull'] for o in out)/N; e=sum(o['n']*o['bear'] for o in out)/N
    return out,b,e
MU=sum(x['s'] for x in R)/len(R)
byc=collections.defaultdict(list)
for x in R: byc[x['rid']].append(x)
def fri(d): return d+dt.timedelta(days=(4-d.weekday())%7)
weeks=[]; t=START
while t<=END: weeks.append(t); t+=dt.timedelta(days=7)
raw={}
for rid,xs in byc.items():
    if len(xs)<5: continue
    wk=collections.defaultdict(list)
    for x in xs: wk[max(fri(x['d']),START)].append(x['s']-MU)
    cum=0.0; ser=[]
    for t in weeks:
        v=wk.get(t,[])
        if v: cum+=sum(v)/math.sqrt(len(v))
        ser.append(cum)
    raw[rid]=ser
i90=len(weeks)-1-13
d90=[r[-1]-r[i90] for r in raw.values()]
m=sum(d90)/len(d90); sd=math.sqrt(sum((v-m)**2 for v in d90)/len(d90)) or 1
K=0.15/sd
companies=[]
for rid,ser in raw.items():
    xs=sorted(byc[rid],key=lambda x:x['d'])
    idx=[100*math.exp(K*v) for v in ser]
    out,b,e=strength(xs,AS_OF); _,b0,e0=strength(xs,AS_OF-dt.timedelta(days=90))
    companies.append(dict(research_id=rid,ticker=xs[0]['tk'],company=xs[0]['co'],n_rows=len(xs),
        n_90d=sum(1 for x in xs if x['d']>AS_OF-dt.timedelta(days=90)),
        index_now=round(idx[-1],1),chg_30d=round(100*(idx[-1]/idx[-1-4]-1),1),chg_90d=round(100*(idx[-1]/idx[i90]-1),1),
        bull=round(b,1),bear=round(e,1),spread=round(b-e,1),
        dspread_90d=None if b0 is None else round((b-e)-(b0-e0),1),
        by_field=out,series=[[weeks[j].isoformat(),round(idx[j],1)] for j in range(len(weeks))]))
companies.sort(key=lambda c:-c['n_rows'])
notes={'source_key':'primary_source cut at first " – ", " — ", " - ", "(", ",", " / ", ";"; mgmt/management stripped; brokers, research, expert, data and news firms mapped to one canonical name; @handles kept; company statements keyed "<Company> (management|filing|press release)"; SRS BA Call Notes with a company -> that company (management); local file paths -> "SRS internal file / paste". Raw->key map in source_key_map.json.',
 'credibility':'v2: one hit/miss per source x company x field x month, scored against the overall confirmation rate; prior by main evidence type (filing 5.0, press release 4.6, management 4.0, independent research 3.6, industry data 3.5, expert call 3.2, sell-side 3.2, news 3.1, substack 2.8, social 2.2, other 3.0); hit/miss from later (<=120d) same research_id+field_key evidence from a different source with prior >= own prior; cred=1+4*sigmoid(logit((prior-1)/4)+0.45*(h-m)/sqrt(h+m)), (prior-1)/4 clipped to [0.001,0.999].',
 'index':'v2: row signal centred on the universe mean (evidence is ~76% positive), summed per week and divided by sqrt(rows that week), cumulated; index=100*exp(k*cum) with k set so 90-day changes have a 15% cross-sectional spread; chg in %. Base: row signal = dir(+1/-1/0) x cred/5 x conf (high 1, medium 0.7, low 0.4, null 0.7); cumulative over all rows dated <= each Friday (pre-start rows included); series from later of 2024-10-18 and first Friday on/after first row, to 2026-10-30; index=100*exp(0.03*cum); chg_30d/90d = index(2026-10-30) minus index at 30/90 days earlier.',
 'bull_bear':'v2: bull = 100*P/(P+N+2), bear = 100*N/(P+N+2) on decayed weights. Base: per field_key, weights as index decayed with 9-month half-life to as_of; mixed counts 0.5 to both; strength=100*sigmoid(0.25*w); company = row-count-weighted mean; dspread_90d = spread now minus spread recomputed as of 2026-08-04 with rows up to then.',
 'n_90d':'rows dated after 2026-08-04 (90 days before as_of).'}
json.dump(dict(as_of='2026-11-02',method_notes=notes,rows_used=len(R),companies=companies,sources=sources),open('signals.json','w'),separators=(',',':'))
print('rows',len(R),'companies',len(companies),'keys',len(nk),'sources n>=3',len(sources))
print('sources with hits/misses',sum(1 for s in sources if s['hits'] or s['misses']),'all keys with h/m',sum(1 for k in main if hits[k] or miss[k]))
