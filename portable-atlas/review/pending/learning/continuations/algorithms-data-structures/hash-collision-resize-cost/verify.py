# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,copy,hashlib,datetime,platform
from pathlib import Path
from cases import configs
from model import evaluate
from chaining import Chaining
from oracle import check
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and 'observations' not in p.parts}
def semantic(r):return {k:v for k,v in r.items() if k not in ['started_utc','ended_utc','environment']}
def projection(r):return {k:r[k] for k in ['inputs','status','differences','total_comparisons','total_moves','final_capacity','final_entries']}
def exercise():
 rows=[]
 for c in configs():x=evaluate(c);check(x);rows.append(x)
 base=configs()[0];bad=[None,[],True,{},dict(base,extra=1),dict(base,fixture=[]),dict(base,fixture={}),dict(base,fixture='unknown'),dict(base,policy=[]),dict(base,policy='unknown'),dict(base,mode={}),dict(base,mode='unknown')];refused=[]
 for c in bad:
  x=evaluate(c);assert x['status']=='REFUSED_INPUT' and x['trace']==[] and x['oracle']==[] and x['total_comparisons'] is None;refused.append(x)
 operation_bad=[['put',True,'A'],['find',0.0],['find','0'],['delete',49],['put',0,''],['put',0,'abc'],['unknown',0],['put',0],['find',0,'A']];op_refused=[]
 for op in operation_bad:
  table=Chaining('doubling','normal')
  try:table.step(op)
  except ValueError:assert table.buckets==[[],[]] and table.n==0;op_refused.append(op)
  else:raise AssertionError('operation accepted')
 names=['same-bucket-is-same-key','update-increases-size','delete-loses-collision','wrong-negative-bucket','grow-at-equality','missing-rehash-move','comparison-counter','claim-fault-always-fails'];killed=[]
 for name in names:
  x=copy.deepcopy(rows[0]);t=x['trace']
  if name=='same-bucket-is-same-key':t[1]['found']=True
  elif name=='update-increases-size':t[4]['n_after']+=1
  elif name=='delete-loses-collision':t[5]['after'][0]=[]
  elif name=='wrong-negative-bucket':x=copy.deepcopy(rows[16]);x['trace'][0]['bucket']=0
  elif name=='grow-at-equality':x=copy.deepcopy(rows[14]);x['trace'][1]['capacity_after']=4
  elif name=='missing-rehash-move':x=copy.deepcopy(rows[2]);x['trace'][2]['rehash_moves']=[]
  elif name=='comparison-counter':t[0]['key_comparisons']=1
  else:x=copy.deepcopy(rows[3]);x['differences']=[6]
  try:check(x)
  except AssertionError:killed.append(name)
  else:raise AssertionError('mutant accepted: '+name)
 return dict(rows=rows,refused=refused,operation_refused=op_refused,mutants=killed)
def main():
 o=R/'observations';raw=o/'attempt-01.json';rc=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not raw.exists();d=exercise();d.update(source_hashes=sources(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(python=platform.python_version(),system=platform.system()),command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0);raw.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  old=json.loads(rc.read_text());assert old['ui_pending'] and not (o/'initial-receipt.json').exists() and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(rc.read_bytes());rc.write_text(json.dumps(dict(source_hashes=sources(),raw_sha256=sha(raw),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ['receipt.json','read-only-proof.json']}),indent=2)+'\n')
 else:
  assert not args;new=exercise();old=json.loads(raw.read_text());assert [semantic(x) for x in new['rows']]==[semantic(x) for x in old['rows']] and new['refused']==old['refused'] and new['operation_refused']==old['operation_refused'] and new['mutants']==old['mutants'];receipt=json.loads(rc.read_text());assert not receipt['ui_pending'] and receipt['source_hashes']==sources() and receipt['raw_sha256']==sha(raw)
  for f,h in receipt['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==old['source_hashes'];qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['explicit_reset'] and qa['transport_no_normal_answer']
  for x in qa['prediction_changes']+qa['condition_changes']+[qa['reset']]:assert all(x[k]=='' for k in ['answer','body','comparison','raw','summary','diagram','trace']) and not x['open']
  assert all(x['chars']>0 and x['status'].startswith('READ_COMPLETE') for x in qa['links']) and len(qa['links'])==11
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
  b=json.loads((o/'browser-cases.json').read_text());assert len(b['rows'])==24
  for obs,expected in zip(b['rows'],old['rows']):assert obs['projection']==projection(expected) and obs['peer_projection']==projection(next(x for x in old['rows'] if x['inputs']==dict(expected['inputs'],policy='doubling' if expected['inputs']['policy']=='fixed' else 'fixed')))
 print('PASS: 24 finite conditions / 12 config refusals / 9 operation refusals / 8 mutants; comparisons and rehash moves are logical counts')
if __name__=='__main__':main()
