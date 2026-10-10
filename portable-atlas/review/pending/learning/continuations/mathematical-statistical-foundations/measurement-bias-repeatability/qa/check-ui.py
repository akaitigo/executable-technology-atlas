"""Readonly independent pairwise/moment and actual SVG/source/memory receipt checks."""
import datetime,json,re,sys
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T193024585259Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','stage','table','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert all(p['svg_count']==0 and not p['text'] and not p['cells'] and not p['bars'] for p in s['plots'])
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
  for key,field in [('bias','bias'),('variance','sample_variance')]:
   if key in o:assert [p[field] for p in s['cells']]==o[key]
  if 'within' in o:assert s['within_sample_variance']==o['within']
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None}
 return r
def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o)
 assert s['initial_run']=='20261005T193008141522Z-msa' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category']
 assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','stage','table','model']) and o['code'] in s['classification'] and not s['table_rows'];assert all(p['svg_count']==0 and not p['text'] for p in s['plots']);return
 out=r['summary'];assert s['classification']=='有限bias/分散分類 · '+cat and not s['answer_hidden']
 assert json.loads(s['model'])=={**{n:out[n] for n in ['cells','within_SSE','within_df','between_cell_SSE','all_values_SSE','rule','pooling','units']},'context':r['context']}
 assert s['cards']=='最大|cell bias|'+out['max_abs_cell_bias']+' arbwithin SSE/df8'+out['within_sample_variance']+' arb²故障: 全測定s²'+out['naive_all_values_sample_variance']+' arb²'
 assert '全符号bias='+out['aggregate_signed_bias'] in s['stage'] and ' / '.join(out['fixed_operator_differences'])+' arb' in s['stage'] and 'operator母集団再現性・製品工程変動は推定しません' in s['stage']
 for text in ['最大|cell bias|='+out['max_abs_cell_bias'],'within SSE/df8='+out['within_sample_variance'],'故障s²='+out['naive_all_values_sample_variance'],'sample s²=SSE/2','参照MSE=bias²+SSE/3','真値保証なし','固定operator差は母集団再現性ではなく','完全Gage R&R分散成分・実instrument・校正traceability・不確かさbudget・統計独立・無作為化・等precisionは未実証']:assert text in s['answer']
 assert len(s['table_rows'])==4
 for c,row in zip(out['cells'],s['table_rows']):assert row['cell']==c['id'] and row['cells']==list(map(str,[c['id'],c['reference'],c['mean'],c['bias'],c['sample_variance'],c['SSE']+'/'+str(c['df']),c['reference_MSE'],'外' if c['bias_flag'] else '内','外' if c['spread_flag'] else '内']))
 measurement=next(p for p in s['plots'] if p['kind']=='measurement');variance=next(p for p in s['plots'] if p['kind']=='variance');assert measurement['svg_count']==variance['svg_count']==1 and not measurement['bars'] and not variance['cells']
 vals=[10,20]+[v for c in out['cells'] for v in c['observations']];lo=min(vals)-2;hi=max(vals)+2;near(measurement['lo'],lo);near(measurement['hi'],hi)
 def y(v):return 270-(float(F(v))-lo)/(hi-lo)*235
 assert len(measurement['cells'])==4
 for i,(g,c) in enumerate(zip(measurement['cells'],out['cells'])):
  x=75+130*i;assert g['cell']==c['id'] and g['mean']==c['mean'] and g['bias']==c['bias'] and g['reference']==str(c['reference']) and len(g['lines'])==2;lines={p['role']:p for p in g['lines']};ref=lines['reference'];bias=lines['bias'];near(ref['x1'],x-36);near(ref['x2'],x+36);near(ref['y1'],y(c['reference']));near(ref['y2'],y(c['reference']));near(bias['x1'],x+20);near(bias['x2'],x+20);near(bias['y1'],y(c['reference']));near(bias['y2'],y(c['mean']));assert ref['classes']=='reference-line' and bias['classes']=='bias-line'
  pts=[p for p in g['points'] if p['role'] is None];means=[p for p in g['points'] if p['role']=='mean'];assert len(pts)==3 and len(means)==1;near(means[0]['cx'],x);near(means[0]['cy'],y(c['mean']))
  for j,p in enumerate(pts):assert p['replicate']==str(j) and p['response']==str(c['observations'][j]);near(p['cx'],x+(j-1)*8);near(p['cy'],y(c['observations'][j]))
 bars=[(c['id'],c['sample_variance']) for c in out['cells']]+[('within',out['within_sample_variance']),('naive',out['naive_all_values_sample_variance'])];vhi=max([2]+[float(F(v)) for _,v in bars])*1.1;near(variance['hi'],vhi);assert len(variance['bars'])==6
 for i,(bar,(key,value)) in enumerate(zip(variance['bars'],bars)):
  x=70+95*i;ybar=270-float(F(value))/vhi*235;assert bar['key']==key and bar['value']==value and len(bar['rect'])==1 and len(bar['texts'])==2;rect=bar['rect'][0];near(rect['x'],x-24);near(rect['y'],ybar);near(rect['width'],48);near(rect['height'],270-ybar);assert rect['classes']==('naive-bar' if key=='naive' else 'within-bar');assert bar['texts'][0]['text']==value and bar['texts'][1]['text']==key;near(bar['texts'][0]['x'],x);near(bar['texts'][0]['y'],ybar-7)
def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json');assert export['mode']=='memory-only' and len(export['requests'])==123;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==123
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(r['revision']>=0 for r in export['requests'])==121
 assert len(e['matrix'])==72 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','within','bias','spread','both','input']}
 for p in e['matrix']:assert p['state']['prediction']==p['pred'] and p['state']['input']==fixed[p['id']]['input_json'];display(p['state'],fixed[p['id']]['expected'],by_id)
 assert len(e['resets'])==18
 for p in e['resets']:
  opened(p['before']);display(p['before'],fixed['centered']['expected'],by_id);empty(p['after'])
  if p['kind']=='prediction':assert p['after']['prediction']==p['value'] and p['after']['input']==p['before']['input']
  else:assert p['after']['scenario']==p['value'] and p['after']['prediction']=='' and p['after']['input']==fixed[p['value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['centered']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']=='edited'
 assert len(e['edited'])==8
 for p,o in zip(e['edited'],edits):
  assert p['id']==o['id'] and p['expected']==o['expected'];opened(p['before']);empty(p['reset']);assert p['reset']['input']==o['input_json'];display(p['state'],o['expected'],by_id)
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(json.loads(p['state']['trace'])['request_utc'])
 one=e['one_operation'];display(one['before'],fixed['centered']['expected'],by_id);empty(one['reset']);display(one['after'],edits[4]['expected'],by_id);assert one['before']['input']==fixed['centered']['input_json'] and one['after']['input']==edits[4]['input_json'];pre=json.loads(one['before']['trace'])['run']['result']['summary'];post=json.loads(one['after']['trace'])['run']['result']['summary'];assert pre['within_sample_variance']==post['within_sample_variance']=='1' and pre['max_abs_cell_bias']=='0' and post['max_abs_cell_bias']=='2' and pre['naive_all_values_sample_variance']==post['naive_all_values_sample_variance']
 assert len(e['stale'])==4 and {p['kind'] for p in e['stale']}=={'prediction','scenario','input','reset'}
 for p in e['stale']:opened(p['before']);empty(p['reset']);empty(p['after']);assert p['reset']==p['after'] and p['elapsed_ms']>=600 and '計算中' in p['pending']['message'] and p['pending']['compare_disabled']
 opened(e['host_before']);display(e['host_before'],fixed['centered']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for p in e['captures']:
  b=(QA/p['file']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(p['state'],oracle[p['state']['input']],by_id);assert p['state']['scroll_width']<=p['state']['width']
  if p['file'].startswith('mobile'):assert p['state']['width']==390
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-measurement-bias-repeatability/SKILL.md','view/qe-coverage':ROOT/'../../../quality-engineering-atlas/COVERAGE.md'};assert len(e['local_navigation'])==9
 for p in e['local_navigation']:
  shown=p['shown'];assert shown['body'] and shown['scroll_width']<=shown['width']
  if p['href'] in mapping:assert shown['body']==mapping[p['href']].read_text()
  elif p['href']=='view/fixed-raw':assert json.loads(shown['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:raw=json.loads(e['link_raw_before']['trace']);assert json.loads(shown['body'])==raw==by_id[raw['request_id']]
 assert e['primary_navigation']['headings']==['2.4.4.1.','Analysis of repeatability'] and e['primary_navigation']['url']=='https://www.itl.nist.gov/div898/handbook/mpc/section4/mpc441.htm'
 http=load(QA/'http-links.json');assert http['unit_sha_mtime_unchanged_during_export'] and http['ui_post_count']==121 and http['health']['mode']=='memory-only' and http['health']['request_count']==123
 for p in http['rows']:assert p['status']==(404 if p['path']=='view/not-listed' else 200)
 assert digest(mapping['view/qe-coverage'])==http['parent_reference_sha256'];setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged'] and all(p['status']==200 for p in setup['get_rows'])
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False
 for n,sha in prior['files'].items():assert digest(ROOT/n)==sha
 # Exhaust finite difference range: integer three-repeat sample variance 2 is unreachable.
 assert not any(u*u+v*v-u*v==6 for u in range(-70,71) for v in range(-70,71))
 assert 'never an integer square' in load(QA/'edited-oracle-before-ui.json')['variance_two_unreachable']
 assert edits[0]['expected']['bias']==['1']*4 and edits[1]['expected']['variance'][0]=='4/3' and edits[2]['expected']['variance'][0]=='7/3'
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['61032'] and all(cleanup['ports_after'][p] for p in ['53478','60285','50835']) and cleanup['server_closed'] and cleanup['memory_receipts_discarded']==123 and cleanup['files_recorded_by_server']==0 and cleanup['owned_tab_closed']=='53' and cleanup['viewport_reset'] and cleanup['protected_ports_untouched']
 assert e['cleanup']['owned_server_stopped'] and e['viewport_reset'] and load(QA/'server-session.json')['record_only'] is False and load(QA/'toolchain.json')['installed'] is False
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-measurement-bias-repeatability/SKILL.md').read_text()):assert (ROOT/'skills/atlas-measurement-bias-repeatability'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha,n
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':72,'select_resets':18,'explicit_reset':True,'edited':8,'one_operation_shift':True,'stale':4,'UI_POST':121,'total_memory_receipts':123,'captures':3,'clicked_local_viewers':9,'NIST_clicked':True,'pairwise_moment_oracle':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
