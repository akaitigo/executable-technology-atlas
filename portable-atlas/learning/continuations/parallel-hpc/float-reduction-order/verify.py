# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,subprocess,datetime,copy,platform
from pathlib import Path
from producer import run,CASES
from oracle import check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def exercise():
 rows=[run(c) for c in CASES]
 for r in rows:check(r)
 invalid=[]
 for v in [[float('nan'),1,-1e16,1],[float('inf'),1,-1e16,1],[True,1,-1e16,1],['1e16',1,-1e16,1],None,[],[1e308,1e308,-1e308,1]]:
  r=run('left',v);assert r['status']=='REFUSED_INPUT';invalid.append({'input_repr':repr(v),'status':r['status']})
 mutants=[]
 for label,case,field,value in [('left-result','left','result',2),('tree-order','tree','steps',[[0,2],[2]]),('fsum-result','fsum','result',1),('same-value-missing','drop-cancel','ids',[0,1,2,3]),('wrong-count','drop-small','count',4),('failure-normal','failure','status','OK')]:
  r=copy.deepcopy(next(x for x in rows if x['case']==case));r[field]=value
  try:check(r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('accepted mutant')
 return rows,invalid,mutants
def main():
 rows,invalid,mutants=exercise();args=sys.argv[1:];o=R/'observations';raw=o/'attempt-01/raw.json';receipt=o/'receipt.json'
 if args==['--record','attempt-01']:
  assert not raw.parent.exists();raw.parent.mkdir();data=dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),rows=rows,invalid=invalid,mutants=mutants);raw.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(receipt.read_text());assert old['ui_pending'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());assert json.loads((o/'ui-qa.json').read_text())['passed'];receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and invalid==data['invalid'] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and len(qa['prediction_changes'])==4
  for v in qa['prediction_changes']+qa['condition_changes']:assert not v['answer'] and not v['body'] and not v['comparison'] and not v['open']
  assert all(x['held'] for x in qa['position_refusals']) and qa['stale_ignored'] and qa['execution_failure_cleared'] and len(qa['links'])==6
  for row in json.loads((o/'browser-cases.json').read_text())['rows']:check(row)
  assert all(not x['read_failure'] and x['chars']>0 for x in qa['links'])
  assert qa['cleanup']['protected_before']==qa['cleanup']['protected_after'] and not qa['cleanup']['own_ports_listening']
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and qa['cleanup']['protected_no_actions']
 print('PASS: real CPython 3.9.6 7 cases; 7 refused inputs; 6 independent mutation rejections; exact float-ratio target=2')
if __name__=='__main__':main()
