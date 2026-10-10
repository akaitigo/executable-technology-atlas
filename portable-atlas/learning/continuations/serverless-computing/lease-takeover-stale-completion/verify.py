# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,tempfile,copy,platform
from pathlib import Path
from runner import run,operate,SCHEDULES
from oracle import check,EXPECTED
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def exercise(dest=None):
 hand=json.loads((R/'hand-oracle.json').read_text());assert hand['fixed_before_implementation'] and hand['lease']==10
 assert hand['cases']=={k:[[c,s] for c,s in v] for k,v in EXPECTED.items()}
 rows=[]
 with tempfile.TemporaryDirectory(prefix='atlas-lease-check-owned-') as tmp:
  for c in SCHEDULES:
   db=Path(tmp)/(c+'.sqlite');r=run(c,db_copy=db);check(r,db);rows.append(r)
   if dest:
    import shutil
    shutil.copy2(db,dest/(c+'.sqlite'))
 invalid=[]
 base=dict(op='complete',owner='A',generation=1,tick=9,result=100)
 for field,value in [('generation',None),('owner','C'),('tick',True),('tick',-1),('generation',True),('generation',0),('result',True)]:
  op=dict(base);op[field]=value;r=operate(Path('never-opened.sqlite'),op);assert r['status']=='REFUSED_INPUT' and not r['sql_issued'];invalid.append(r)
 mutants=[]
 for label,c,index,field,value in [('stale-accepted','takeover',4,'rowcount',1),('wrong-final','takeover',4,'after',['DONE','B',2,20,100]),('expiry-inclusive','expiry-boundary',1,'rowcount',1),('owner-ignored','owner-mismatch',1,'rowcount',1),('generation-ignored','generation-mismatch',1,'rowcount',1),('done-reaccepted','done-replay',2,'rowcount',1)]:
  r=copy.deepcopy(next(x for x in rows if x['case']==c));r['events'][index][field]=value
  try:check(r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('accepted mutation')
 return rows,invalid,mutants
def main():
 o=R/'observations';folder=o/'attempt-01';raw=folder/'raw.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not folder.exists();folder.mkdir();rows,invalid,mutants=exercise(folder);raw.write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),rows=rows,invalid=invalid,mutants=mutants),ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(receipt.read_text());assert old['ui_pending'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());assert json.loads((o/'ui-qa.json').read_text())['passed'];receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;rows,invalid,mutants=exercise();data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and invalid==data['invalid'] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  for r in data['rows']:check(r,folder/(r['case']+'.sqlite'))
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and [x['prediction'] for x in qa['prediction_changes']]==['keep','overwrite','boundary','']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert all(v['held'] for v in qa['position_refusals']) and qa['stale_ignored'] and qa['sql_exception_no_normal_answer'] and len(qa['links'])==7
  assert all(v['chars']>0 and not v['read_failure'] for v in qa['links']) and len(qa['positions'])==25 and all(v['matched'] for v in qa['positions'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  assert qa['cleanup']['protected_before']==qa['cleanup']['protected_after']
  assert [v['last_rowcount'] for v in qa['tick_boundaries']]==[1,0,None,None]
  assert all(v['answer']==v['body']=='' and not v['open'] and v['comparison']=='REFUSED_INPUT' for v in qa['tick_boundaries'][2:])
  assert qa['before_state_continuity']
  for row in json.loads((o/'browser-cases.json').read_text())['rows']:check(row)
 print('PASS: real SQLite 9 cases / 25 operations; 7 SQL-before refusals; 6 independent mutations; saved DB readonly oracle')
if __name__=='__main__':main()
