# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,copy,platform
from pathlib import Path
from runner import run,CASES
from oracle import check,HAND
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert HAND['fixed_before_implementation'];rows=[]
 for c,args in CASES.items():
  r=run(*args);check(c,r);rows.append(dict(case=c,raw=r))
 assert run(slot=0)['trace'][0]['selected']=='A' and run(slot=3)['trace'][0]['selected']=='B' and run(slot=4)['status']=='REFUSED'
 assert run(hb=False,slot=0)['trace'][0]['selected']=='A' and run(hb=False,slot=1)['status']=='REFUSED'
 assert run(ha='true')['status']=='REFUSED'
 mutants=[]
 for label,c,field,value in [('wrong-slot0','normal','trace',[dict(slot=0,selected='B',healthy=True,outcome='SELECTED')]),('dead-candidate','b-down','candidates',['A','B']),('wrong-bound','normal','bounds',[['A',0,2],['B',2,4]]),('loss-hidden','late-health-fault','trace',[dict(slot=i,selected=n,healthy=True,outcome='SELECTED') for i,n in enumerate(['A','B','B','B'])]),('refusal-success','slot-total','status','SELECTED'),('failure-success','failure','status','SELECTED')]:
  r=copy.deepcopy(next(x['raw'] for x in rows if x['case']==c));r[field]=value
  try:check(c,r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('mutant accepted')
 return rows,mutants
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def main():
 o=R/'observations';raw=o/'attempt-01.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();rows,mutants=exercise();raw.write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,python=platform.python_version(),system=platform.system(),machine=platform.machine(),source_hashes=sources(),rows=rows,mutants=mutants),ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(receipt.read_text());assert rc['ui_pending'] and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;rows,mutants=exercise();data=json.loads(raw.read_text());assert [(v['case'],semantic(v['raw'])) for v in rows]==[(v['case'],semantic(v['raw'])) for v in data['rows']] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['failure_no_normal_answer']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert [v['prediction'] for v in qa['prediction_changes']]==['ratio','all-a','loss','']
  assert len(qa['links'])==5 and all(v['chars']>0 and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  for v in json.loads((o/'browser-cases.json').read_text())['rows']:check(v['case'],v['raw'])
 print('PASS: 15 actual Python cases; 15 enumerated slots; 9 refusal conditions; real RuntimeError; 6 literal-oracle mutants')
if __name__=='__main__':main()
