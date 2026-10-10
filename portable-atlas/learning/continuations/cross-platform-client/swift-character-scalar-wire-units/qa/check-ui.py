import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT));from checker import verify_row,TABLE
Q=ROOT/'qa'
def snap():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def cleared(s):
 assert s['resultsHidden'] and s['answerHidden'] and not s['answerOpen'] and not s['traceOpen'];assert all(v=='' for v in s['fields'].values());assert s['raw'] is None
expected={e['id']:e for e in TABLE['rows']}
before=snap();requests=list((ROOT/'observations/20261005T151257838190Z-preview/requests').glob('*.json'));assert len(requests)==106
for path in requests:
 raw=json.loads(path.read_text());verify_row(raw['run']);assert raw['input_json']==raw['run']['stdin'] and raw['request_id']==path.stem and raw['compile']['exit']==0
 for n,d in raw['source_digests'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n

def check_result(s,e,pred=None):
 f=s['fields'];raw=json.loads((ROOT/s['raw']).read_text());verify_row(raw['run']);r=raw['run']['result'];assert raw['input_json']==s['input'] and json.loads(f['trace'])==raw['run'] and raw['request_id'] in f['run']
 assert json.loads(f['normal'])==e['expected']['normal'] and json.loads(f['faulty'])==e['expected']['faulty'];assert not s['resultsHidden']
 if pred is not None:assert s['message'].startswith('予想未選択。' if not pred else '予想と一致。' if pred==e['category'] else '予想と不一致。')
 if e['category']=='input':assert s['answerHidden'] and not s['answerOpen'] and f['answer-body']=='' and f['counts']=='測定なし' and '正常答えなし' in f['classification']
 else:
  c=e['expected']['decoded'];assert json.loads(f['counts'])=={k:c[k] for k in ['character','scalar','utf16','utf8']};assert not s['answerHidden']
  for k,label in [('character','Character'),('scalar','scalar'),('utf16','UTF16'),('utf8','UTF8')]:assert f'{label}={c[k]}' in f['answer-body']
  n=e['expected']['normal'];fa=e['expected']['faulty'];assert f"正常scalar gate={str(n['scalar_ok']).lower()}、byte gate={str(n['byte_ok']).lower()}で{'受入' if n['accepted'] else '拒否'}" in f['answer-body'];assert f"故障は{'受入' if fa['accepted'] else '拒否'}" in f['answer-body']
 assert s['viewport']==s['scrollWidth']
rows=json.loads((Q/'iab-matrix.json').read_text());preds=['','accepted','mismatch','refused','input'];assert len(rows)==65 and {(r['case'],r['prediction']) for r in rows}=={(c,p) for c in expected for p in preds}
for row in rows:
 e=expected[row['case']];reset=row['caseReset'];cl=row['cleared'];co=row['compared'];op=row['opened'];cleared(reset);cleared(cl);assert reset['prediction']=='' and reset['input']==e['input_json'] and cl['prediction']==row['prediction'];check_result(co,e,row['prediction']);assert not co['answerOpen'] and not co['traceOpen'];assert op['answerOpen']==(e['category']!='input') and op['traceOpen'] and co['fields']==op['fields']
controls=json.loads((Q/'prediction-controls.json').read_text());assert len(controls)==5 and {r['target'] for r in controls}==set(preds)
for r in controls:
 s,c=r['success'],r['cleared'];assert s['message'].startswith('予想と一致。') and s['answerOpen'] and s['traceOpen'] and s['fields']['answer-body'];cleared(c);assert c['prediction']==r['target']!=s['prediction'] and c['input']==s['input']
edits=json.loads((Q/'editable-controls.json').read_text());assert len(edits)==13 and {r['target_case'] for r in edits}==set(expected)
for r in edits:
 s,c=r['success'],r['cleared'];assert s['message'].startswith('予想と一致。') and s['answerOpen'] and s['traceOpen'] and s['input']!=r['target'];cleared(c);assert c['input']==r['target'] and c['prediction']==s['prediction'] and c['scenario']==s['scenario'];check_result(r['compared'],expected[r['target_case']],c['prediction']);assert r['opened']['answerOpen']==(r['target_case'] not in ['number','malformed'])
stales=[json.loads((Q/'stale-response.json').read_text())]+json.loads((Q/'stale-controls.json').read_text());assert len(stales)==3
for s in stales:
 cleared(s['pending']);assert s['pending']['message']=='実SwiftでJSON往復を実行中です。';cleared(s['changed']);cleared(s['after_old_response']);assert s['changed']==s['after_old_response'];assert len(s['request_files'])==2
 raw=[json.loads((ROOT/n).read_text()) for n in s['request_files']];assert len({r['request_id'] for r in raw})==2
 final=s['new_response'];assert final['raw'] in s['request_files'];e=next(e for e in TABLE['rows'] if e['input_json']==final['input']);check_result(final,e,final['prediction']);assert s['new_opened']['answerOpen']
host=json.loads((Q/'host-failure.json').read_text());assert host['success']['answerOpen'] and host['success']['fields']['answer-body'];cleared(host['failure']);assert host['failure']['message'].startswith('実行/通信失敗。正常答えは生成していません。') and host['owned_server_stop_exit']==0
caps=json.loads((Q/'capture-dom.json').read_text());assert len(caps)==3
for c in caps:
 s=c['dom'];e=next(e for e in TABLE['rows'] if e['input_json']==s['input']);check_result(s,e,s['prediction']);assert (Q/(c['name']+'.jpg')).read_bytes()[:2]==b'\xff\xd8'
for p in (ROOT/'observations').glob('*preview/owned-tmp-cleanup.json'):assert json.loads(p.read_text())['owned_tmp_cleaned']
preview=json.loads((Q/'preview.json').read_text());assert preview['server']['stopped'] and preview['iab']['status']=='closed' and preview['iab']['blank_closed'] and preview['viewport_reset']
links=[]
for doc in [ROOT/'README.md',ROOT/'index.html']:
 targets=re.findall(r'\]\(([^)]+)\)',doc.read_text()) if doc.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',doc.read_text())
 for target in targets:
  if target.startswith(('https:','http:','#')):continue
  assert (doc.parent/target.split('#')[0]).exists(),target;links.append(str(doc.relative_to(ROOT))+':'+target)
assert snap()==before
print(json.dumps({'status':'passed','immutable_real_swift_requests':106,'matrix_comparisons':65,'prediction_controls':5,'edited_inputs_real_results':13,'stale_responses_suppressed':3,'decode_failure_normal_answers':0,'host_failure_normal_answers':0,'captures':3,'local_links_exist':links,'read_only_files':len(before),'all_hash_mtime_equal':True},ensure_ascii=False))
