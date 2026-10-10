# SPDX-License-Identifier: Apache-2.0
# No model import: literal pre-implementation table + separate set construction.
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def check(r):
 assert r['status']=='MODEL_COMPLETE' and r['mode']=='INDEPENDENT_FINITE_MODEL'
 c=r['inputs'];h=next(e for e in H['cases'] if all(e[k]==c[k] for k in c))
 assert [e['input'] for e in r['generated']]==h['generated']
 assert [e['state'] for e in r['generated']]==H['states'][str(c['seed'])][:c['count']]
 assert r['draws']==[dict(state=s,accepted=True) for s in H['states'][str(c['seed'])][:c['count']]]
 for k in ['first_failure_index','first_failure','final_counterexample','global_minimum','global_failures']:assert r[k]==h[k],k
 def expected(t):
  assert type(t) is list and len(t)==3 and all(type(v) is int for v in t) and -3<=t[0]<=t[1]<=3 and -4<=t[2]<=4
  return t[2] in {i for i in range(-3,4) if i>=t[0] and i<t[1]}
 def actual(t):
  lo,hi,x=t
  if c['variant']=='M1':return x in set(range(lo+1,hi))
  if c['variant']=='M2':return x in set(range(lo,hi+1))
  return expected(t)
 for e in r['generated']+r['enumeration']:
  t=e['input'];assert e['set_members']==[i for i in range(-3,4) if i>=t[0] and i<t[1]]
  assert e['expected']==expected(t) and e['actual']==actual(t) and e['failed']==(expected(t)!=actual(t))
 assert r['generated_failures']==sum(e['failed'] for e in r['generated']) and r['no_generated_failure_is_proof'] is False
 want={str(lo)+','+str(hi)+','+str(x) for lo in range(-3,4) for hi in range(lo,4) for x in range(-4,5)}
 assert len(r['enumeration'])==252 and {','.join(map(str,e['input'])) for e in r['enumeration']}==want
 ranks=[]
 for e in r['enumeration']:
  t=e['input'];rr=[sum(map(abs,t)),*map(abs,t),*t];assert e['rank']==rr;ranks.append(rr)
 assert ranks==sorted(ranks)
 if h['first_failure'] is None:assert r['shrink_trace']==[] and r['local_minimal'] is False and r['local_equals_global'] is None
 else:
  key=c['variant']+':'+','.join(map(str,h['first_failure']));literal=H['shrink_traces'][key]
  assert [[e['candidate'],e['decision']] for e in r['shrink_trace']]==literal
  current=h['first_failure'][:];round_no=0
  for e in r['shrink_trace']:
   assert e['from_input']==current and e['round']==round_no
   t=e['candidate'];valid=-3<=t[0]<=t[1]<=3 and -4<=t[2]<=4
   assert e['valid']==valid
   assert e['rank']==[sum(map(abs,t)),*map(abs,t),*t]
   assert e['coordinate'] in ['lo','hi','x'] and e['rule'] in ['zero','step']
   if valid:assert e['expected']==expected(t) and e['actual']==actual(t) and e['failed']==(expected(t)!=actual(t))
   else:assert e['expected'] is None and e['actual'] is None and e['failed'] is None
   if e['decision']=='ACCEPT':assert valid and expected(t)!=actual(t) and e['rank']<[sum(map(abs,current)),*map(abs,current),*current];current=t;round_no+=1
  assert current==h['final_counterexample'] and r['local_minimal'] is True and r['local_equals_global']==(current==h['global_minimum'])
 return True
