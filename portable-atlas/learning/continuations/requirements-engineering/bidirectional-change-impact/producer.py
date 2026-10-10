"""Own 6-node DFS; direction tables are deliberately independent."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
class Refused(Exception):pass
def graph_for(variant):
 g=copy.deepcopy({k:FIXTURE[k] for k in ['nodes','forward','reverse']})
 if variant=='missing-back':g['reverse'].remove(['D-CAP','R-CAP'])
 elif variant=='missing-field':del g['reverse']
 elif variant=='unknown-endpoint':g['forward'][0][1]='D-UNKNOWN'
 elif variant=='invalid-edge':g['forward'][0]=['R-CAP','R-FIFO']
 elif variant=='duplicate-edge':g['forward'].append(g['forward'][0].copy())
 elif variant=='wrong-field-type':g['forward']={}
 elif variant=='edge-shape':g['forward'][0]=['R-CAP']
 elif variant=='cross-branch':g['forward'][0]=['R-CAP','D-FIFO']
 elif variant=='wrong-node-type':g['nodes'][0]['type']='design'
 elif variant=='empty-forward':g['forward']=[]
 return g
def validate(g,direction,start):
 def require(ok,reason):
  if not ok:raise Refused(reason)
 require(isinstance(g,dict),'GRAPH_TYPE')
 require(all(k in g for k in ['nodes','forward','reverse']),'MISSING_FIELD')
 require(all(isinstance(g[k],list) for k in ['nodes','forward','reverse']),'FIELD_TYPE')
 ids={};expected={n['id']:n for n in FIXTURE['nodes']}
 for n in g['nodes']:
  require(isinstance(n,dict) and set(n)=={'id','type','text'} and all(isinstance(v,str) for v in n.values()),'NODE_TYPE')
  require(n['id'] not in ids,'DUPLICATE_ID');require(n['id'] in expected and n==expected[n['id']],'NODE_IDENTITY');ids[n['id']]=n['type']
 require(set(ids)==set(expected),'NODE_SET')
 for table in ['forward','reverse']:
  seen=set();types={('requirement','design'),('design','test')} if table=='forward' else {('test','design'),('design','requirement')}
  for edge in g[table]:
   require(isinstance(edge,list) and len(edge)==2 and all(isinstance(x,str) for x in edge),'EDGE_SHAPE');a,b=edge
   require(a in ids and b in ids,'UNKNOWN_ENDPOINT');require((a,b) not in seen,'DUPLICATE_EDGE');seen.add((a,b))
   require((ids[a],ids[b]) in types,'EDGE_TYPE');require(a.split('-')[1]==b.split('-')[1],'CROSS_BRANCH')
 require(direction in ['forward','reverse'],'DIRECTION');require(isinstance(start,str) and start in ids,'UNKNOWN_ID');require(ids[start]==('requirement' if direction=='forward' else 'test'),'START_TYPE')
def traverse(g,direction,start):
 todo=[start];seen=set();steps=[]
 while todo:
  x=todo.pop()
  if x in seen:continue
  seen.add(x);nxt=[b for a,b in g[direction] if a==x];steps.append(dict(visit=x,neighbors=nxt));todo.extend(nxt)
 return sorted(seen),steps
def run(case_id,start_override=None):
 cases={x['id']:x for x in FIXTURE['cases']}
 if case_id not in cases:return dict(case=case_id,status='INPUT_REFUSED',reason='UNKNOWN_CASE',reachable=[],missing_reverse=[],missing_forward=[],trace=[],input=None)
 c=cases[case_id];g=graph_for(c['variant']);start=c['start'] if start_override is None else start_override
 out=dict(case=case_id,input=dict(graph=g,direction=c['direction'],start=start),status='',reason='',reachable=[],missing_reverse=[],missing_forward=[],trace=[])
 try:
  validate(g,c['direction'],start)
  if c['variant']=='execution-failure':raise RuntimeError('injected traversal failure')
  rev={tuple(x) for x in g['reverse']};fwd={tuple(x) for x in g['forward']}
  out['missing_reverse']=sorted([list((b,a)) for a,b in fwd if (b,a) not in rev]);out['missing_forward']=sorted([list((b,a)) for a,b in rev if (b,a) not in fwd])
  out['reachable'],out['trace']=traverse(g,c['direction'],start);out['status']='TRACE_INCOMPLETE' if out['missing_reverse'] or out['missing_forward'] else 'NORMAL'
 except Refused as e:out.update(status='INPUT_REFUSED',reason=str(e))
 except Exception as e:out.update(status='EXECUTION_FAILURE',reason=str(e))
 return out
