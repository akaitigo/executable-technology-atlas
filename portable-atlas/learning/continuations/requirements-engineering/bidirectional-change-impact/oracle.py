"""Literal ID oracle and separate Boolean adjacency closure; no producer import."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text());TABLE=json.loads((ROOT/'oracle.json').read_text())
def input_graph(variant):
 g=copy.deepcopy({k:FIXTURE[k] for k in ['nodes','forward','reverse']})
 # Literal alternatives, no producer mutation helper.
 overrides={
 'missing-back':{'reverse':[['T-CAP','D-CAP'],['D-FIFO','R-FIFO'],['T-FIFO','D-FIFO']]},
 'unknown-endpoint':{'forward':[['R-CAP','D-UNKNOWN'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO']]},
 'invalid-edge':{'forward':[['R-CAP','R-FIFO'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO']]},
 'duplicate-edge':{'forward':[['R-CAP','D-CAP'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO'],['R-CAP','D-CAP']]},
 'wrong-field-type':{'forward':{}},
 'edge-shape':{'forward':[['R-CAP'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO']]},
 'cross-branch':{'forward':[['R-CAP','D-FIFO'],['D-CAP','T-CAP'],['R-FIFO','D-FIFO'],['D-FIFO','T-FIFO']]},
 'empty-forward':{'forward':[]}}
 g.update(overrides.get(variant,{}))
 if variant=='missing-field':g.pop('reverse')
 if variant=='wrong-node-type':g['nodes']=[{'id':'R-CAP','type':'design','text':'容量要求'},*g['nodes'][1:]]
 return g
def closure(graph,table,start):
 ids=[n['id'] for n in graph['nodes']];index={n:i for i,n in enumerate(ids)};size=len(ids);m=[[i==j for j in range(size)] for i in range(size)]
 for a,b in graph[table]:m[index[a]][index[b]]=True
 for k in range(size):
  for i in range(size):
   for j in range(size):m[i][j]=m[i][j] or (m[i][k] and m[k][j])
 return sorted(n for n in ids if m[index[start]][index[n]])
def validate(raw):
 assert raw['fixture']==FIXTURE;assert [x['case'] for x in raw['cases']]==list(TABLE['expected'])
 count=0
 for observed,case in zip(raw['cases'],FIXTURE['cases']):
  expect=TABLE['expected'][case['id']];g=input_graph(case['variant']);assert observed['input']==dict(graph=g,direction=case['direction'],start=case['start'])
  for key,value in expect.items():assert observed[key]==value,(case['id'],key)
  if expect['status'] in ['NORMAL','TRACE_INCOMPLETE']:
   assert closure(g,case['direction'],case['start'])==expect['reachable'];count+=1
   assert observed['trace'][0]['visit']==case['start'] and sorted(t['visit'] for t in observed['trace'])==expect['reachable']
   for t in observed['trace']:assert t['neighbors']==[b for a,b in g[case['direction']] if a==t['visit']]
   expected_reverse=[pair['reverse'] for pair in TABLE['reverse_pairs'] if pair['forward'] in g['forward'] and pair['reverse'] not in g['reverse']]
   expected_forward=[pair['forward'] for pair in TABLE['reverse_pairs'] if pair['reverse'] in g['reverse'] and pair['forward'] not in g['forward']]
   assert sorted(expected_reverse)==expect['missing_reverse'] and sorted(expected_forward)==expect['missing_forward']
  else:assert not observed['trace']
 return dict(cases=len(raw['cases']),matrix_closures=count,literal_ID_sets=True,independent_reverse_correspondence=True,stakeholder_approval=False)
