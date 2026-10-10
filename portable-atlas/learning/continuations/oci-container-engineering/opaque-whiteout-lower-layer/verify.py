# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,tempfile,copy,platform
from pathlib import Path
from runner import run,CASES
from oracle import check,MAPS,REJECT
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def semantic(r):return {k:v for k,v in r.items() if k not in ('started_utc','ended_utc')}
def exercise(dest=None):
 hand=json.loads((R/'hand-oracle.json').read_text());assert hand['fixed_before_implementation'] and hand['maps']==MAPS and hand['refusals']==REJECT
 rows=[]
 with tempfile.TemporaryDirectory(prefix='atlas-opaque-check-owned-') as tmp:
  for c in CASES:
   d=Path(tmp)/c;d.mkdir();r=run(c,copies=d);check(r,d);rows.append(r)
   if dest:
    import shutil
    shutil.copytree(d,dest/c)
 for params in [('opaque-before','newA','d/.wh..wh..opq\x00other'),('opaque-before','newA','日本語'),('opaque-before','bad','d/.wh..wh..opq'),('opaque-before','newA','x'*41)]:
  refused=run(*params);assert refused['status']=='REFUSED_INPUT' and refused['lower_before'] is None and refused['lower_after'] is None and 'upper_tar_sha256' not in refused
 mutants=[]
 for label,c,field,value in [('lower-survives','opaque-before','final_map',MAPS['no-opaque']),('upper-erased','opaque-after','final_map',{'keep':'k'}),('marker-visible','opaque-before','final_map',dict(MAPS['opaque-before'],**{'d/.wh..wh..opq':''})),('lower-mutated','nonempty','lower_after',{}),('nonempty-applied','nonempty','status','APPLIED'),('failure-success','failure','status','APPLIED')]:
  r=copy.deepcopy(next(x for x in rows if x['case']==c));r[field]=value
  try:check(r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('accepted mutation')
 return rows,mutants

def main():
 o=R/'observations';folder=o/'attempt-01';raw=folder/'raw.json';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not folder.exists();folder.mkdir();rows,mutants=exercise(folder);raw.write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),source_hashes=sources(),rows=rows,mutants=mutants),ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(receipt.read_text());assert old['ui_pending'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());assert json.loads((o/'ui-qa.json').read_text())['passed'];receipt.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;rows,mutants=exercise();data=json.loads(raw.read_text());assert [semantic(r) for r in rows]==[semantic(r) for r in data['rows']] and mutants==data['mutants'];rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources() and rc['raw_sha256']==sha(raw)
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==data['source_hashes']
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  for r in data['rows']:check(r,folder/r['case'])
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and [v['prediction'] for v in qa['prediction_changes']]==['lower-only','all','keep-b','']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert qa['stale_ignored'] and qa['failure_no_normal_answer'] and len(qa['links'])==5 and all(v['chars'] and not v['read_failure'] for v in qa['links'])
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  for row in json.loads((o/'browser-cases.json').read_text())['rows']:check(row)
 print('PASS: actual USTAR 13 cases; 8 subset refusals / lower map unchanged; 6 independent mutations; manual USTAR member decoder')
if __name__=='__main__':main()
