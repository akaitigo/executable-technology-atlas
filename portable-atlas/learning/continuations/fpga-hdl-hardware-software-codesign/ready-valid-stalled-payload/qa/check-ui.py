import datetime,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runner import ROOT,SOURCES,digest,snapshot
from oracle import expected
QA=ROOT/'qa/20261005T164323129181Z-iab';MODES=['normal','advance_on_stall','ignore_ready']
def read(p):return json.loads(p.read_text())
def empty(s):
 assert all(s[k]=='' for k in ['answer','normal','advance','ignore','step','ticks','wave','trace','run','classification'])
 assert s['answer_hidden'] and not s['answer_open'] and not s['trace_open'] and s['results_hidden'] and s['raw'] is None and s['next_disabled']
def state(s,e,binding):
 raw=read(ROOT/s['raw']);run=raw['run'];r=run['result'];assert run==json.loads(s['trace']);assert raw['input_json']==run['stdin']==s['input'];assert r==e==json.loads(run['stdout']);assert run['exit']==(2 if e['status']=='input_refusal' else 0) and not run['stderr'];assert raw['source_digests']==binding and raw['request_id'] in s['run']
 if r['status']=='input_refusal':assert s['answer']=='' and s['answer_hidden'] and not s['answer_open'] and s['wave']=='' and s['ticks']=='' and s['next_disabled'] and r['code'] in s['classification']
 else:
  assert r==expected(r['input']);assert json.loads(s['normal'])==r['normal']['captured'] and json.loads(s['advance'])==r['advance_on_stall']['captured'] and json.loads(s['ignore'])==r['ignore_ready']['captured']
  assert not s['answer_hidden'];assert 'data='+str(r['input']['data']) in s['answer'] and 'valid='+str(r['input']['valid']) in s['answer'] and 'ready='+json.dumps(r['input']['ready'],separators=(',',':')) in s['answer']
  for label,m in [('正常捕捉=','normal'),('advance-on-stall=','advance_on_stall'),('ready無視=','ignore_ready')]:assert label+json.dumps(r[m]['captured'],separators=(',',':')) in s['answer']
  assert 'RTL/FPGA/timing/CDC/実deviceの成功ではありません' in s['answer']
  cursor=int(s['step'].split(' / ')[0]);n=len(r['input']['ready']);assert s['step']==str(cursor)+' / '+str(n)+' edge';assert json.loads(s['ticks'])=={m:r[m]['ticks'][:cursor] for m in MODES};assert s['next_disabled']==(cursor==n)
  svg=ET.fromstring(s['wave']);paths=[e for e in svg.iter() if e.tag.split('}')[-1]=='path'];assert len(paths)==(6 if cursor else 0)
  for m in MODES:
   assert m in s['wave_text']
   for t in r[m]['ticks'][:cursor]:assert str(t['data'])+' / '+('YES' if t['capture'] else '-') in s['wave_text']
 assert s['scroll_width']<=s['width']
def main():
 before=snapshot();ui=read(QA/'ui.json');table=read(ROOT/'expected-table.json')['rows'];byid={r['id']:r for r in table};binding={n:digest(ROOT/n) for n in SOURCES};assert ui['run_id']=='20261005T164312950518Z-ready' and ui['preview_id']=='20261005T164323129181Z-preview'
 assert len(ui['matrix'])==75 and {(x['id'],x['pred']) for x in ui['matrix']}=={(r['id'],p) for r in table for p in ['','payload','duplicate','agree','input']}
 for x in ui['matrix']:
  s=x['state'];e=byid[x['id']]['expected'];assert s['scenario']==x['id'] and s['prediction']==x['pred'] and s['initial_run']==ui['run_id'];state(s,e,binding)
  cat='input' if e['status']=='input_refusal' else 'payload' if e['normal']['captured']!=e['advance_on_stall']['captured'] else 'duplicate' if e['normal']['captured']!=e['ignore_ready']['captured'] else 'agree';prefix='予想未選択。' if not x['pred'] else '予想と一致。' if x['pred']==cat else '予想と不一致。';assert s['message']==prefix+' 観測: '+cat
 assert len(ui['resets'])==20
 for x in ui['resets']:
  assert x['before']['answer_open'] and x['before']['trace_open'] and x['before']['step']=='1 / 3 edge';empty(x['after'])
  if x['kind']=='scenario':assert x['after']['scenario']==x['new_value'] and x['after']['input']==byid[x['new_value']]['input_json'] and x['after']['prediction']==''
  else:assert x['after']['prediction']==x['new_value'] and x['after']['input']==x['before']['input']
 assert len(ui['steps'])==4
 for x in ui['steps']:assert x['cursor']==int(x['state']['step'][0]);state(x['state'],byid['stall17']['expected'],binding)
 edits=read(QA/'edited-oracle-before-ui.json')['cases'];assert len(edits)==len(ui['edited'])==10
 for x,e in zip(ui['edited'],edits):
  assert {k:x[k] for k in ['id','input_json','expected']}==e;assert x['before']['answer_open'] and x['before']['trace_open'];empty(x['reset']);assert x['reset']['input']==x['input_json'];state(x['state'],x['expected'],binding)
 assert len(ui['stale'])==3 and {x['kind'] for x in ui['stale']}=={'prediction','scenario','input'}
 for x in ui['stale']:
  delta=datetime.datetime.fromisoformat(x['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['started_utc'].replace('Z','+00:00'));assert delta.total_seconds()>=.6;empty(x['reset']);empty(x['after']);assert x['after']['input']==x['reset']['input'] and x['after']['prediction']==x['reset']['prediction']
 assert ui['host_before']['answer_open'] and ui['host_before']['trace_open'];empty(ui['host_after']);assert '実行/通信失敗' in ui['host_after']['message'] and ui['host_after']['input']==ui['host_before']['input']
 assert len(ui['captures'])==3
 for x in ui['captures']:
  p=QA/x['path'];assert p.read_bytes()[:2]==b'\xff\xd8' and p.stat().st_size>20000;state(x['state'],byid[x['state']['scenario']]['expected'],binding)
  if x['path'].startswith('mobile-'):assert x['state']['width']==390
 inputs={r['input_json']:r['expected'] for r in table};inputs.update({r['input_json']:r['expected'] for r in edits});requests=list((ROOT/'observations'/ui['preview_id']/'requests').glob('*.json'));assert len(requests)==125
 for p in requests:
  raw=read(p);run=raw['run'];r=run['result'];assert p.stem==raw['request_id'] and raw['source_digests']==binding;assert raw['input_json']==run['stdin'];assert r==inputs[raw['input_json']]==json.loads(run['stdout']) and not run['stderr'];assert run['exit']==(2 if r['status']=='input_refusal' else 0)
  if r['status']=='observed':assert expected(r['input'])==r
 d=ROOT/'observations'/ui['preview_id'];assert read(d/'server-start.json')['source_digests']==binding;assert read(d/'server-stop.json')=={'server_closed':True,'owned_tmp_created':False,'owned_tmp_remaining':False};assert ui['cleanup']['owned_tabs_closed']==['39','40','41'] and ui['cleanup']['stopped'] and ui['cleanup']['viewport_reset'] and not ui['cleanup']['owned_model_tmp_created']
 assert all('net::ERR_BLOCKED_BY_CLIENT' in x['status'] and x['not_bypassed'] for x in ui['navigation']);http=read(QA/'http-links.json');assert http['subject_filesystem_exists'] and all(x['status']==(404 if x['path'].startswith('subjects/') else 200) for x in http['rows'])
 for a in ui['links']:
  h=a['href']
  if h and not h.startswith('https://'):assert (ROOT/h).is_file()
 inv=read(ROOT/'qa/tool-inventory.json');assert inv['PATH_inventory']=={'iverilog':None,'verilator':None,'ghdl':None} and not inv['install_attempted'] and not inv['RTL_run']
 if (QA/'artifact-index.json').exists():
  idx=read(QA/'artifact-index.json');assert idx['excludes_self'];assert all(digest(QA/n)==h for n,h in idx['files'].items())
 assert before==snapshot();print(json.dumps({'ui_comparisons':75,'select_resets':20,'edited_actual':10,'step_prefixes':4,'delayed_stale':3,'captures':3,'bound_requests':len(requests),'host_failure_empty':True,'read_only':True}));return 0
if __name__=='__main__':sys.exit(main())
