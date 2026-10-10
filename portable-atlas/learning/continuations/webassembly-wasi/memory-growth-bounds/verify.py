# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import argparse,copy,datetime,hashlib,json,platform
from pathlib import Path
from oracle import check,check_refusal,binary_contract
R=Path(__file__).resolve().parent
SOURCES=['fixture.json','hand-oracle.json','binary.js','runtime.js','app.js','index.html','source.html','oracle.py','verify.py','route.py','serve.py','README.md','VERIFICATION.md','sources.json','coverage.json','skills/memory-growth/SKILL.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {f:sha(R/f) for f in SOURCES}
def calculate():
 runs=json.loads((R/'observations/browser-transcript.json').read_text());invalid=json.loads((R/'observations/host-invalid-transcript.json').read_text());fixture=json.loads((R/'fixture.json').read_text());hand=json.loads((R/'hand-oracle.json').read_text())
 assert hand['fixed_before_implementation'] and hand['page_bytes']==65536 and hand['growth']['bytes']==131072
 assert [(r['case'],r['address']) for r in runs]==[(c['id'],c['address']) for c in fixture['cases']]
 for r in runs:check(r)
 for r in invalid:check_refusal(r)
 assert [r['address'] for r in invalid]==[-1,131073,True,1.5,'65535',None,{},[]]
 mutations=[]
 for label,name,op,field,value in [('wrong-last-byte','last-byte','core-load8','value',170),('trap-class','initial-oob','core-load8','error_class','RangeError'),('old-index-zero','grow-one','old-typed-index','value',0),('dataview-range','grow-one','old-data-get','error_class','RangeError'),('js-grow-as-core','js-max','js-grow','error_class','RuntimeError'),('core-grow-zero','core-max','core-grow','value',0)]:
  r=copy.deepcopy(next(r for r in runs if r['case']==name));next(e for e in r['events'] if e['op']==op)[field]=value
  try:check(r)
  except AssertionError:mutations.append(dict(label=label,rejected=True))
  else:raise AssertionError('mutation accepted '+label)
 return dict(browser_runs=runs,host_invalid=invalid,mutation_rejections=mutations,binary_contract=binary_contract(),scope='saved actual IAB execution; checker does not run WebAssembly')
def main():
 p=argparse.ArgumentParser();p.add_argument('--record');p.add_argument('--seal-record',action='store_true');a=p.parse_args();data=calculate();folder=R/'observations/attempt-01';receipt=R/'observations/receipt.json'
 if a.record:
  assert not (R/'observations/address-revision-receipt.json').exists(),'revision frozen'
  assert a.record=='attempt-01' and not folder.exists(),'only unused attempt'
  folder.mkdir();raw=dict(command=['python3','-B','verify.py','--record','attempt-01'],recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_status=0,provenance='actual tool-returned IAB JSON transcription with field-equality-verified final rerun timestamps; see transcription-provenance.json; Python never reexecutes Browser or fabricates outcomes',browser_actions='IAB tab27: choose each fixture, Browserで実行, read raw after completion; host invalid8 separately',environment=dict(python_checker=platform.python_version(),system=platform.system(),machine=platform.machine(),browser='Codex In-app Browser',engine_version='not exposed by tool'),inputs=json.loads((R/'fixture.json').read_text()),source_hashes=hashes(),**data)
  (folder/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');receipt.write_text(json.dumps(dict(source_hashes=hashes(),artifacts={'observations/attempt-01/raw.json':sha(folder/'raw.json'),'observations/browser-transcript.json':sha(R/'observations/browser-transcript.json'),'observations/host-invalid-transcript.json':sha(R/'observations/host-invalid-transcript.json')},ui_pending=True),indent=2)+'\n')
 elif a.seal_record:
  assert not (R/'observations/address-revision-receipt.json').exists(),'revision frozen'
  old=json.loads(receipt.read_text());assert old['ui_pending'];(R/'observations/initial-receipt.json').write_bytes(receipt.read_bytes());assert json.loads((R/'observations/ui-qa.json').read_text())['passed']
  receipt.write_text(json.dumps(dict(source_hashes=hashes(),artifacts={str(f.relative_to(R)):sha(f) for f in R.rglob('*') if f.is_file() and str(f.relative_to(R)).startswith('observations/') and f.name not in ('receipt.json','read-only-proof.json')},ui_pending=False,sealed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2)+'\n')
 else:
  raw=json.loads((folder/'raw.json').read_text());assert {k:raw[k] for k in data}==data
  receipt_data=json.loads(receipt.read_text());assert not receipt_data['ui_pending'] and receipt_data['source_hashes']==hashes()
  for f,h in receipt_data['artifacts'].items():assert sha(R/f)==h,f
  initial=json.loads((R/'observations/initial-receipt.json').read_text());assert initial['source_hashes']==raw['source_hashes']
  for f,h in initial['artifacts'].items():assert sha(R/f)==h,f
  qa=json.loads((R/'observations/ui-qa.json').read_text());assert qa['passed'] and qa['conditions_cleared']==7
  assert [p['prediction'] for p in qa['prediction_changes']]==['views','same','boundary','']
  for v in qa['prediction_changes']+qa['condition_controls']:assert all(v[k]=='' for k in ['comparison','answer','body']) and not v['open']
  assert [v['input'] for v in qa['position_refusals']]==['-1','20','']
  for v in qa['position_refusals']:assert v['open'] and v['body'] and v['comparison'] and v['answer'] and v['held_all_fields']
  assert qa['stale_response']['accepted_case']=='grow-one' and qa['stale_response']['ignored_case']=='last-byte' and qa['stale_response']['unchanged_after_release']
  check(qa['stale_response']['raw_ignored']);check(qa['stale_response']['raw_accepted'])
  assert qa['execution_failure']['answer']==qa['execution_failure']['body']=='' and not qa['execution_failure']['open'] and qa['execution_failure']['comparison']=='EXECUTION_FAILURE: 前の比較・正常答えを破棄'
  assert len(qa['links'])==7 and qa['resources']['own_tab_closed'] and qa['resources']['own_server_exit']==0 and not qa['resources']['own_port_listening']
  assert qa['resources']['protected_before']['53478']==qa['resources']['protected_after']['53478']==3901
  assert set(qa['resources']['protected_before'])==set(qa['resources']['protected_after'])=={'53478','60285'} and qa['resources']['protected_no_actions']
 if not a.record and not a.seal_record:
  revision=json.loads((R/'observations/address-revision-raw.json').read_text())
  assert [(v['raw']['case'],v['raw']['address']) for v in revision['rows']]==[(c,a) for c in ['last-byte','initial-oob'] for a in [0,1,65535,65536,131072]]
  for v in revision['rows']:
   r=v['raw'];e=r['events'][-1];addr=r['address'];assert r['module_hex']==data['browser_runs'][0]['module_hex'] and r['module_sha256']==data['browser_runs'][0]['module_sha256'] and r['events'][:-1]==data['browser_runs'][0]['events'][:-1]
   assert r['started_utc']<=r['ended_utc'] and e['address']==addr and r['instantiated'] and r['stage']=='complete'
   expected='答え: 初期address '+str(addr)
   if addr>=65536:assert r['status']=='EXPECTED_TRAP' and e['error_class']=='RuntimeError' and e['error_message']=='memory access out of bounds';expected+='は実RuntimeErrorのbounds trap。'
   else:
    val={0:7,1:0,65535:171}[addr];assert r['status']=='LOAD_OK' and e['value']==val and e['outcome']=='value';expected+='は'+str(val)+'。1pageの範囲内。'
   assert v['answer']==expected and v['open'] and v['input_reset']==dict(answer='',body='',open=False,prediction='')
  manifest=json.loads((R/'observations/address-revision-manifest.json').read_text())
  for f,m in manifest.items():
   p=R/'observations/address-revision-history'/f;assert sha(p)==m['sha256'] and p.stat().st_mtime_ns==m['mtime_ns']
  revrc=json.loads((R/'observations/address-revision-receipt.json').read_text());assert revrc['source_hashes']==hashes()
  for f,h in revrc['artifacts'].items():assert sha(R/f)==h
 print('PASS: saved actual IAB 7 cases / 50 API events; 8 host refusals; 6 mutation rejections; 72-byte core contract; no Browser reexecution')
if __name__=='__main__':main()
