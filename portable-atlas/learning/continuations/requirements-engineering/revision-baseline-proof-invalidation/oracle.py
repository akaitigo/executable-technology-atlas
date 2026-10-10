# Independent Boolean matrix closure and serialization. No producer import.
import json,sys,hashlib
IDS=sorted(['R-CAP','D-CAP','T-CAP','R-FIFO','D-FIFO','T-FIFO']);REQUIRED=sorted([['R-CAP','D-CAP'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO']])
def canonical(g,graph=False):
 nodes=sorted(g['nodes'],key=lambda n:n['id']);links=sorted(g['links'],key=lambda e:(e['source'],e['target']))
 if graph:nodes=[{'id':n['id']} if n['id'][0]=='T' else n for n in nodes]
 return {'nodes':nodes,'links':links}
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def closure(g):
 m=[[i==j for j in range(6)] for i in range(6)]
 for e in g['links']:m[IDS.index(e['source'])][IDS.index(e['target'])]=True
 for k in range(6):
  for i in range(6):
   for j in range(6):m[i][j]=m[i][j] or (m[i][k] and m[k][j])
 return m

def check(r,x,literal=None):
 if literal and 'status' in literal:assert r==literal;return
 assert r['status']=='OBSERVED';o,n=x['old'],x['new'];om,nm=closure(o),closure(n)
 reach=lambda m:{id:[v for j,v in enumerate(IDS) if m[IDS.index(id)][j]] for id in ['R-CAP','R-FIFO']}
 assert r['oldReach']==reach(om) and r['newReach']==reach(nm)
 ob,nb=canonical(o,True),canonical(n,True);od,nd=digest(ob),digest(nb)
 assert r['oldGraphBaseline']==ob and r['newGraphBaseline']==nb and r['oldGraphDigest']==od and r['newGraphDigest']==nd and r['recompute']==(ob!=nb) and r['oldCacheApplicable']==(ob==nb)
 on={v['id']:v for v in o['nodes']};nn={v['id']:v for v in n['nodes']};oe={(e['source'],e['target']):e for e in o['links']};ne={(e['source'],e['target']):e for e in n['links']};cn=sorted(v for v in IDS if on[v]!=nn[v]);ce=sorted(k for k in set(oe)|set(ne) if oe.get(k)!=ne.get(k));seeds=sorted(set(v for v in cn if v[0]!='T')|{e[0] for e in ce});impact=sorted({v for s in seeds for j,v in enumerate(IDS) if om[IDS.index(s)][j] or nm[IDS.index(s)][j]});missing=[e for e in REQUIRED if tuple(e) not in ne]
 assert r['changedNodes']==cn and r['changedEdges']==[list(e) for e in ce] and r['impactSeeds']==seeds and r['impact']==impact and r['missing']==missing and r['traceComplete']==(missing==[])
 expected=[]
 for test in ['T-CAP','T-FIFO']:
  ancestors=[v for i,v in enumerate(IDS) if nm[i][IDS.index(test)]];b=canonical({'nodes':[nn[v] for v in ancestors],'links':[e for e in n['links'] if e['source'] in ancestors and e['target'] in ancestors]});current=digest(b);p=next((p for p in x['proofs'] if p['test']==test),None);stored=digest(canonical(p['baseline'])) if p else None
  branches={v.split('-')[1] for v in ancestors if v[0]!='T'}|{test.split('-')[1]};absent=[e for e in REQUIRED if e[0].split('-')[1] in branches and tuple(e) not in ne];status='UNKNOWN_TRACE' if absent else 'MISSING' if not p else 'STALE' if current!=stored else 'CURRENT_'+p['result'];reasons=['missing required link'] if absent else ['no stored evidence'] if not p else ['baseline mismatch'] if current!=stored else ['matching metadata; no new test execution']
  expected.append(dict(test=test,status=status,storedResult=p['result'] if p else None,storedDigest=stored,currentDigest=current,currentBaseline=b,ancestors=ancestors,missing=absent,reasons=reasons))
 assert r['proofs']==expected and r['approval']=='UNCONFIRMED' and r['testsExecuted'] is False
 for id,walk in r['walks'].items():assert walk[0]==id and sorted(walk)==r['newReach'][id] and len(walk)==len(set(walk))
 if literal:
  for k in ['recompute','newReach','missing','impact']:assert r[k]==literal[k],k
  assert {p['test']:p['status'] for p in r['proofs']}==literal['proof']
if __name__=='__main__':
 a=json.loads(sys.stdin.read());check(a['result'],a['input']);print(json.dumps(dict(status='passed',independent=True)))
