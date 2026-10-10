"""Read actual IAB DOM evidence; independently check every mathematical result."""
import datetime,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect
QA=ROOT/'qa/20261005T180120076210Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','caption','table','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not s['answer_open'] and not s['trace_open']
 assert all(p['svg_count']==0 and not p['groups'] and p['truth'] is None for p in s['plots'])
def opened(s):assert s['answer_open'] and s['trace_open']
def actual(raw,o):
 assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES};run=raw['run'];r=run['result']
 assert raw['input_json']==run['stdin'] and json.loads(run['stdout'])==r and run['stderr']=='' and r['status']==o['status']
 if r['status']=='calculated':
  assert run['exit']==0;assert datetime.datetime.fromisoformat(r['started_utc']).tzinfo is not None and datetime.datetime.fromisoformat(r['started_utc'])<=datetime.datetime.fromisoformat(r['ended_utc']);inspect(r,json.loads(raw['input_json']));s=r['summary'];assert s['category']==o['category'] and s['input']['p']==o['p'] and s['input']['k']==o['k']
  if 'selected_contains' in o:assert {m:s['selected'][m]['contains'] for m in ['wald','wilson']}==o['selected_contains']
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None,'rows':None}
 return r

def display(s,o):
 raw=load(ROOT/s['raw']);assert raw['input_json']==s['input'];r=actual(raw,o);assert s['initial_run']=='20261005T180119345114Z-coverage' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · Decimal40 · exit{raw['run']['exit']}"
 category='input' if r['status']=='input_refusal' else r['summary']['category'];message=('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==category else '予想と不一致。')+' 観測: '+category;assert s['message']==message
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not s['cards'] and not s['caption'] and not s['table'];assert all(p['svg_count']==0 for p in s['plots']);assert json.loads(s['trace'])==raw['run'] and o['code'] in s['classification'];return
 summary=r['summary'];x=summary['input'];assert json.loads(s['trace'])==r and not s['answer_hidden']
 assert s['classification']==f"n=8 / 真p={x['p']} / 観測k={x['k']}"
 for m in ['wald','wilson']:
  for text in [summary['coverage'][m],summary['difference_from_nominal'][m]]:assert text in s['cards']
  assert ','.join(map(str,summary['covered_k'][m])) in s['cards']
  for key in ['lower','upper']:assert summary['selected'][m][key] in s['answer']
  assert summary['coverage'][m] in s['answer']
 assert summary['delta'] in s['caption'] and str(x['k']) in s['caption']
 for word in ['95%保証ではありません','丸めz','近似端点','Fraction oracle','固定区間','posterior','真p既知','実データ推定・個別助言は未評価']:assert word in s['answer']
 for p in s['plots']:
  assert p['svg_count']==1 and len(p['groups'])==9 and p['truth']==x['p'];m=p['method']
  for k,g in enumerate(p['groups']):
   t=r['rows'][k][m];assert g['k']==str(k) and g['contains']==str(t['contains']).lower() and g['selected']==str(k==x['k']).lower() and len(g['line'])==1
   line=g['line'][0];assert line['lower']==t['lower'] and line['upper']==t['upper']
   for key,end in [('x1','lower'),('x2','upper')]:assert abs(float(line[key])-(55+(float(t[end])+.2)/1.4*355))<1e-9
   assert ('covered' in line['classes'])==t['contains'] and ('selected' in line['classes'])==(k==x['k'])
 for row in r['rows']:
  assert row['mass'] in s['table']
  for m in ['wald','wilson']:
   for end in ['lower','upper']:assert format(float(row[m][end]),'.5f') in s['table']

def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={x['id']:x for x in rows};edited=load(QA/'edited-oracle-before-ui.json')['cases'];by_text={x['input_json']:x['expected'] for x in rows+edited}
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False
 for n,sha in prior['files'].items():assert digest(ROOT/n)==sha
 assert len(e['matrix'])==80 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','wilson','equal','wald','input']}
 for x in e['matrix']:assert x['state']['input']==fixed[x['id']]['input_json'];display(x['state'],fixed[x['id']]['expected'])
 assert len(e['resets'])==21
 for x in e['resets']:
  opened(x['before']);empty(x['after'])
  if x['kind']=='prediction':assert x['after']['input']==x['before']['input'] and x['after']['prediction']==x['new_value']
  else:assert x['after']['scenario']==x['new_value'] and x['after']['prediction']=='' and x['after']['input']==fixed[x['new_value']]['input_json']
 assert len(e['edited'])==12
 for x,o in zip(e['edited'],edited):
  assert {n:x[n] for n in ['id','input_json','expected']}==o;opened(x['before']);empty(x['reset']);assert x['reset']['input']==o['input_json'];display(x['state'],o['expected'])
 assert len(e['stale'])==3 and {x['kind'] for x in e['stale']}=={'prediction','scenario','input'}
 for x in e['stale']:
  opened(x['before']);empty(x['reset']);empty(x['after']);assert x['reset']==x['after'];assert (datetime.datetime.fromisoformat(x['checked_utc'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(x['started_utc'].replace('Z','+00:00'))).total_seconds()>=.6
 opened(e['host_before']);display(e['host_before'],fixed['p1-k0']['expected']);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert [x['path'] for x in e['captures']]==['desktop-boundary-k0.jpg','mobile-fixed-k3.jpg','mobile-input-refusal.jpg']
 for x in e['captures']:
  b=(QA/x['path']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(x['state'],by_text[x['state']['input']]);assert x['state']['scroll_width']<=x['state']['width']
  if x['path'].startswith('mobile'):assert x['state']['width']==390
 selected=json.loads(e['captures'][1]['state']['trace'])['summary']['selected'];assert selected['k']==3 and selected['wald']['contains'] and not selected['wilson']['contains']
 reqs=list((ROOT/'observations'/e['preview_id']/'requests').glob('*.json'));assert len(reqs)==135
 for p in reqs:
  raw=load(p);assert raw['request_id']==p.stem;actual(raw,by_text[raw['input_json']])
 start=load(ROOT/'observations'/e['preview_id']/'server-start.json');assert start['source_digests']=={n:digest(ROOT/n) for n in SOURCES} and start['delay_ms']==600
 assert load(ROOT/'observations'/e['preview_id']/'server-stop.json')['server_closed']
 fixedraw=load(ROOT/'observations'/e['run_id']/'raw.json');assert fixedraw['source_digests']==start['source_digests']
 index=load(ROOT/'observations'/e['run_id']/'artifact-index.json');assert index['excludes_self']
 for n,sha in index['files'].items():assert digest(ROOT/'observations'/e['run_id']/n)==sha
 for row in fixedraw['rows']:actual({'input_json':row['input_json'],'source_digests':fixedraw['source_digests'],'run':row['run']},row['expected'])
 links=load(QA/'http-links.json');assert links['old_wald_exists']
 for x in links['rows']:assert x['status']==(404 if x['path'].startswith('../') else 200)
 for x in e['links']:
  if not x['href'].startswith('https:'):assert (ROOT/x['href']).is_file()
 for x in e['navigation']:assert x['not_bypassed'] and x['closed'] and x['status']=='blocked' and 'ERR_BLOCKED_BY_CLIENT' in x['error']
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['52042'] and not cleanup['ports_after']['52866'] and cleanup['ports_after']['53478'] and cleanup['ports_after']['60285'];assert cleanup['protected_ports_untouched'] and cleanup['viewport_reset'] and cleanup['owned_tabs_closed']==['46','47','48','49']
 assert e['viewport_reset'] and e['cleanup']['owned_servers_stopped'];assert not load(ROOT/'qa/toolchain.json')['installed']
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-wilson-wald-finite-coverage/SKILL.md').read_text()):assert (ROOT/'skills/atlas-wilson-wald-finite-coverage'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  index=load(QA/'artifact-index.json');assert index['excludes_self'] and index['excludes_future_verification']
  for n,sha in index['files'].items():assert digest(ROOT/n)==sha
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':80,'select_resets':21,'edited':12,'stale':3,'requests':135,'captures':3,'host_failure':True,'exact_score_oracle':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
