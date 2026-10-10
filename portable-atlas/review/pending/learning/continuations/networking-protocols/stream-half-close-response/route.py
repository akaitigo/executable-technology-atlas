import sys
sys.dont_write_bytecode=True
import json,subprocess
from pathlib import Path
from verify import validate_raw,sha
R=Path(__file__).resolve().parent
raw=json.loads((R/'observations/attempt-01/raw.json').read_text());validate_raw(raw)
b=json.loads((R/'observations/browser.json').read_text());assert b['observed_all_36'] and len(b['rows'])==36
for r,v in zip(raw['rows'],b['rows']):
 for n in ('fixture','mode','width','execution_status','protocol_outcome','request_received_hex','response_received_hex','closed_filenos'):assert r[n]==v[n]
 assert r['request_decision']['kind']==v['decision']
r=next(r for r in raw['rows'] if r['fixture']=='ping' and r['mode']=='normal' and r['width']==64)
assert len(b['normal_directions'])==len(r['trace'])==14
req=resp=0;reqe=respe=False
for i,(e,v) in enumerate(zip(r['trace'],b['normal_directions'])):
 assert v['step']==i
 for n in ('endpoint','api','result','states'):assert v[n]==e[n]
 if e['api']=='recv':
  if e['result']=='data':
   if e['endpoint']=='B':req+=e['bytes']
   else:resp+=e['bytes']
  if e['result']=='eof':
   if e['endpoint']=='B':reqe=True
   else:respe=True
 assert (v['request_bytes'],v['response_bytes'],v['request_eof'],v['response_eof'])==(req,resp,reqe,respe)
assert all(b[n] for n in ('normal_B_eof_tx_open','normal_B_send_after_eof','fault_A_eof_no_reply','body_refusal_reply','compare_and_probes_both_completed','run_and_probes_both_completed'))
assert [v['answer'] for v in b['predictions']]==['予測は正解','予測は不正解','予測は正解','予測は不正解','予測は未回答'] and all(v['change_cleared'] for v in b['predictions'])
assert b['comparison']==[['normal','passed','refusal','000c4552523a626f64795f656f66'],['fault','passed','missing_response','空']]
assert [v['status'] for v in b['probes']]==['timeout','execution_failure']
assert len(b['sources'])==12 and all(v['actual_link_clicked'] and v['viewer_populated'] and v['characters']==len((R/v['file']).read_text()) for v in b['sources'])
assert b['original']['actual_link_clicked'] and b['original']['disconnecting'] and b['original']['shutdown1']
assert b['reset']==dict(fixture='ping',mode='normal',width='1',prediction='unanswered',hidden=True,comparison_hidden=True,raw='',probes='',status='リセット: 未読')
assert b['previous']=='step 12: A close → ok' and b['next']=='step 13: B close → ok'
for n in ('run_failure','compare_failure'):assert b[n]==dict(hidden=True,comparison_hidden=True,raw='',status='失敗: Failed to fetch')
assert len(b['screenshots'])==6 and all(v['actual_tool_capture'] and not v['saved'] and v['path'] is None and v['sha256'] is None for v in b['screenshots'])
h=json.loads((R/'observations/http.json').read_text());assert len(h['normal'])==36 and len(h['refusals'])==15 and len(h['sources'])==12 and h['probes_exact']
for r,v in zip(raw['rows'],h['normal']):assert v['status']==200 and v['exact'] and v['response']==r
assert all(v['status']==400 for v in h['refusals']) and all(v['exact'] for v in h['sources'])
a=json.loads((R/'observations/ui-async.json').read_text());r=subprocess.run(['node','ui_async_probe.mjs'],text=True,capture_output=True);assert r.returncode==0 and json.loads(r.stdout)==a and len(a['rows'])==11
c=json.loads((R/'observations/cleanup.json').read_text());assert c['own']['tab_closed'] and c['own']['listener_after_exit_status']==1 and c['child_threads']==0 and c['protected_operations'].startswith('none;')
receipt=json.loads((R/'observations/receipt.json').read_text());assert not receipt['ui_pending']
actual={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')};assert actual==receipt['hashes']
print(json.dumps(dict(status='passed',stored_socketpair_rows=36,probes=2,browser_rows=36,http_rows=36,http_refusals=15,direction_steps=14,ui_async_cases=11,scope='finite AF_UNIX unit only')))
