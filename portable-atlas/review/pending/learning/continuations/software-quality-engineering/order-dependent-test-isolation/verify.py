# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from model import evaluate
from oracle import H,check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for h in H['cases']:
  r=evaluate({k:h[k] for k in ['isolation','order']});check(r);rows.append(r)
 base=dict(isolation='shared',order='override-first');bad=[None,[],True,{},dict(base,extra=1),dict(base,isolation=True),dict(base,isolation=[]),dict(base,isolation={}),dict(base,isolation='unknown'),dict(base,order=None),dict(base,order=[]),dict(base,order={}),dict(base,order='unknown')];refused=[]
 for c in bad:
  r=evaluate(c);assert r['status']=='REFUSED_INPUT' and r['attempts']==[] and not r['actual_unittest_executed'];refused.append(r)
 names=['favorable-only','failure-exit-zero','weaken-assertion','hide-state-leak','fixture-not-reset','teardown-skipped','runner-not-executed'];killed=[]
 for name in names:
  r=copy.deepcopy(rows[0] if name!='fixture-not-reset' else rows[2]);a=r['attempts'][0]
  if name=='favorable-only':r['attempts']=r['attempts'][:1]
  elif name=='failure-exit-zero':a['exit_status']=0
  elif name=='weaken-assertion':a['worker']['trace'][1]['expected']=8;a['stdout']=json.dumps(a['worker'])
  elif name=='hide-state-leak':a['worker']['trace'][1]['body_before']=0;a['stdout']=json.dumps(a['worker'])
  elif name=='fixture-not-reset':a['worker']['trace'][0]['teardown_after']=2;a['stdout']=json.dumps(a['worker'])
  elif name=='teardown-skipped':del a['worker']['trace'][1]['teardown_after'];a['stdout']=json.dumps(a['worker'])
  else:r['actual_unittest_executed']=False
  try:check(r)
  except (AssertionError,KeyError):killed.append(name)
  else:raise AssertionError('mutant accepted')
 return dict(rows=rows,refused=refused,mutants=killed)
def semantic(r):
 if r['status']=='REFUSED_INPUT':return dict(inputs=r['inputs'],status=r['status'],attempts=r['attempts'],actual_unittest_executed=r['actual_unittest_executed'])
 return dict(inputs=r['inputs'],status=r['status'],actual_unittest_executed=r['actual_unittest_executed'],attempts=[dict(attempt=a['attempt'],status=a['status'],exit_status=a['exit_status'],worker={k:v for k,v in a['worker'].items() if k not in ['pid','started_utc','ended_utc']}) for a in r['attempts']])
def projection(r):
 return dict(inputs=r['inputs'],status=r['status'],started_utc=r['started_utc'],ended_utc=r['ended_utc'],actual_unittest_executed=r['actual_unittest_executed'],attempts=[dict(attempt=a['attempt'],status=a['status'],exit_status=a['exit_status'],started_utc=a['started_utc'],ended_utc=a['ended_utc'],worker=a['worker'],stderr_kind='ASSERTION_FAILURE_8_NE_10' if 'AssertionError: 8 != 10' in a['stderr'] else 'OK_2_TESTS') for a in r['attempts']])
def main():
 o=R/'observations';raw=o/'attempt-01.json';rc=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(rc.read_text());assert old['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rc.read_bytes());rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(x) for x in new['rows']]==[semantic(x) for x in old['rows']] and [semantic(x) for x in new['refused']]==[semantic(x) for x in old['refused']] and new['mutants']==old['mutants'];receipt=json.loads(rc.read_text());assert not receipt['ui_pending'] and receipt['source_hashes']==sources() and receipt['raw_sha256']==sha(raw)
  for f,h in receipt['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','trace','attempts']) and not x['open']
  assert len(qa['links'])==12 and all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']);assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==4
  for obs,expected in zip(b['rows'],old['rows']):
   assert obs['inputs']==expected['inputs'] and obs['status']=='ATTEMPTS_RECORDED' and obs['actual_unittest_executed'] and len(obs['attempts'])==2
   restored=copy.deepcopy(expected)
   for a,x in zip(restored['attempts'],obs['attempts']):a.update({k:x[k] for k in ['attempt','status','exit_status','worker']});a['stdout']=json.dumps(x['worker'])
   check(restored)
 print('PASS: 4 finite mode/order conditions x2 real unittest child attempts / 13 refusals / 7 mutants; expected assertion failure retained')
if __name__=='__main__':main()
