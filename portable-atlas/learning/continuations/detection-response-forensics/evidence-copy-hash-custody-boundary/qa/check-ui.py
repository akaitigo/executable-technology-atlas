import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runner import ROOT,SOURCES,digest,snapshot
QA=ROOT/'qa/20261005T162231652642Z-iab'
def read(p):return json.loads(p.read_text())
def core(result,expected):assert {k:result.get(k) for k in expected}==expected
def empty(s):
 assert all(s[k]=='' for k in ['answer','normal','faulty','bytes','hashes','ledger','trace','run','classification'])
 assert s['answer_hidden'] and not s['answer_open'] and not s['trace_open'] and s['results_hidden'] and s['raw'] is None
def state(s,e,binding):
 raw=read(ROOT/s['raw']);run=raw['run'];r=run['result'];assert run==json.loads(s['trace']);assert run['stdin']==s['input']==raw['input_json'];core(r,e);assert json.loads(run['stdout'])==r and not run['stderr'];assert raw['source_digests']==binding and raw['request_id'] in s['run'];assert run['exit']==(2 if e['status']=='input_refusal' else 0)
 if e['status']=='input_refusal':
  assert s['answer']=='' and s['answer_hidden'] and not s['answer_open'];assert e['code'] in s['classification'];assert s['bytes']=='ファイル未作成' and s['hashes']=='hashなし' and s['ledger']=='台帳判定なし'
 else:
  assert json.loads(s['normal'])==r['normal'] and json.loads(s['faulty'])==r['faulty'];assert json.loads(s['ledger'])=={'errors':r['ledger_errors'],'trace':r['ledger_trace']}
  assert json.loads(s['bytes'])=={'original':r['original_ascii'],'copy_before':r['copy_before_ascii'],'copy_after':r['copy_after_ascii'],'changed_bytes':r['changed_bytes'],'original_unchanged':r['original_unchanged'],'temporary_cleanup':r['temporary_cleanup']}
  assert json.loads(s['hashes'])=={'original':r['original_sha256'],'copy_before':r['copy_before_sha256'],'copy_after':r['copy_after_sha256']}
  assert not s['answer_hidden'];assert '実evidenceID='+r['evidenceID'] in s['answer'];assert '原本='+json.dumps(r['original_ascii'],ensure_ascii=False,separators=(',',':')) in s['answer'];assert '複製後='+json.dumps(r['copy_after_ascii'],ensure_ascii=False,separators=(',',':')) in s['answer']
  assert r['original_sha256'] in s['answer'] and r['copy_after_sha256'] in s['answer'];assert '台帳errors='+json.dumps(r['ledger_errors'],ensure_ascii=False,separators=(',',':')) in s['answer'];assert '正常判定='+r['normal']['decision'] in s['answer'] and '故障判定='+r['faulty']['decision'] in s['answer'];assert '法的chain of custodyの証明ではありません' in s['answer'];assert r['temporary_cleanup'] and r['original_unchanged'] and not r['authenticity_proven'] and not r['legal_custody_proven']
 assert s['scroll_width']<=s['width']
def main():
 before=snapshot();ui=read(QA/'ui.json');table=read(ROOT/'expected-table.json')['rows'];byid={r['id']:r for r in table};binding={n:digest(ROOT/n) for n in SOURCES}
 assert ui['run_id']=='20261005T162158614954Z-custody' and ui['preview_id']=='20261005T162231652642Z-preview'
 assert len(ui['matrix'])==70 and {(e['id'],e['pred']) for e in ui['matrix']}=={(r['id'],p) for r in table for p in ['','match','mismatch','ledger','input']}
 for row in ui['matrix']:
  s=row['state'];e=byid[row['id']]['expected'];assert s['scenario']==row['id'] and s['prediction']==row['pred'] and s['initial_run']==ui['run_id'];state(s,e,binding)
  cat='input' if e['status']=='input_refusal' else 'ledger' if e['normal']['decision']=='ledger_refusal' else 'match' if e['integrity_match'] else 'mismatch'
  prefix='予想未選択。' if not row['pred'] else '予想と一致。' if row['pred']==cat else '予想と不一致。';assert s['message']==prefix+' 観測: '+cat
 assert len(ui['resets'])==19
 for e in ui['resets']:
  assert e['before']['answer_open'] and e['before']['trace_open'] and e['before']['answer'];empty(e['after'])
  if e['kind']=='scenario':assert e['after']['scenario']==e['new_value'] and e['after']['input']==byid[e['new_value']]['input_json'] and e['after']['prediction']==''
  else:assert e['after']['prediction']==e['new_value'] and e['after']['input']==e['before']['input']
 edited=read(QA/'edited-oracle-before-ui.json')['cases'];assert len(ui['edited'])==len(edited)==10
 for row,expected in zip(ui['edited'],edited):
  assert {k:row[k] for k in ['id','input_json','expected']}==expected;assert row['before']['answer_open'] and row['before']['trace_open'];empty(row['reset']);assert row['reset']['input']==row['input_json'];state(row['state'],row['expected'],binding)
 assert {e['kind'] for e in ui['stale']}=={'prediction','scenario','input'} and len(ui['stale'])==3
 for e in ui['stale']:
  delta=datetime.datetime.fromisoformat(e['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(e['started_utc'].replace('Z','+00:00'));assert delta.total_seconds()>=.6;empty(e['reset']);empty(e['after']);assert e['reset']['input']==e['after']['input'] and e['reset']['prediction']==e['after']['prediction']
 assert ui['host_before']['answer_open'] and ui['host_before']['trace_open'];empty(ui['host_after']);assert '実行/通信失敗' in ui['host_after']['message'] and ui['host_after']['input']==ui['host_before']['input']
 assert len(ui['captures'])==3
 for e in ui['captures']:
  p=QA/e['path'];assert p.read_bytes()[:2]==b'\xff\xd8' and p.stat().st_size>20000;state(e['state'],byid[e['state']['scenario']]['expected'],binding)
  if e['path'].startswith('mobile-'):assert e['state']['width']==390
 inputs={r['input_json']:r['expected'] for r in table};inputs.update({r['input_json']:r['expected'] for r in edited});requests=list((ROOT/'observations'/ui['preview_id']/'requests').glob('*.json'));assert len(requests)==119
 for p in requests:
  raw=read(p);run=raw['run'];r=run['result'];assert p.stem==raw['request_id'] and raw['source_digests']==binding;assert raw['input_json']==run['stdin'];core(r,inputs[raw['input_json']]);assert json.loads(run['stdout'])==r and not run['stderr'];assert run['exit']==(2 if r['status']=='input_refusal' else 0)
  if r['status']=='observed':
   assert r['temporary_cleanup'] and r['original_unchanged'];assert r['file_trace'][1]=='shutil.copyfile original.txt -> copy.txt'
   for text,h in [(r['original_ascii'],r['original_sha256']),(r['copy_before_ascii'],r['copy_before_sha256']),(r['copy_after_ascii'],r['copy_after_sha256'])]:assert hashlib.sha256(text.encode('ascii')).hexdigest()==h
  else:assert r['temporary_cleanup']=='not-created'
 d=ROOT/'observations'/ui['preview_id'];assert read(d/'server-start.json')['source_digests']==binding;assert read(d/'server-stop.json')=={'server_closed':True,'owned_tmp_created':False,'owned_tmp_remaining':False}
 assert ui['cleanup']['closed'] and ui['cleanup']['viewport_reset'] and ui['cleanup']['stopped'] and ui['cleanup']['each_observed_request_tmp_cleaned'];assert ui['cleanup']['owned_tab_ids']==['36','37','38']
 assert len(ui['navigation'])==2 and all('net::ERR_BLOCKED_BY_CLIENT' in n['status'] and n['not_bypassed'] for n in ui['navigation'])
 http=read(QA/'http-links.json');assert http['subject_filesystem_exists'] and all(r['status']==(404 if r['path'].startswith('subjects/') else 200) for r in http['rows'])
 for a in ui['links']:
  h=a['href']
  if h and not h.startswith('https://'):assert (ROOT/h).is_file()
 if (QA/'artifact-index.json').exists():
  idx=read(QA/'artifact-index.json');assert idx['excludes_self'];assert all(digest(QA/n)==h for n,h in idx['files'].items())
 assert before==snapshot();print(json.dumps({'ui_comparisons':70,'select_resets':19,'edited_actual':10,'delayed_stale':3,'captures':3,'bound_requests':len(requests),'all_observed_tmp_cleaned':True,'host_failure_empty':True,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
