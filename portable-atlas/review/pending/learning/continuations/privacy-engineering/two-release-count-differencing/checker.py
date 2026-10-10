"""Independent delete-enumeration with algebraically solved additions."""
import copy,json,sys
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text())
def oracle(x):
 witnesses=[];budget=x['background'];count=0
 for t in range(3):
  for da in range(min(x['before'][0],budget['max_delete'])+1):
   for db in range(min(x['before'][1],budget['max_delete'])+1):
    for dc in range(min(x['before'][2],budget['max_delete'])+1):
     d=[da,db,dc]
     if sum(d)>budget['max_delete']:continue
     a=[x['after'][i]-x['before'][i]-int(i==t)+d[i] for i in range(3)]
     if min(a)<0 or sum(a)>budget['max_add']:continue
     witnesses.append({'target':x['categories'][t],'add':a,'delete':d})
 return witnesses
def key(w):return (w['target'],tuple(w['add']),tuple(w['delete']))
def inspect(r,x):
 assert r['status']=='calculated';s=r['summary'];assert s['input']==x;expected=oracle(x);observed=s['witnesses'];assert len(observed)==len({key(w) for w in observed}) and {key(w) for w in observed}=={key(w) for w in expected}
 candidates=[c for c in x['categories'] if any(w['target']==c for w in expected)];delta=[b-a for a,b in zip(x['before'],x['after'])];naive=next((c for i,c in enumerate(x['categories']) if delta==[int(i==j) for j in range(3)]),None)
 assert s['candidates']==candidates and s['witness_count']==len(expected) and s['candidate_witness_counts']=={c:sum(w['target']==c for w in expected) for c in x['categories']} and s['delta']==delta
 assert s['category']==('known' if len(candidates)==1 else 'ambiguous' if candidates else 'inconsistent') and s['known_category']==(candidates[0] if len(candidates)==1 else None) and s['naive_category_ignoring_background']==naive and s['naive_uniqueness_justified']==(naive is not None and candidates==[naive])
 b=x['background'];av=sum(1 for a in range(b['max_add']+1) for c in range(b['max_add']+1-a) for d in range(b['max_add']+1-a-c));dv=sum(1 for a in range(x['before'][0]+1) for c in range(x['before'][1]+1) for d in range(x['before'][2]+1) if a+c+d<=b['max_delete']);assert s['enumerated_transition_count']==3*av*dv and s['maximum_transition_count']==300 and s['enumerated_transition_count']<=300
 assert s['delete_capacity_rule']=='background delete <= before; no target/new record deletion' and s['target_presence']=='given added once and still present; not inferred from counts' and s['units']=='synthetic record counts'
 ctx=r['context'];assert ctx['synthetic_only'] and ctx['target_addition_given'] and not any(v for n,v in ctx.items() if n not in ['synthetic_only','target_addition_given'])
def handcheck(r,name):
 h=HAND['cases'][name];s=r['summary'];assert s['category']==h['category'] and s['candidates']==h['candidates'] and s['witness_count']==h['witness_count']
 if name=='same-delta-background':assert {key(w) for w in s['witnesses']}=={key(w) for w in HAND['background_witnesses']}
def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  p=run(row['input_json']);r=p['result'];assert p['stderr']==''
  if row['expected']['status']=='calculated':assert p['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case']);valid.append(r)
  else:assert p['exit']==2 and r=={'status':'input_refusal','code':row['expected']['code'],'summary':None}
 mutants=[]
 for name in ['ignore-background','omit-witness','duplicate-witness','delete-target','known-with-zero','ambiguous-is-safe','delta-sign','background-unbounded','target-inferred','probability-claim','real-linkage','DP-claim']:
  r=copy.deepcopy(valid[5] if name=='known-with-zero' else valid[2] if name=='delete-target' else valid[1]);s=r['summary']
  if name=='ignore-background':s['candidates']=['A'];s['category']='known'
  elif name=='omit-witness':s['witnesses'].pop()
  elif name=='duplicate-witness':s['witnesses'].append(copy.deepcopy(s['witnesses'][0]))
  elif name=='delete-target':s['witnesses'].append({'target':'B','add':[1,0,0],'delete':[0,1,0]})
  elif name=='known-with-zero':s['category']='known';s['known_category']='A'
  elif name=='ambiguous-is-safe':s['category']='safe'
  elif name=='delta-sign':s['delta']=[-1,0,0]
  elif name=='background-unbounded':s['maximum_transition_count']=999
  elif name=='target-inferred':r['context']['target_presence_inferred']=True
  elif name=='probability-claim':r['context']['count_witnesses_have_probabilities']=True
  elif name=='real-linkage':r['context']['actual_person_linked']=True
  else:r['context']['DP_guarantee_implemented']=True
  try:inspect(r,s['input'])
  except (AssertionError,TypeError,ValueError,KeyError):mutants.append(name)
  else:raise AssertionError('surviving mutant '+name)
 if (ROOT/'observation-data.js').exists():
  raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.DIFF_OBSERVATION=').strip().removesuffix(';'));assert raw==json.loads((ROOT/'observations'/raw['run_id']/'raw.json').read_text()) and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in raw['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case'])
   else:assert r['code']==row['expected']['code'] and row['run']['exit']==2
 assert before==snapshot();print(json.dumps({'hand_cases':6,'refused':6,'mutants_rejected':mutants,'oracle':'delete enumeration and solved additions','unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())
