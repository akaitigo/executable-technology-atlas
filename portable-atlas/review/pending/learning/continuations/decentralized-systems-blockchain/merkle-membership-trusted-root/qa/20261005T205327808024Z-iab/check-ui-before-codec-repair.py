"""Readonly validation of saved real UI, raw child receipts and geometry."""
import datetime,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect
QA=ROOT/'qa/20261005T205327808024Z-iab'
def load(p):return json.loads(p.read_text())
def near(a,b):assert abs(float(a)-b)<1e-8,(a,b)
def empty(s):
 assert all(s[k]=='' for k in ['classification','cards','stage','model','trace','run','answer'])
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[k] for k in ['answer_open','model_open','trace_open'])
 assert s['svg_count']==0 and not s['path_nodes'] and not s['path_lines'] and not s['roots'] and not s['table_rows']
def main():
 before=snapshot();u=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];edits=load(QA/'edited-oracle-before-ui.json')['cases']
 expected={a['input_json']:a['expected'] for a in rows+edits};fixed={a['id']:a for a in rows}
 requests=load(QA/'memory-receipts.json')['requests'];by={a['request_id']:a for a in requests}
 assert len(requests)==len(by)==107 and sum(a['revision']>=0 for a in requests)==105
 def actual(raw):
  p=raw['run'];out=p['result'];ex=expected[raw['input_json']]
  assert raw['mode']=='memory-only' and raw['input_json']==p['stdin'] and p['argv']==['python3','-B','calculate.py'] and p['stderr']=='' and json.loads(p['stdout'])==out and out['status']==ex['status']
  assert raw['raw_href']=='view/receipt/'+raw['request_id'] and raw['raw_json_href']=='receipts/'+raw['request_id']+'.json'
  assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES} and datetime.datetime.fromisoformat(raw['request_utc']).tzinfo
  if out['status']=='calculated':
   assert p['exit']==0;inspect(out,json.loads(raw['input_json']));assert all(out['summary'][k]==ex[k] for k in ['category','sender_match','trusted_match'])
   assert datetime.datetime.fromisoformat(out['started_utc'])<=datetime.datetime.fromisoformat(out['ended_utc'])
  else:assert p['exit']==2 and out=={'status':'input_refusal','code':ex['code'],'summary':None}
  return out
 for a in requests:actual(a)
 def display(s):
  raw=json.loads(s['trace']);assert raw==by[raw['request_id']] and s['input']==raw['input_json'] and s['raw']==raw['raw_href'];out=actual(raw)
  assert not s['results_hidden'] and s['initial_run']==u['run_id'];cat='input' if out['status']=='input_refusal' else out['summary']['category']
  assert s['run']=='request '+raw['request_id']+' · memory-only · exit'+str(raw['run']['exit'])
  assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
  if cat=='input':
   assert s['answer_hidden'] and not s['answer'] and out['code'] in s['classification'] and all(not s[k] for k in ['cards','stage','model','table_rows','roots','path_nodes','path_lines']) and s['svg_count']==0;return
  out=out['summary'];assert s['classification']=='有限位置membership · '+cat and not s['answer_hidden']
  model=json.loads(s['model']);assert model=={**{k:out[k] for k in ['leaf_preimage_hex','trace','trust_anchor_source','proved_index','value_uniqueness_claimed']},'context':raw['run']['result']['context']}
  assert s['cards']=='固定trusted root'+('一致' if out['trusted_match'] else '不一致')+'同送rootとの内部整合'+('一致' if out['sender_match'] else '不一致')+'故障: 同送rootを信頼'+('受理' if out['sender_match'] else '拒否')
  assert str(out['input']['index']) in s['stage'] and 'requestから採用せず' in s['stage']
  for phrase in ['固定trusted rootは置き換わりません','Aは位置0/2に重複','唯一の履歴を証明しません','教材独自形式']:assert phrase in s['answer']
  assert len(s['table_rows'])==2 and s['svg_count']==1 and len(s['path_nodes'])==5 and len(s['path_lines'])==4 and len(s['roots'])==3
  for j,t in enumerate(out['trace']):
   assert s['table_rows'][j]=={'level':str(j),'cells':[str(j),t['sibling_side'],t['left_hash'],t['right_hash'],t['parent_hash']]}
  nodes=s['path_nodes']
  for j,h in enumerate([out['leaf_hash'],out['trace'][0]['parent_hash'],out['trace'][1]['parent_hash']]):
   g=next(a for a in nodes if a['attributes'].get('data-current-level')==str(j));assert g['attributes']['data-hash']==h and len(g['rects'])==1
   rect=g['rects'][0];near(rect['x'],170);near(rect['y'],35+175*j);near(rect['width'],300);near(rect['height'],72);assert g['texts'][1]['text']==h[:20]+'…'
  for j,t in enumerate(out['trace']):
   g=next(a for a in nodes if a['attributes'].get('data-sibling-level')==str(j));assert g['attributes']['data-side']==t['sibling_side'] and g['attributes']['data-hash']==t['sibling_hash']
   rect=g['rects'][0];near(rect['x'],12 if t['sibling_side']=='left' else 484);near(rect['y'],121+175*j);near(rect['width'],144);near(rect['height'],62)
   assert g['texts'][0]['text']=='sibling '+t['sibling_side'] and g['texts'][1]['text']==t['sibling_hash'][:12]+'…'
   line,sib=s['path_lines'][2*j:2*j+2];near(line['x1'],320);near(line['x2'],320);near(line['y1'],107+175*j);near(line['y2'],210+175*j);near(sib['x1'],84 if t['sibling_side']=='left' else 556);near(sib['y1'],183+175*j);near(sib['x2'],320);near(sib['y2'],210+175*j)
  for a,(role,h,match) in zip(s['roots'],[('derived',out['derived_root'],True),('sender',out['sender_root'],out['sender_match']),('trusted',out['trusted_root'],out['trusted_match'])]):
   assert a['role']==role and a['hash']==h and a['match']==str(match).lower() and h in a['text']
 assert len(u['matrix'])==56 and {(a['id'],a['pred']) for a in u['matrix']}=={(a['id'],p) for a in rows for p in ['','trusted_match','root_mismatch','input']}
 for a in u['matrix']:assert a['state']['input']==fixed[a['id']]['input_json'] and a['state']['prediction']==a['pred'];display(a['state'])
 assert len(u['resets'])==18
 for a in u['resets']:
  display(a['before']);assert all(a['before'][k] for k in ['answer_open','model_open','trace_open']);empty(a['after'])
  if a['kind']=='prediction':assert a['after']['prediction']==a['value'] and a['after']['input']==a['before']['input']
  else:assert a['after']['scenario']==a['value'] and a['after']['prediction']=='' and a['after']['input']==fixed[a['value']]['input_json']
 assert len(u['edited'])==8
 for a,e in zip(u['edited'],edits):
  assert a['id']==e['id'] and a['expected']==e['expected'] and a['reset']['input']==e['input_json'];empty(a['reset']);display(a['state'])
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'])<datetime.datetime.fromisoformat(json.loads(a['state']['trace'])['request_utc'])
 reset=u['explicit_reset'];empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['normal-0']['input_json'] and reset['after']['prediction']==''
 one=u['one_operation'];display(one['before']);display(one['after']);pre=json.loads(one['before']['trace'])['run']['result']['summary'];post=json.loads(one['after']['trace'])['run']['result']['summary']
 assert pre['trusted_match'] and post['sender_match'] and not post['trusted_match'] and pre['trusted_root']==post['trusted_root'] and post['input']==json.loads(fixed['rebuilt-sender-tree']['input_json'])
 assert len(u['stale'])==4 and {a['kind'] for a in u['stale']}=={'prediction','scenario','input','reset'}
 for a in u['stale']:empty(a['reset']);empty(a['after']);assert a['reset']==a['after'] and a['elapsed_ms']>=600 and '計算中' in a['pending']['message'] and a['pending']['compare_disabled']
 display(u['host_before']);empty(u['host_after']);assert '実行/通信失敗' in u['host_after']['message']
 assert len(u['captures'])==3
 for a in u['captures']:
  display(a['state']);assert (QA/a['file']).read_bytes()[:8]==b'\x89PNG\r\n\x1a\n' and a['state']['scroll_width']<=a['state']['width']
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-merkle-membership-trusted-root/SKILL.md','view/parent-readme':ROOT/'../../../subjects/decentralized-systems-blockchain/README.md'}
 assert len(u['local_navigation'])==9
 for a in u['local_navigation']:
  assert a['shown']['scroll_width']<=a['shown']['width'];body=a['shown']['body']
  if a['href'] in mapping:assert body==mapping[a['href']].read_text()
  elif a['href']=='view/fixed-raw':assert json.loads(body)==load(ROOT/'observations'/u['run_id']/'raw.json')
  else:assert json.loads(body)==json.loads(u['link_raw_before']['trace'])==by[a['href'].rsplit('/',1)[1]]
 assert any('NIST IR 8202' in h for h in u['primary_navigation']['headings'])
 http=load(QA/'http-links.json');assert http['ui_post_count']==105 and http['total']==107 and http['unit_sha_mtime_unchanged_during_GET_POST_export']
 assert all(a['status']==(404 if a['path']=='view/not-listed' else 200) for a in http['rows']) and http['parent_reference_sha256']==digest(mapping['view/parent-readme'])
 setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged']
 for a in setup['requests']:assert a==by[a['request_id']] and a['revision']<0
 c=load(QA/'cleanup.json');assert not c['ports_after']['53381'] and not c['ports_after']['52508'] and all(c['ports_after'][str(p)] for p in [53478,60285,50835]) and c['server_closed'] and c['files_recorded_by_server']==0 and c['memory_receipts_discarded']==107 and c['owned_tab_closed']=='31' and c['viewport_reset']
 prior=load(ROOT/'qa/oracle-before-producer.json')
 for n,h in prior['files'].items():assert digest(ROOT/n)==h
 skill=ROOT/'skills/atlas-merkle-membership-trusted-root/SKILL.md'
 for target in re.findall(r'\]\(([^)]+)\)',skill.read_text()):assert (skill.parent/target).resolve().is_file()
 assert (ROOT/'qa/20261005T204654347912Z-iab/export-failure.json').is_file()
 assert before==snapshot()
 print(json.dumps({'matrix':56,'select_resets':18,'edited':8,'stale':4,'captures':3,'actual_viewers':9,'UI_POST':105,'saved_receipts':107,'source_and_geometry_matched':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
