# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,tempfile,copy,platform
from pathlib import Path
from runner import run,FIXTURES,BASE
from oracle import check,EXPECTED
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def exercise(dest=None):
 hand=json.loads((R/'hand-oracle.json').read_text());assert hand['fixed_before_implementation']
 assert hand['cases']=={k:dict(status=s,apply_writes=w,conflicts=f,bytes=b) for k,(s,w,f,b) in EXPECTED.items()}
 rows=[]
 with tempfile.TemporaryDirectory(prefix='atlas-threeway-check-owned-') as tmp:
  for c in FIXTURES:
   d=Path(tmp)/c;d.mkdir();r=run(c,copies=d);check(r,d if r['fixture_created'] else None);rows.append(r)
   if dest:
    import shutil
    shutil.copytree(d,dest/c)
 invalid=[]
 for local,path in [(dict(BASE,unknown=1),'project.json'),(dict(BASE,templateVersion=True),'project.json'),(dict(BASE,templateVersion=0),'project.json'),(dict(BASE,owner='unknown'),'project.json'),(dict(BASE,description=[]),'project.json'),(BASE,'../outside'),(BASE,'/outside'),(None,'project.json')]:
  r=run('preserve',local,path);assert r['status']=='REFUSED_INPUT' and not r['fixture_created'] and r['setup_writes']==r['apply_writes']==0;invalid.append(r)
 mutants=[]
 for label,c,field,value in [('lost-user-edit','preserve','after_bytes',EXPECTED['overwrite-fault'][3]),('conflict-write','conflict','apply_writes',1),('same-change-conflict','same-change','conflicts',['description']),('wrong-version','preserve','final',dict(templateVersion=1,owner='team-b',description='user')),('conflict-fields','owner-conflict','conflicts',[]),('failure-applied','failure','status','APPLIED')]:
  r=copy.deepcopy(next(x for x in rows if x['case']==c));r[field]=value
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
  assert not args;rows,invalid,mutants=exercise();data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and [semantic(r) for r in invalid]==[semantic(r) for r in data['invalid']] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  for r in data['rows']:check(r,folder/r['case'] if r['fixture_created'] else None)
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and [v['prediction'] for v in qa['prediction_changes']]==['preserve','overwrite','conflict','']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert qa['stale_ignored'] and qa['failure_no_normal_answer'] and len(qa['links'])==5 and all(v['chars'] and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  assert qa['cleanup']['protected_before']==qa['cleanup']['protected_after']
  assert qa['path_refusal']['answer']==qa['path_refusal']['body']=='' and not qa['path_refusal']['open'] and qa['path_refusal']['comparison']=='REFUSED_INPUT'
  assert qa['local_override']['after']=='{\"description\":\"new\",\"owner\":\"team-c\",\"templateVersion\":2}\n' and 'team-c' in qa['local_override']['answer']
  for row in json.loads((o/'browser-cases.json').read_text())['rows']:check(row)
 print('PASS: actual tmp file write/read 9 cases; 8 pre-tree refusals; 6 independent mutation rejections; literal exact bytes/conflict fields')
if __name__=='__main__':main()
