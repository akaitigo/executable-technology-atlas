# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from model import evaluate
from oracle import H,config,check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];rows=[]
 for f in H['fixtures']:
  for fold in [False,True]:r=evaluate(config(f,fold));check(r,f,fold);rows.append(r)
 base=config(H['fixtures'][0],False);bad=[None,[],True,{},dict(base,extra=1),dict(base,fold=0),dict(base,fold='false'),dict(base,report=None),dict(base,report={}),dict(base,report=[dict(id='m1',status='unknown')]),dict(base,report=[dict(id='m1',status=[])]),dict(base,report=[dict(id='m1',status={})]),dict(base,report=[dict(id='m1',status=True)]),dict(base,report=[dict(id=1,status='Killed')]),dict(base,report=[dict(id='m9',status='Killed')]),dict(base,report=[dict(id='m1',status='Killed',extra=1)]),dict(base,report=[dict(id='m1',status='Killed')]*2),dict(base,report=[dict(id='m'+str(i+1),status='Killed') for i in range(9)])];refused=[]
 for c in bad:
  r=evaluate(c);assert r['status']=='REFUSED_INPUT' and r['canonical'] is None and r['reported'] is None and not r['classifications'];refused.append(r)
 names=['unrun-invalid-as-survived','timeout-undetected','total-denominator','nocoverage-in-covered','zero-is-100','runner-claim','duplicate-ID-group'];killed=[]
 for name in names:
  f=H['fixtures'][0];r=copy.deepcopy(rows[0])
  if name=='unrun-invalid-as-survived':r['canonical']=rows[1]['reported']
  elif name=='timeout-undetected':r['canonical']['metrics']['detected']=1
  elif name=='total-denominator':r['canonical']['ratios']['mutation_score']=r['canonical']['ratios']['detected_over_total_context_only']
  elif name=='nocoverage-in-covered':r['canonical']['group_ids']['covered'].append('m3')
  elif name=='zero-is-100':f=H['fixtures'][-1];r=copy.deepcopy(rows[-2]);r['canonical']['ratios']['mutation_score']['percent']=100
  elif name=='runner-claim':r['runner_executed']=True
  else:r['canonical']['group_ids']['total'].append('m1')
  try:check(r,f,False)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant survived')
 return dict(rows=rows,refused=refused,mutants=killed)
def semantic(r):return {k:v for k,v in r.items() if k not in ['started_utc','ended_utc']}
def projection(r,start=None,end=None):return {k:(start or r[k]) if k=='started_utc' else (end or r[k]) if k=='ended_utc' else r[k] for k in ['inputs','status','started_utc','ended_utc','canonical','reported','classifications','runner_executed','timeout_executed','synthetic_report']}
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
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','counts','classification']) and not x['open']
  assert len(qa['links'])==11 and all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']);assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==20
  for obs,expected in zip(b['rows'],old['rows']):assert obs==projection(expected,obs['started_utc'],obs['ended_utc'])
 print('PASS: 20 fixture/fault cases / 18 input refusals / 7 mutants; synthetic report aggregation only')
if __name__=='__main__':main()
