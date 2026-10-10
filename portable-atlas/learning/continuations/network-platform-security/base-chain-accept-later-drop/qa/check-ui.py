import datetime,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runner import ROOT,SOURCES,digest,snapshot
QA=ROOT/'qa/20261005T155837568171Z-iab'
def read(p):return json.loads(p.read_text())
def empty(s):
 assert all(s[k]=='' for k in ['answer','normal','faulty','packet','trace','run','classification']),s
 assert s['answer_hidden'] and not s['answer_open'] and not s['trace_open'] and s['results_hidden'] and s['raw'] is None
def state(s,expected,binding):
 raw=read(ROOT/s['raw']);run=raw['run'];assert run==json.loads(s['trace']);assert run['stdin']==s['input']==raw['input_json']
 assert run['result']==expected and json.loads(run['stdout'])==expected and not run['stderr'];assert raw['source_digests']==binding
 assert raw['request_id'] in s['run'];assert run['exit']==(2 if expected['status']=='input_refusal' else 0)
 if expected['status']=='input_refusal':
  assert s['answer']=='' and s['answer_hidden'] and not s['answer_open'];assert expected['code'] in s['classification'];assert s['normal']=='判定なし' and s['faulty']=='判定なし'
 else:
  n,f=expected['normal'],expected['faulty'];p=expected['packet']
  assert json.loads(s['normal'])==n and json.loads(s['faulty'])==f and json.loads(s['packet'])==p
  assert not s['answer_hidden'] and f"{p['source']} {p['protocol']}/{p['dport']}" in s['answer']
  assert '正常版はservice chain' in s['answer'] and '最終'+n['final'] in s['answer'] and '故障版は最終'+f['final'] in s['answer']
  assert ' / '.join(n['trace']) in s['answer'] and ' / '.join(f['trace']) in s['answer']
  assert '実packetの配送・firewall安全性は未検証' in s['answer']
 assert s['scroll_width']<=s['width']
def main():
 before=snapshot();ui=read(QA/'ui.json');table=read(ROOT/'expected-table.json')['rows'];byid={r['id']:r for r in table};binding={n:digest(ROOT/n) for n in SOURCES}
 assert ui['run_id']=='20261005T155810989767Z-chain';assert ui['preview_id']=='20261005T155837568171Z-preview'
 assert len(ui['matrix'])==90 and {(e['id'],e['pred']) for e in ui['matrix']}=={(r['id'],p) for r in table for p in ['','mismatch','accept','drop','input']}
 for e in ui['matrix']:
  expected=byid[e['id']]['expected'];s=e['state'];assert s['scenario']==e['id'] and s['prediction']==e['pred'] and s['initial_run']==ui['run_id'];state(s,expected,binding)
  category='input' if expected['status']=='input_refusal' else 'mismatch' if expected['normal']['final']!=expected['faulty']['final'] else expected['normal']['final']
  prefix='予想未選択。' if not e['pred'] else '予想と一致。' if e['pred']==category else '予想と不一致。';assert s['message']==prefix+' 観測: '+category
 assert len(ui['resets'])==23
 for e in ui['resets']:
  assert e['before']['answer_open'] and e['before']['trace_open'] and e['before']['answer'];empty(e['after'])
  if e['kind']=='scenario':assert e['after']['scenario']==e['new_value'] and e['after']['input']==byid[e['new_value']]['input_json'] and e['after']['prediction']==''
  else:assert e['after']['prediction']==e['new_value'] and e['after']['input']==e['before']['input']
 assert len(ui['edited'])==8
 for e in ui['edited']:
  assert e['before']['answer_open'] and e['before']['trace_open'];empty(e['reset']);assert e['reset']['input']==e['input_json'];state(e['state'],e['expected'],binding)
 timed=[e for e in ui['stale'] if 'checked_utc' in e];assert {e['kind'] for e in timed}=={'prediction','scenario','input'} and len(timed)==3
 for e in timed:
  assert (datetime.datetime.fromisoformat(e['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(e['started_utc'].replace('Z','+00:00'))).total_seconds()>=.6
  empty(e['reset']);empty(e['after']);assert e['after']['input']==e['reset']['input'] and e['after']['prediction']==e['reset']['prediction']
 assert ui['host_before']['answer_open'] and ui['host_before']['trace_open'];empty(ui['host_after']);assert '実行/通信失敗' in ui['host_after']['message'];assert ui['host_after']['input']==ui['host_before']['input']
 assert len(ui['captures'])==3
 for e in ui['captures']:
  p=QA/e['path'];assert p.read_bytes()[:2]==b'\xff\xd8' and p.stat().st_size>20000;state(e['state'],byid[e['state']['scenario']]['expected'],binding)
  if e['path'].startswith('mobile-'):assert e['state']['width']==390
 expected_inputs={r['input_json']:r['expected'] for r in table};expected_inputs.update({e['input_json']:e['expected'] for e in ui['edited']})
 requests=list((ROOT/'observations'/ui['preview_id']/'requests').glob('*.json'));assert len(requests)>=140
 for p in requests:
  raw=read(p);run=raw['run'];assert p.stem==raw['request_id'];assert raw['source_digests']==binding
  assert raw['input_json']==run['stdin'];expected=expected_inputs[raw['input_json']];assert run['result']==json.loads(run['stdout'])==expected and not run['stderr'];assert run['exit']==(2 if expected['status']=='input_refusal' else 0)
 for rid in [ui['preview_id'],'20261005T160713257255Z-preview']:
  d=ROOT/'observations'/rid;assert read(d/'server-start.json')['source_digests']==binding;assert read(d/'server-stop.json')=={'server_closed':True,'owned_tmp_created':False,'owned_tmp_remaining':False}
 cleanup=ui['cleanup'];assert cleanup['closed'] and cleanup['viewport_reset'] and cleanup['stopped'] and not cleanup['owned_tmp_created'];assert cleanup['owned_tab_ids']==['33','34','35']
 assert ui['raw_navigation']['status']=='net::ERR_BLOCKED_BY_CLIENT' and ui['raw_navigation']['not_bypassed'];assert 'net::ERR_BLOCKED_BY_CLIENT' in ui['markdown_navigation']['status'] and ui['markdown_navigation']['not_bypassed']
 links=read(QA/'http-links.json');assert links['subject_filesystem_exists'];assert all(e['status']==(404 if e['path'].startswith('subjects/') else 200) for e in links['rows'])
 for e in ui['links']:
  h=e['href']
  if h and not h.startswith('https://'):assert (ROOT/h).is_file(),h
 index=QA/'artifact-index.json'
 if index.exists():
  idx=read(index);assert idx['excludes_self'];assert all(digest(QA/n)==h for n,h in idx['files'].items())
 assert before==snapshot(),'QA checker wrote files';print(json.dumps({'ui_comparisons':90,'resets':23,'edited':8,'delayed_stale':3,'captures':3,'requests_bound':len(requests),'host_failure_empty':True,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
