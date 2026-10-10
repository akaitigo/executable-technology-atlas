"""Readonly pairwise/moment verification of actual IAB, receipts and SVG geometry."""
import datetime,json,re,sys
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T185652838288Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','stage','table','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert all(p['svg_count']==0 and not p['text'] and not p['cells'] and not p['controls'] for p in s['plots'])
def opened(s):assert all(s[n] for n in ['answer_open','model_open','trace_open'])
def actual(raw,o):
 assert raw['mode']=='memory-only' and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
 run=raw['run'];r=run['result'];assert raw['input_json']==run['stdin'] and json.loads(run['stdout'])==r and run['stderr']=='' and r['status']==o['status']
 assert datetime.datetime.fromisoformat(raw['request_utc']).tzinfo is not None and run['argv']==['python3','-B','calculate.py']
 assert raw['raw_href']=='view/receipt/'+raw['request_id'] and raw['raw_json_href']=='receipts/'+raw['request_id']+'.json'
 if r['status']=='calculated':
  assert run['exit']==0;inspect(r,json.loads(raw['input_json']));s=r['summary'];assert s['category']==o['category']
  assert datetime.datetime.fromisoformat(r['started_utc'])<=datetime.datetime.fromisoformat(r['ended_utc'])
  if 'hand_case' in o:handcheck(r,o['hand_case'])
  for n in ['winner','selection_loss','confirmation_loss']:
   if n in o:assert s[n]==o[n],n
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None}
 return r
def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o)
 assert s['initial_run']=='20261005T185637934495Z-robust' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category']
 assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','stage','table','model']) and o['code'] in s['classification']
  assert all(p['svg_count']==0 and not p['text'] for p in s['plots']);return
 out=r['summary'];assert s['classification']=='合成fixture比較 · '+cat and not s['answer_hidden']
 assert json.loads(s['model'])=={**{n:out[n] for n in ['selection','confirmation','noise_weights','loss_definition','units','sequence']},'context':r['context']}
 assert s['cards']=='選択固定setting'+(out['winner'] or 'tie / 未選択')+'選択loss'+out['selection_loss']+' arb²別fixture確認loss'+('未実行' if out['confirmation_loss'] is None else out['confirmation_loss']+' arb²')
 assert 'setting '+(out['winner'] or 'なし')+' 固定' in s['stage'] and '確認でsettingを再選択しません' in s['stage']
 for text in ['選択loss='+out['selection_loss'],'別fixture確認loss='+('未実行' if out['confirmation_loss'] is None else out['confirmation_loss']),'分母6','分母5','確認データで再選択せず','統計独立性・実物noise耐性・無作為化・実因果/有意性は未実証','SN比・直交表・tolerance designは未教材']:assert text in s['answer']
 table=''
 for phase in ['selection','confirmation']:
  f=out[phase];p=next(p for p in s['plots'] if p['phase']==phase)
  if f is None:assert p['svg_count']==0 and '確認未実行' in p['text'] and not p['cells'];continue
  for control,m in f['settings'].items():table+=phase+' / '+control+''.join(m[n] for n in ['mean','variance_N','sample_variance_Nminus1','loss','noise_difference'])
  vals=[10]+[v for c in f['cells'] for v in c['observations']];lo=min(vals)-2;hi=max(vals)+2
  def y(v):return 270-(float(F(v))-lo)/(hi-lo)*235
  assert p['svg_count']==1 and p['fixture']==f['fixture_id'] and len(p['cells'])==4 and len(p['controls'])==2;near(p['lo'],lo);near(p['hi'],hi);assert p['target']['value']=='10';near(p['target']['y'],y(10))
  for index,g in enumerate(p['controls']):
   control='C'+str(index);cells=f['cells'][2*index:2*index+2];assert g['control']==control and g['chosen']==str(control==out['winner']).lower() and len(g['line'])==1;line=g['line'][0]
   assert line['means']==','.join(c['mean'] for c in cells) and ('chosen' in line['classes'].split())==(control==out['winner'])
   near(line['x1'],95);near(line['x2'],365);near(line['y1'],y(cells[0]['mean']));near(line['y2'],y(cells[1]['mean']))
  for index,g in enumerate(p['cells']):
   c=f['cells'][index];assert g['cell']==c['control']+('N-' if c['noise']==-1 else 'N+') and g['mean']==c['mean'];x=95 if c['noise']==-1 else 365
   pts=[pt for pt in g['circles'] if pt['role'] is None];means=[pt for pt in g['circles'] if pt['role']=='mean'];assert len(pts)==3 and len(means)==1;near(means[0]['cx'],x);near(means[0]['cy'],y(c['mean']))
   for j,pt in enumerate(pts):assert pt['replicate']==str(j) and pt['response']==str(c['observations'][j]);near(pt['cx'],x+(j-1)*8);near(pt['cy'],y(c['observations'][j]))
 assert s['table']==table
def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json')
 assert export['mode']=='memory-only' and len(export['requests'])==109;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==109
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(r['revision']>=0 for r in export['requests'])==107
 assert len(e['matrix'])==60 and {(x['id'],x.get('prediction',x.get('pred'))) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','pass','fail','tie','input']}
 for x in e['matrix']:assert x['state']['prediction']==x.get('prediction',x.get('pred')) and x['state']['input']==fixed[x['id']]['input_json'];display(x['state'],fixed[x['id']]['expected'],by_id)
 assert len(e['resets'])==17
 for x in e['resets']:
  opened(x['before']);display(x['before'],fixed['pass']['expected'],by_id);empty(x['after'])
  if x['kind']=='prediction':assert x['after']['prediction']==x['value'] and x['after']['input']==x['before']['input']
  else:assert x['after']['scenario']==x['value'] and x['after']['prediction']=='' and x['after']['input']==fixed[x['value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['pass']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']=='edited'
 assert len(e['edited'])==8
 for x,o in zip(e['edited'],edits):
  assert x['id']==o['id'] and x['expected']==o['expected'];opened(x['before']);empty(x['reset']);assert x['reset']['input']==o['input_json'];display(x['state'],o['expected'],by_id)
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(json.loads(x['state']['trace'])['request_utc'])
 assert len(e['stale'])==4 and {x['kind'] for x in e['stale']}=={'prediction','scenario','input','reset'}
 for x in e['stale']:opened(x['before']);empty(x['reset']);empty(x['after']);assert x['reset']==x['after'] and x['elapsed_ms']>=600 and '計算中' in x['pending']['message']
 opened(e['host_before']);display(e['host_before'],fixed['pass']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for x in e['captures']:
  b=(QA/x['file']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(x['state'],oracle[x['state']['input']],by_id);assert x['state']['scroll_width']<=x['state']['width']
  if x['file'].startswith('mobile'):assert x['state']['width']==390
 assert len(e['qa_attempts'])==1;empty(e['qa_attempts'][0]['state'])
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-control-noise-robustness-confirmation/SKILL.md','view/qe-coverage':ROOT/'../../../quality-engineering-atlas/COVERAGE.md'}
 assert len(e['local_navigation'])==9
 for x in e['local_navigation']:
  shown=x['shown'];assert shown['body'] and shown['scroll_width']<=shown['width']
  if x['href'] in mapping:assert shown['body']==mapping[x['href']].read_text()
  elif x['href']=='view/fixed-raw':assert json.loads(shown['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:raw=json.loads(e['link_raw_before']['trace']);assert json.loads(shown['body'])==raw==by_id[raw['request_id']]
 assert e['primary_navigation']['headings']==['5.5.6.','What are Taguchi designs?'] and e['primary_navigation']['url']=='https://www.itl.nist.gov/div898/handbook/pri/section5/pri56.htm'
 http=load(QA/'http-links.json');assert http['unit_sha_mtime_unchanged_during_export'] and http['ui_post_count']==107 and http['health']['mode']=='memory-only' and http['health']['request_count']==109
 for x in http['rows']:assert x['status']==(404 if x['path']=='view/not-listed' else 200)
 assert digest(mapping['view/qe-coverage'])==http['parent_reference_sha256'];setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged'] and all(r['status']==200 for r in setup['get_rows'])
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False
 for name,sha in prior['files'].items():assert digest(ROOT/name)==sha
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['57718'] and all(cleanup['ports_after'][n] for n in ['53478','60285','50835'])
 assert cleanup['server_closed'] and cleanup['memory_receipts_discarded']==109 and cleanup['files_recorded_by_server']==0 and cleanup['owned_tab_closed']=='51' and cleanup['viewport_reset'] and cleanup['protected_ports_untouched']
 assert e['cleanup']['owned_server_stopped'] and e['viewport_reset'];session=load(QA/'server-session.json');assert session['mode']=='memory-only' and session['record_only'] is False
 assert load(QA/'toolchain.json')['installed']==False
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-control-noise-robustness-confirmation/SKILL.md').read_text()):assert (ROOT/'skills/atlas-control-noise-robustness-confirmation'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha,n
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':60,'select_resets':17,'explicit_reset':True,'edited':8,'stale':4,'UI_POST':107,'total_memory_receipts':109,'captures':3,'clicked_local_viewers':9,'NIST_clicked':True,'pairwise_moment_oracle':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
