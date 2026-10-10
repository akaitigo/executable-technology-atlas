# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,hashlib,copy,platform
from pathlib import Path
from oracle import check,H
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {str(p.relative_to(R)):sha(p) for p in R.rglob('*') if p.is_file() and 'observations' not in p.parts}
def exercise():
 assert H['fixed_before_implementation'];data=json.loads((R/'observations/browser-attempt-01.json').read_text());assert [v['case'] for v in data['rows']]==list(H['cases'])
 for v in data['rows']:check(v['case'],v['raw'])
 mutants=[]
 for label,c,field,value in [('tightly-packed-read','packed','readback',[1,2,3,4,5,6]),('wrong-bits','normal','readback_bits',[0]*6),('wrong-offset','normal','read_offsets',[0,4,8,12,16,20]),('wrong-input-hex','normal','input_hex','00'*32),('validation-as-success','short-binding','status','GPU_SUCCESS'),('not-destroyed','normal','resources_destroyed',0)]:
  r=copy.deepcopy(next(v['raw'] for v in data['rows'] if v['case']==c));r[field]=value
  try:check(c,r)
  except AssertionError:mutants.append(label)
  else:raise AssertionError('mutant accepted')
 return mutants
def main():
 o=R/'observations';receipt=o/'receipt.json';args=sys.argv[1:]
 if args==['--record','attempt-01']:
  assert not receipt.exists();mutants=exercise();(o/'checker-attempt-01.json').write_text(json.dumps(dict(command=['python3','-B','verify.py','--record','attempt-01'],exit_status=0,python=platform.python_version(),system=platform.system(),machine=platform.machine(),gpu_reexecuted=False,mode='saved actual GPU observations, no CPU substitution',mutants=mutants,source_hashes=sources()),indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=sources(),ui_pending=True),indent=2)+'\n')
 elif args==['--seal-record']:
  rc=json.loads(receipt.read_text());assert rc['ui_pending'] and json.loads((o/'ui-qa.json').read_text())['passed'];(o/'initial-receipt.json').write_bytes(receipt.read_bytes());receipt.write_text(json.dumps(dict(source_hashes=sources(),ui_pending=False,artifacts={str(p.relative_to(R)):sha(p) for p in o.rglob('*') if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}),indent=2)+'\n')
 else:
  assert not args;mutants=exercise();rc=json.loads(receipt.read_text());assert not rc['ui_pending'] and rc['source_hashes']==sources()
  for f,h in rc['artifacts'].items():assert sha(R/f)==h
  assert json.loads((o/'checker-attempt-01.json').read_text())['mutants']==mutants
  assert json.loads((o/'initial-receipt.json').read_text())['source_hashes']==json.loads((o/'checker-attempt-01.json').read_text())['source_hashes']
  qa=json.loads((o/'ui-qa.json').read_text());assert qa['passed'] and qa['stale_ignored'] and qa['validation_no_normal_answer'] and qa['transport_no_normal_answer']
  for v in qa['prediction_changes']+qa['condition_changes']:assert v['answer']==v['body']==v['comparison']=='' and not v['open']
  assert [v['prediction'] for v in qa['prediction_changes']]==['correct','shift','error','']
  assert len(qa['links'])==6 and all(v['chars']>0 and not v['read_failure'] for v in qa['links'])
  refused=qa['input_refusal'];assert refused['status']=='REFUSED_INPUT' and not refused['gpu_submitted'] and not refused['gpu_readback'] and refused['resources_destroyed']==0 and not refused['device_destroyed'] and 'input_hex' not in refused
  revision=json.loads((o/'prediction-reset-qa.json').read_text());assert revision['passed'] and revision['delayed_prediction_response_ignored'] and revision['compare_after_release']=='先に実行'
  assert [v['prediction'] for v in revision['prediction_changes']]==['correct','shift','error','']
  for v in revision['prediction_changes']:
   assert all(v[k]=='' for k in ('answer','body','comparison','raw','readback','diagram')) and not v['open'] and v['status']=='未実行'
  manifest=json.loads((o/'prediction-reset-history-manifest.json').read_text());assert manifest['old_file_count']==30
  for f,v in manifest['files'].items():
   archived=o/'prediction-reset-history'/f;assert sha(archived)==v['sha256'] and archived.stat().st_mtime_ns==v['mtime_ns']
  assert revision['cleanup']['own_tab_closed'] and revision['cleanup']['own_server_exit']==0 and not revision['cleanup']['own_port_listening']
  assert qa['cleanup']['own_tab_closed'] and qa['cleanup']['own_server_exit']==0 and not qa['cleanup']['own_port_listening'] and qa['cleanup']['protected_no_actions']
 print('PASS: saved actual GPU 5 compute/readbacks + 1 validation error; literal bytes/bits/offset oracle; 6 mutants; not a GPU reexecution')
if __name__=='__main__':main()
