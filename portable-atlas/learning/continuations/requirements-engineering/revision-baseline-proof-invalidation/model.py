import json,sys,hashlib,re
IDS=['R-CAP','D-CAP','T-CAP','R-FIFO','D-FIFO','T-FIFO'];REQS=['R-CAP','R-FIFO'];TESTS=['T-CAP','T-FIFO'];REQUIRED=[('R-CAP','D-CAP'),('D-CAP','T-CAP'),('R-FIFO','D-FIFO'),('D-FIFO','T-FIFO')]
class Refused(Exception):pass
def exact(x,keys,reason):
 if not isinstance(x,dict) or set(x)!=set(keys):raise Refused(reason)
def graph(g,subset=False):
 exact(g,['nodes','links'],'GRAPH')
 if not isinstance(g['nodes'],list) or not isinstance(g['links'],list) or len(g['links'])>8:raise Refused('GRAPH')
 seen=set()
 for n in g['nodes']:
  exact(n,['id','rev','hash'],'NODES')
  if n['id'] not in IDS or n['id'] in seen:raise Refused('NODES')
  seen.add(n['id'])
  if type(n['rev'])!=int or not 1<=n['rev']<=9:raise Refused('REVISION')
  if not isinstance(n['hash'],str) or not re.fullmatch('[a-f0-9]{64}',n['hash']):raise Refused('HASH')
 if not subset and seen!=set(IDS):raise Refused('NODES')
 edges=set()
 for e in g['links']:
  exact(e,['source','target','rev'],'LINK');a,b=e['source'],e['target']
  if not isinstance(a,str) or not isinstance(b,str) or a not in seen or b not in seen or (a[0],b[0]) not in [('R','D'),('D','T')] or (a,b) in edges:raise Refused('LINK')
  edges.add((a,b))
  if type(e['rev'])!=int or not 1<=e['rev']<=9:raise Refused('REVISION')
def validate(x):
 exact(x,['old','new','proofs'],'FIELDS');graph(x['old']);graph(x['new'])
 if not isinstance(x['proofs'],list) or len(x['proofs'])>2:raise Refused('PROOF')
 seen=set()
 for p in x['proofs']:
  exact(p,['test','result','baseline'],'PROOF')
  if p['test'] not in TESTS or p['test'] in seen or p['result'] not in ['PASS','FAIL']:raise Refused('PROOF')
  seen.add(p['test']);graph(p['baseline'],True)
def canon(g,graph_only=False):
 return dict(nodes=[dict(id=n['id']) if graph_only and n['id'].startswith('T') else n for n in sorted(g['nodes'],key=lambda n:n['id'])],links=sorted(g['links'],key=lambda e:(e['source'],e['target'])))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def walk(g,start,reverse=False):
 seen=[];stack=[start]
 while stack:
  n=stack.pop()
  if n in seen:continue
  seen.append(n)
  adjacent=sorted([e['source'] if reverse else e['target'] for e in g['links'] if (e['target'] if reverse else e['source'])==n],reverse=True);stack.extend(adjacent)
 return seen

def process(x):
 validate(x);old,new=x['old'],x['new'];ob=canon(old,True);nb=canon(new,True);od,nd=digest(ob),digest(nb)
 oldReach={r:sorted(walk(old,r)) for r in REQS};newReach={r:sorted(walk(new,r)) for r in REQS}
 oldN={n['id']:n for n in old['nodes']};newN={n['id']:n for n in new['nodes']};oldE={(e['source'],e['target']):e for e in old['links']};newE={(e['source'],e['target']):e for e in new['links']}
 changedNodes=sorted(n for n in IDS if oldN[n]!=newN[n]);changedEdges=sorted(e for e in set(oldE)|set(newE) if oldE.get(e)!=newE.get(e));seeds=sorted(set(n for n in changedNodes if not n.startswith('T'))|set(e[0] for e in changedEdges));impact=sorted(set(v for seed in seeds for g in [old,new] for v in walk(g,seed)))
 missing=[list(e) for e in sorted(REQUIRED) if e not in newE];proofs=[]
 for test in TESTS:
  ancestors=sorted(walk(new,test,True));baseline=canon(dict(nodes=[newN[n] for n in ancestors],links=[e for e in new['links'] if e['source'] in ancestors and e['target'] in ancestors]));current=digest(baseline);stored=next((p for p in x['proofs'] if p['test']==test),None);storedDigest=digest(canon(stored['baseline'])) if stored else None
  # Required relationships for every requirement/design currently upstream, plus this test's declared original branch.
  branches=set(n.split('-')[1] for n in ancestors if n[0] in ['R','D'])|{test.split('-')[1]};needed=[e for e in REQUIRED if e[0].split('-')[1] in branches];absent=[list(e) for e in sorted(needed) if e not in newE]
  status='UNKNOWN_TRACE' if absent else 'MISSING' if stored is None else 'STALE' if storedDigest!=current else 'CURRENT_'+stored['result']
  reasons=['missing required link'] if absent else ['no stored evidence'] if stored is None else ['baseline mismatch'] if storedDigest!=current else ['matching metadata; no new test execution']
  proofs.append(dict(test=test,status=status,storedResult=stored['result'] if stored else None,storedDigest=storedDigest,currentDigest=current,currentBaseline=baseline,ancestors=ancestors,missing=absent,reasons=reasons))
 return dict(status='OBSERVED',oldGraphDigest=od,newGraphDigest=nd,oldCacheApplicable=od==nd,recompute=od!=nd,oldGraphBaseline=ob,newGraphBaseline=nb,oldReach=oldReach,newReach=newReach,changedNodes=changedNodes,changedEdges=[list(e) for e in changedEdges],impactSeeds=seeds,impact=impact,missing=missing,traceComplete=not missing,proofs=proofs,approval='UNCONFIRMED',testsExecuted=False,walks={r:walk(new,r) for r in REQS})
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read())
  if '--fail' in sys.argv:raise RuntimeError('injected metadata model error')
  out=process(x);code=0
 except (json.JSONDecodeError,Refused) as e:out=dict(status='INPUT_REFUSED',reason=str(e) if isinstance(e,Refused) else 'JSON');code=2
 except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=type(e).__name__);code=1
 print(json.dumps(out));sys.exit(code)
