# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,platform,datetime
from pathlib import Path
from model import run,valid
from oracle import H,check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for h in H['cases']:
  c={k:h[k] for k in ['generator','seed','count','variant']};r=run(c);check(r);rows.append(r)
 base=dict(generator='uniform',seed=7,count=2,variant='M1');bad=[]
 for key,value in [('seed',True),('seed',1.0),('seed',0),('count',0),('count',2.0),('generator','unknown'),('variant','M3'),('extra',1)]:
  c={**base,key:value};r=run(c);assert r['status']=='REFUSED_INPUT' and r['generated']==[] and r['shrink_trace']==[] and r['enumeration']==[];bad.append(r)
 tuples=[]
 for t in [[2,1,0],[0,1,0.0],[0,4,0],[False,1,0],[0,1,5],None,[0,1]]:
  assert not valid(t);tuples.append(dict(input=t,accepted=False))
 assert valid([-3,3,-4]) and valid([0,0,0])
 # Full LCG cycle check is separate from short displayed runs.
 state=7;cycle=[]
 for _ in range(256):state=(5*state+1)%256;cycle.append(state)
 assert len(set(cycle))==256 and state==7 and len([s for s in cycle if s<252])==252
 killed=[];sample=next(r for r in rows if r['inputs']==dict(generator='boundary',seed=7,count=4,variant='M1'))
 for name in ['generated-x','lost-failure-accepted','invalid-accepted','first-erased','local-as-global','global-count','enumeration-missing','predicate-copied']:
  r=copy.deepcopy(sample)
  if name=='generated-x':r['generated'][0]['input'][2]=0
  elif name=='lost-failure-accepted':r['shrink_trace'][0]['decision']='ACCEPT'
  elif name=='invalid-accepted':
   r=copy.deepcopy(next(v for v in rows if v['inputs']==dict(generator='boundary',seed=1,count=2,variant='M2')));r['shrink_trace'][0]['decision']='ACCEPT'
  elif name=='first-erased':r['first_failure']=None
  elif name=='local-as-global':r['global_minimum']=r['final_counterexample'];r['local_equals_global']=True
  elif name=='global-count':r['global_failures']=0
  elif name=='enumeration-missing':r['enumeration'].pop()
  else:r['generated'][0]['expected']=r['generated'][0]['actual'];r['generated'][0]['failed']=False
  try:check(r)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant accepted: '+name)
 return dict(rows=rows,refused=bad,tuple_schema=tuples,mutants=killed,cycle=cycle)
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def main():
 o=R/'observations';raw=o/'attempt-01.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists() and not receipt.exists();d=exercise();d.update(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),library_executed=False);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(receipt.read_text());assert rc['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(r) for r in new['rows']]==[semantic(r) for r in old['rows']] and [semantic(r) for r in new['refused']]==[semantic(r) for r in old['refused']]
  for k in ['tuple_schema','mutants','cycle']:assert new[k]==old[k]
  rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes']
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['transport_no_normal_answer'] and qa['read_refusal']
  for v in qa['prediction_changes']+qa['condition_changes']:
   assert all(v[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','generated','shrink','global']) and not v['open']
  assert [v['prediction'] for v in qa['prediction_changes']]==['boundary','global','separate','unknown',''] and len(qa['condition_changes'])==4
  assert len(qa['links'])==7 and all(v['chars']>0 and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==24
  for observed,expected in zip(b['rows'],old['rows']):
   assert observed==projection(expected,observed['started_utc'],observed['ended_utc'])
 print('PASS: 24 finite cases / 8 config refusals / 7 tuple schema refusals / 8 mutants / full256 LCG cycle; no library execution')
def projection(r,start=None,end=None):
 return dict(inputs=r['inputs'],status=r['status'],started_utc=start or r['started_utc'],ended_utc=end or r['ended_utc'],generated=[dict(index=e['index'],state=e['state'],input=e['input'],expected=e['expected'],actual=e['actual'],failed=e['failed']) for e in r['generated']],first_failure=r['first_failure'],first_failure_index=r['first_failure_index'],shrink=[[e['candidate'],e['decision']] for e in r['shrink_trace']],final_counterexample=r['final_counterexample'],global_minimum=r['global_minimum'],global_failures=r['global_failures'],local_equals_global=r['local_equals_global'],enumeration_count=len(r['enumeration']),enumeration_fail_bits=''.join('1' if e['failed'] else '0' for e in r['enumeration']))
if __name__=='__main__':main()
