import sys
sys.dont_write_bytecode=True
import json,subprocess
from pathlib import Path
from verify import check,sha,validate_threads
from oracle import HAND_COUNTS
R=Path(__file__).resolve().parent
b=json.loads((R/'observations/browser.json').read_text());rows=check()['rows']
assert b['observed_all_56'] and len(b['rows'])==56 and b['rendered_summary_cards_seen_exact']
for r,v in zip(rows,b['rows']):
 for n in ('fixture','schedule','accepted_count','seen'):assert r[n]==v[n]
 assert r['trace'][-1]['requests']==v['final_requests']
for schedule,key in [('split-2','split_2_hand_steps'),('atomic-AB','atomic_AB_hand_steps')]:
 r=next(r for r in rows if r['fixture']=='same' and r['schedule']==schedule)
 for i,v in enumerate(b[key]):
  t=r['trace'][i];assert v['step']==i and v['event']==t['event'] and v['accepted_count']==t['accepted_count'] and v['seen']==t['seen']
  assert v['cached_absent']==[t['requests'][n]['cached_absent'] for n in 'AB']
  assert v['statuses']==[t['requests'][n]['status'] for n in 'AB']
assert b['invalid_all_five_steps_unchanged']
assert all(v['change_cleared'] for v in b['predictions']) and [v['answer'] for v in b['predictions']]==['予測は正解','予測は不正解','予測は正解','予測は不正解','予測は未回答']
assert {v['fixture']:v['counts'] for v in b['comparisons']}==HAND_COUNTS
assert b['stored_thread_rows']==14 and b['intentional_failure_visible']
assert len(b['source_links'])==12 and all(v['actual_link_clicked'] and v['viewer_populated'] and v['characters']==len((R/v['file']).read_text()) for v in b['source_links'])
assert b['reset']==dict(fixture='same',schedule='split-2',prediction='unanswered',hidden=True,comparison_hidden=True,raw='',threads='',status='リセット: 未実行')
assert b['previous']=='step 3: Aw / 受入 1件' and b['next']=='step 4: Bw / 受入 2件'
for n in ('run_transport_failure','compare_transport_failure'):assert b[n]==dict(hidden=True,comparison_hidden=True,raw='',status='失敗: Failed to fetch')
assert len(b['screenshots'])==6 and all(v['actual_tool_capture'] and not v['saved'] and v['path'] is None and v['sha256'] is None for v in b['screenshots'])
h=json.loads((R/'observations/http.json').read_text());assert len(h['normal'])==56 and len(h['refusals'])==14 and h['stored_threads_exact']
for r,v in zip(rows,h['normal']):assert v['status']==200 and v['exact'] and v['response']==r
assert all(v['status']==400 for v in h['refusals']) and len(h['sources'])==12 and all(v['exact'] for v in h['sources'])
validate_threads(json.loads((R/'observations/attempt-01/threads.json').read_text()))
a=json.loads((R/'observations/ui-async.json').read_text());live=subprocess.run(['node','ui_async_probe.mjs'],text=True,capture_output=True);assert live.returncode==0 and json.loads(live.stdout)==a
c=json.loads((R/'observations/cleanup.json').read_text());assert c['own']['tab_closed'] and c['own']['listener_after_exit_status']==1 and c['protected_before']==c['protected_after']
archive=R/'observations/review-generation-01';snapshot=json.loads((archive/'snapshot-map.json').read_text())
assert snapshot['file_count']==27 and snapshot['digest']=='2ddedb9139e63d651e44cdb95bf0f231e2d33a03c1fbfe1268f5e5e3d1103c15'
for n,h in snapshot['hashes'].items():assert sha(archive/n)==h
import hashlib
assert hashlib.sha256(json.dumps(snapshot['hashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==snapshot['digest']
review=R/'observations/review-generation-02';u=json.loads((review/'browser.json').read_text());http_review=json.loads((review/'http.json').read_text())
assert u['run_completed_with_witness'] and u['compare_completed_with_witness'] and u['comparison_counts']==[1,2,2,2,2,1,1,1]
assert u['reset_cleared_both'] and u['app_source_characters']==len((R/'app.js').read_text()) and u['current_failure']==dict(hidden=True,raw='',status='失敗: Failed to fetch')
assert u['cleanup']['tab_closed'] and u['cleanup']['listener_after_exit_status']==1
assert http_review['app_source_exact'] and http_review['app_sha256']==sha(R/'app.js')
regression=json.loads((review/'async-before-after.json').read_text());assert regression['old']['exit_status']!=0 and regression['new']['exit_status']==0
assert len(a['rows'])==11
receipt=json.loads((R/'observations/receipt.json').read_text());assert not receipt['ui_pending']
actual={str(p.relative_to(R)):sha(p) for p in sorted(R.rglob('*')) if p.is_file() and p.name not in ('receipt.json','read-only-proof.json')}
assert actual==receipt['hashes']
print(json.dumps(dict(status='passed',browser_rows=56,model_trace_states=252,http_rows=56,http_refusals=14,thread_witnesses=14,broken_barrier_failure=1,ui_async_cases=11,scope='finite module only')))
