"""Readonly independent exact inequality and actual SVG/source/memory receipt checks."""
import datetime,json,re,sys
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T191639582830Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','stage','table','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert all(p['svg_count']==0 and not p['text'] and not p['points'] and not p['lines'] for p in s['plots'])
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
  for key,field in [('fixed','fixed_outside'),('buggy','buggy_outside')]:
   if key in o:assert [p[field] for p in s['steps']]==o[key]
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None}
 return r
def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o)
 assert s['initial_run']=='20261005T191632549409Z-control' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category']
 assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','stage','table','model']) and o['code'] in s['classification'];assert not s['table_rows']
  assert all(p['svg_count']==0 and not p['text'] for p in s['plots']);return
 out=r['summary'];assert s['classification']=='固定/再推定比較 · '+cat and not s['answer_hidden']
 assert json.loads(s['model'])=={**{n:out[n] for n in ['frozen','steps','rule','estimator','sigma_known','units']},'context':r['context']}
 assert s['cards']=='固定版の外側点'+str(len(out['fixed_flags']))+'故障版が隠した点'+str(len(out['masked_flags']))+'別仕様の外側点'+str(len(out['spec_flags']))
 f=out['frozen'];assert f"baseline N{f['N']}: mean={f['mean']}, s²={f['s2']} arb²" in s['stage'] and '仕様 '+ ' / '.join(map(str,out['input']['specification']))+' arbは別条件' in s['stage']
 for text in ['baseline mean='+f['mean'],'s²='+f['s2'],'半径平方='+f['radius_squared'],'分母N−1','等値は内側','母σ未知','I-MR/s÷c₄未実装','正規性・独立性・誤警報率・ARL・原因特定は未検証','全点内側でも安定を証明せず']:assert text in s['answer']
 assert len(s['table_rows'])==len(out['steps'])
 for p,row in zip(out['steps'],s['table_rows']):
  assert row['index']==str(p['index']) and row['cells']==list(map(str,[p['index'],p['value'],f['mean'],f['s2'],'外' if p['fixed_outside'] else '内',p['buggy']['mean'],p['buggy']['s2'],'外' if p['buggy_outside'] else '内','外' if p['spec_outside'] else '内']))
 values=out['input']['baseline']+out['input']['monitoring'];nb=f['N'];n=len(values)
 def series(kind,role):
  key='mean' if role=='center' else 'LCL_approx' if role=='control-lower' else 'UCL_approx';start=float(F(f[key])) if key=='mean' else f[key]
  return [start]*nb+[start if kind=='fixed' else float(F(p['buggy'][key])) if key=='mean' else p['buggy'][key] for p in out['steps']]
 allv=values+out['input']['specification']+series('buggy','control-lower')+series('buggy','control-upper')+[f['LCL_approx'],f['UCL_approx']];lo=min(allv)-2;hi=max(allv)+2
 def x(i):return 40+i*540/(n-1)
 def y(v):return 260-(float(v)-lo)/(hi-lo)*220
 for plot in s['plots']:
  kind=plot['kind'];assert plot['svg_count']==1 and plot['baseline_count']==str(nb) and len(plot['points'])==n and len(plot['lines'])==6;near(plot['lo'],lo);near(plot['hi'],hi)
  lines={p['role']:p for p in plot['lines']};assert set(lines)=={'center','control-lower','control-upper','spec-lower','spec-upper','observations'}
  for role,line in lines.items():
   expected=values if role=='observations' else [out['input']['specification'][0 if role=='spec-lower' else 1]]*n if role.startswith('spec') else series(kind,role)
   actualvalues=list(map(float,line['values'].split(',')));vertices=[list(map(float,v.split(','))) for v in line['points'].split()];assert len(actualvalues)==n and len(vertices)==n
   for i,v in enumerate(expected):near(actualvalues[i],v);near(vertices[i][0],x(i));near(vertices[i][1],y(v))
   if role.startswith('control'):assert line['classes']=='control-line'
   if role.startswith('spec'):assert line['classes']=='spec-line'
  assert len(plot['split'])==1;near(plot['split'][0]['x'],x(nb-.5))
  for i,point in enumerate(plot['points']):
   baseline=i<nb;flag=False if baseline else out['steps'][i-nb][kind+'_outside'];assert point['phase']==('baseline' if baseline else 'monitoring') and point['index']==str(i+1 if baseline else i-nb+1) and point['value']==str(values[i]) and point['outside']==str(flag).lower();near(point['cx'],x(i));near(point['cy'],y(values[i]));assert point['classes']==('baseline-point' if baseline else 'outside-point' if flag else 'monitor-point')
def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json');assert export['mode']=='memory-only' and len(export['requests'])==123;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==123
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(r['revision']>=0 for r in export['requests'])==121
 assert len(e['matrix'])==72 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','masked','alert','spec-only','quiet','input']}
 for p in e['matrix']:assert p['state']['prediction']==p['pred'] and p['state']['input']==fixed[p['id']]['input_json'];display(p['state'],fixed[p['id']]['expected'],by_id)
 assert len(e['resets'])==18
 for p in e['resets']:
  opened(p['before']);display(p['before'],fixed['shock']['expected'],by_id);empty(p['after'])
  if p['kind']=='prediction':assert p['after']['prediction']==p['value'] and p['after']['input']==p['before']['input']
  else:assert p['after']['scenario']==p['value'] and p['after']['prediction']=='' and p['after']['input']==fixed[p['value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['shock']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']=='edited'
 assert len(e['edited'])==8
 for p,o in zip(e['edited'],edits):
  assert p['id']==o['id'] and p['expected']==o['expected'];opened(p['before']);empty(p['reset']);assert p['reset']['input']==o['input_json'];display(p['state'],o['expected'],by_id)
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(json.loads(p['state']['trace'])['request_utc'])
 one=e['one_operation'];display(one['before'],edits[0]['expected'],by_id);empty(one['reset']);display(one['after'],edits[1]['expected'],by_id);assert one['before']['input']==edits[0]['input_json'] and one['after']['input']==edits[1]['input_json']
 assert len(e['stale'])==4 and {p['kind'] for p in e['stale']}=={'prediction','scenario','input','reset'}
 for p in e['stale']:opened(p['before']);empty(p['reset']);empty(p['after']);assert p['reset']==p['after'] and p['elapsed_ms']>=600 and '計算中' in p['pending']['message'] and p['pending']['compare_disabled']
 opened(e['host_before']);display(e['host_before'],fixed['shock']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for p in e['captures']:
  b=(QA/p['file']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(p['state'],oracle[p['state']['input']],by_id);assert p['state']['scroll_width']<=p['state']['width']
  if p['file'].startswith('mobile'):assert p['state']['width']==390
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-frozen-baseline-control-limits/SKILL.md','view/qe-coverage':ROOT/'../../../quality-engineering-atlas/COVERAGE.md'};assert len(e['local_navigation'])==9
 for p in e['local_navigation']:
  shown=p['shown'];assert shown['body'] and shown['scroll_width']<=shown['width']
  if p['href'] in mapping:assert shown['body']==mapping[p['href']].read_text()
  elif p['href']=='view/fixed-raw':assert json.loads(shown['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:raw=json.loads(e['link_raw_before']['trace']);assert json.loads(shown['body'])==raw==by_id[raw['request_id']]
 assert e['primary_navigation']['headings']==['6.3.2.','What are Variables Control Charts?'] and e['primary_navigation']['url']=='https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm'
 http=load(QA/'http-links.json');assert http['unit_sha_mtime_unchanged_during_export'] and http['ui_post_count']==121 and http['health']['mode']=='memory-only' and http['health']['request_count']==123
 for p in http['rows']:assert p['status']==(404 if p['path']=='view/not-listed' else 200)
 assert digest(mapping['view/qe-coverage'])==http['parent_reference_sha256'];setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged'] and all(p['status']==200 for p in setup['get_rows'])
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False and digest(ROOT/'qa/hand-before-arithmetic-repair.json')==prior['files']['hand-oracle.json'] and digest(ROOT/'expected-table.json')==prior['files']['expected-table.json']
 correction=load(ROOT/'qa/hand-correction.json');assert correction['correct']=='358/15' and correction['before_first_fixed_record'] and correction['old']!=correction['correct']
 assert datetime.datetime.fromisoformat(correction['utc'])<datetime.datetime.strptime(e['run_id'].split('Z-')[0],'%Y%m%dT%H%M%S%f').replace(tzinfo=datetime.timezone.utc)
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['59696'] and all(cleanup['ports_after'][p] for p in ['53478','60285','50835']) and cleanup['server_closed'] and cleanup['memory_receipts_discarded']==123 and cleanup['files_recorded_by_server']==0 and cleanup['owned_tab_closed']=='52' and cleanup['viewport_reset'] and cleanup['protected_ports_untouched']
 assert e['cleanup']['owned_server_stopped'] and e['viewport_reset'] and load(QA/'server-session.json')['record_only'] is False and load(QA/'toolchain.json')['installed'] is False
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-frozen-baseline-control-limits/SKILL.md').read_text()):assert (ROOT/'skills/atlas-frozen-baseline-control-limits'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha,n
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':72,'select_resets':18,'explicit_reset':True,'edited':8,'one_operation_shock':True,'stale':4,'UI_POST':121,'total_memory_receipts':123,'captures':3,'clicked_local_viewers':9,'NIST_clicked':True,'pairwise_integer_oracle':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
