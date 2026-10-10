"""Readonly independent OLS of actual IAB/memory receipts and SVG geometry."""
import datetime,json,re,sys
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T183533908152Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','conditional','table','variance','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert all(p['svg_count']==0 and not p['cells'] and not p['lines'] and p['prediction'] is None and p['error'] is None for p in s['plots'])
def opened(s):assert all(s[n] for n in ['answer_open','model_open','trace_open'])
def actual(raw,o):
 assert raw['mode']=='memory-only' and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES};run=raw['run'];r=run['result'];assert raw['input_json']==run['stdin'] and json.loads(run['stdout'])==r and run['stderr']=='' and r['status']==o['status']
 assert datetime.datetime.fromisoformat(raw['request_utc']).tzinfo is not None
 assert raw['raw_href']=='view/receipt/'+raw['request_id'] and raw['raw_json_href']=='receipts/'+raw['request_id']+'.json'
 if r['status']=='calculated':
  assert run['exit']==0;inspect(r,json.loads(raw['input_json']));s=r['summary'];assert s['category']==o['category'];assert datetime.datetime.fromisoformat(r['started_utc'])<=datetime.datetime.fromisoformat(r['ended_utc'])
  if 'hand_case' in o:handcheck(r,o['hand_case'])
  if 'effects' in o:
   assert [s['effects'][n] for n in ['A','B','AB']]==o['effects'] and s['coefficients']['AB']==o['betaAB'] and s['DOD']==o['DOD'] and s['MSE']==o['MSE'] and [s['conditional_A'][n] for n in ['B-','B+']]==o['conditional'] and s['df']['within']==8
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None,'cells':None}
 return r

def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o);assert s['initial_run']=='20261005T183533319681Z-factorial' and not s['results_hidden'];assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category'];assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','conditional','table','variance','model']);assert all(p['svg_count']==0 for p in s['plots']) and o['code'] in s['classification'];return
 out=r['summary'];assert s['classification']=='4cell × 3合成反復 · '+out['category'] and not s['answer_hidden'];model=json.loads(s['model']);assert model=={**{n:out[n] for n in ['coefficients','SS','df','MSE','main_only_fitted_means','main_only_SSE','ofat','units']},'context':r['context']}
 for n in ['A','B','AB']:
  assert out['effects'][n]+' arb' in s['cards'] and out['coefficients'][n]+' arb' in s['cards'];assert out['effects'][n] in s['answer']
 for word in ['差の差='+out['DOD'],'betaAB='+out['coefficients']['AB'],'加法予測='+out['ofat']['missing_prediction'],'予測誤差='+out['ofat']['prediction_error'],'MSE='+out['MSE'],'SSE/df8','実物反復・無作為化・時間順序・実因果・有意性評価は未実施','Taguchi SN比/直交表は扱いません']:assert word in s['answer']
 assert '差の差='+out['DOD'] in s['conditional'] and out['conditional_A']['B-'] in s['conditional'] and out['conditional_A']['B+'] in s['conditional']
 assert 'cell内SSE='+out['SS']['within'] in s['variance'] and 'MSE='+out['MSE'] in s['variance'] and 'df=8' in s['variance'] and 'interactionのSS='+out['SS']['AB'] in s['variance'] and '有意性検定は行っていません' in s['variance']
 for c in r['cells']:
  for text in [c['id'],', '.join(map(str,c['observations'])),c['mean'],c['SSE'],c['sample_variance']]:assert text in s['table']
 all_values=[F(v) for c in r['cells'] for v in c['observations']]+[F(out['ofat']['missing_prediction'])];lo=min(all_values)-2;hi=max(all_values)+2
 def y(v):return 270-(float(F(v))-float(lo))/(float(hi)-float(lo))*235
 for p in s['plots']:
  assert p['svg_count']==1 and len(p['cells'])==4 and len(p['lines'])==2;near(p['lo'],lo);near(p['hi'],hi)
  for b,line in enumerate(p['lines']):
   ids=[0,1] if b==0 else [2,3];assert line['means']==','.join(out['means'][i] for i in ids);near(line['x1'],95);near(line['x2'],365);near(line['y1'],y(out['means'][ids[0]]));near(line['y2'],y(out['means'][ids[1]]));assert ('bminus' if b==0 else 'bplus') in line['classes']
  for i,g in enumerate(p['cells']):
   c=r['cells'][i];assert g['cell']==str(i) and g['mean']==c['mean'] and g['observed_ofat']==str(i!=3).lower();x=95 if c['levels'][0]==-1 else 365
   points=[v for v in g['circles'] if v['role'] is None];means=[v for v in g['circles'] if v['role']=='mean'];assert len(means)==1;near(means[0]['cx'],x);near(means[0]['cy'],y(c['mean']))
   assert len(points)==(0 if p['kind']=='ofat' and i==3 else 3)
   for j,pt in enumerate(points):assert pt['replicate']==str(j) and pt['response']==str(c['observations'][j]);near(pt['cx'],x+(j-1)*8);near(pt['cy'],y(c['observations'][j]))
  if p['kind']=='full':assert p['prediction'] is None and p['polygon'] is None and p['error'] is None
  else:
   assert p['prediction']==out['ofat']['missing_prediction'] and p['error']==out['ofat']['prediction_error'] and p['polygon']['response']==out['ofat']['missing_prediction'] and p['polygon']['observed']=='false'
   vertices=[list(map(float,v.split(','))) for v in p['polygon']['points'].split()];near(vertices[0][0],365);near(vertices[0][1],y(out['ofat']['missing_prediction'])-7)

def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json');assert export['mode']=='memory-only' and len(export['requests'])==112;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==112
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(raw['revision']>=0 for raw in export['requests'])==110
 assert len(e['matrix'])==60 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','additive','interaction','crossover','input']}
 for x in e['matrix']:assert x['state']['input']==fixed[x['id']]['input_json'];display(x['state'],fixed[x['id']]['expected'],by_id)
 assert len(e['resets'])==17
 for x in e['resets']:
  opened(x['before']);display(x['before'],fixed['crossover']['expected'],by_id);empty(x['after'])
  if x['kind']=='prediction':assert x['after']['prediction']==x['new_value'] and x['after']['input']==x['before']['input']
  else:assert x['after']['scenario']==x['new_value'] and x['after']['prediction']=='' and x['after']['input']==fixed[x['new_value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['crossover']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']!=reset['after']['input']
 assert len(e['edited'])==10
 for x,o in zip(e['edited'],edits):
  assert {n:x[n] for n in ['id','input_json','expected']}==o;opened(x['before']);empty(x['reset']);assert x['reset']['input']==o['input_json'];display(x['state'],o['expected'],by_id)
 assert len(e['stale'])==4 and {x['kind'] for x in e['stale']}=={'prediction','scenario','input','reset'}
 for x in e['stale']:
  opened(x['before']);empty(x['reset']);empty(x['after']);assert x['reset']==x['after'];assert (datetime.datetime.fromisoformat(x['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['started_utc'].replace('Z','+00:00'))).total_seconds()>=.6
 opened(e['host_before']);display(e['host_before'],fixed['crossover']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert [x['path'] for x in e['captures']]==['desktop-crossover.jpg','mobile-tiny-interaction.jpg','mobile-input-refusal.jpg']
 for x in e['captures']:
  b=(QA/x['path']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(x['state'],oracle[x['state']['input']],by_id);assert x['state']['scroll_width']<=x['state']['width']
  if x['path'].startswith('mobile'):assert x['state']['width']==390
 assert len(e['navigation'])==9 and all(x['status']=='shown' and x['body'] and x['scroll']<=x['width'] for x in e['navigation'])
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-replicated-two-factor-interaction/SKILL.md','view/qe-coverage':ROOT/'../../../quality-engineering-atlas/COVERAGE.md'}
 for x in e['navigation']:
  if x['path'] in mapping:assert x['body']==mapping[x['path']].read_text()
  elif x['path']=='view/fixed-raw':assert json.loads(x['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:assert json.loads(x['body'])==e['link_raw_before']==by_id[e['link_raw_before']['request_id']]
 assert e['primary_navigation']['status']=='shown' and e['primary_navigation']['not_bypassed'] and 'Choosing an experimental design' in e['primary_navigation']['headings']
 http=load(QA/'http-links.json');assert http['unit_sha_mtime_unchanged_during_export'] and http['ui_post_count']==110 and http['health']['mode']=='memory-only' and http['health']['request_count']==112
 for x in http['rows']:assert x['status']==(404 if x['path']=='view/not-listed' else 200)
 assert digest(mapping['view/qe-coverage'])==http['parent_reference_sha256'];setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged'] and setup['mode']=='memory-only' and all(r['status']==200 for r in setup['get_rows'])
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False
 for name,sha in prior['files'].items():assert digest(ROOT/name)==sha
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['55501'] and all(cleanup['ports_after'][n] for n in ['53478','60285','50835']);assert cleanup['server_closed'] and cleanup['memory_receipts_discarded']==112 and cleanup['files_recorded_by_server']==0 and cleanup['owned_tab_closed']=='50' and cleanup['viewport_reset'] and cleanup['protected_ports_untouched']
 assert e['cleanup']['owned_server_stopped'] and e['viewport_reset'];session=load(QA/'server-session.json');assert session['mode']=='memory-only' and session['record_only'] is False
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-replicated-two-factor-interaction/SKILL.md').read_text()):assert (ROOT/'skills/atlas-replicated-two-factor-interaction'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':60,'select_resets':17,'explicit_reset':True,'edited':10,'stale':4,'UI_POST':110,'total_memory_receipts':112,'captures':3,'clicked_local_viewers':9,'NIST_clicked':True,'OLS_oracle':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
