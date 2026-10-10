# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,platform,copy
from pathlib import Path
from runner import run,CASES
from oracle import check,COMMON,TAILS,COLUMNS
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def exercise():
 hand=json.loads((R/'hand-oracle.json').read_text());assert hand['fixed_before_implementation'] and hand['columns']==COLUMNS and hand['common']==COMMON
 for c,t in TAILS.items():assert hand[c]==t
 rows=[run(c) for c in CASES]
 for row in rows:check(row)
 invalid=[]
 for h in [None,True,0,[],{},'healthy','Unknown','']:
  r=run('degraded',h);assert r['status']=='REFUSED_INPUT' and not r['events'];invalid.append(r)
 mutants=[]
 for label,c,index,field,value in [('degraded-start','degraded',4,'stage2_starts',1),('fault-block','desired-only-fault',4,'stage2_starts',0),('healthy-twice','healthy',5,'stage2_starts',2),('rollback-immediate','rollback',5,'actual','v1'),('old-generation','rollback',5,'generation',1),('synced-means-health','degraded',3,'health','Healthy')]:
  r=copy.deepcopy(next(x for x in rows if x['case']==c));r['events'][index][field]=value
  try:check(r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('accepted mutation')
 return rows,invalid,mutants
def main():
 rows,invalid,mutants=exercise();o=R/'observations';raw=o/'attempt-01/raw.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.parent.exists();raw.parent.mkdir();raw.write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),rows=rows,invalid=invalid,mutants=mutants),ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(receipt.read_text());assert old['ui_pending'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());assert json.loads((o/'ui-qa.json').read_text())['passed'];receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and [semantic(r) for r in invalid]==[semantic(r) for r in data['invalid']] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  for f,h in rc['artifacts'].items():assert sha(R/f)==h,f
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and [v['prediction'] for v in qa['prediction_changes']]==['stop','start','immediate','']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert all(v['held'] for v in qa['position_refusals']) and qa['stale_ignored'] and qa['execution_failure_cleared'] and len(qa['links'])==6
  assert all(v['chars']>0 and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  assert len(qa['positions'])==29 and all(v['matched'] for v in qa['positions'])
  assert qa['cleanup']['protected_before']==qa['cleanup']['protected_after']
  for row in json.loads((o/'browser-cases.json').read_text())['rows']:check(row)
  check(json.loads((o/'final-mapping-server-raw.json').read_text()))
 print('PASS: real finite CPython 7 cases / 29 stage events; 8 host refusals; 6 independent mutation rejections')
if __name__=='__main__':main()
