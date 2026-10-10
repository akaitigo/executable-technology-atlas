"""Readonly independent delete enumeration and actual SVG/source/memory receipt checks."""
import datetime,json,re,sys
from pathlib import Path
from fractions import Fraction as F
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T194352446173Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','stage','table','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert all(p['svg_count']==0 and not p['text'] and not p['release_groups'] and not p['candidates'] for p in s['plots'])
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
  for key in ['candidates','witness_count']:
   if key in o:assert s[key]==o[key]
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None}
 return r
def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o)
 assert s['initial_run']=='20261005T194343270878Z-diff' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category'];assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','stage','table','model']) and o['code'] in s['classification'] and not s['table_rows'];assert all(p['svg_count']==0 and not p['text'] for p in s['plots']);return
 out=r['summary'];assert s['classification']=='有限候補列挙 · '+cat and not s['answer_hidden']
 assert json.loads(s['model'])=={**{n:out[n] for n in ['delta','candidates','witness_count','candidate_witness_counts','enumerated_transition_count','equation','target_presence','delete_capacity_rule','candidate_semantics']},'context':r['context']}
 assert s['cards']=='整合category'+(' / '.join(out['candidates']) or 'なし（不整合）')+'count-vector witness'+str(out['witness_count'])+'故障: 背景を無視した断定'+(out['naive_category_ignoring_background'] or '差分単独で候補なし')
 for text in ['対象1record追加/残存','背景add≤'+str(out['input']['background']['max_add']),'delete≤'+str(out['input']['background']['max_delete']),'走査'+str(out['enumerated_transition_count'])+' / 最大300']:assert text in s['stage']
 for text in ['整合category=['+','.join(out['candidates'])+']','witness='+str(out['witness_count']),'countから対象存在を推定していません','対象や新recordを削除しません','0候補は前提不整合で安全ではなく','count-vector数は確率/個人数ではなく','実人物・外部linkage・現実再識別率・DP保証・法適合・公表は未実施']:assert text in s['answer']
 assert len(s['table_rows'])==out['witness_count']
 for i,(w,row) in enumerate(zip(out['witnesses'],s['table_rows'])):assert row['index']==str(i) and row['cells']==[w['target'],', '.join(map(str,w['add'])),', '.join(map(str,w['delete']))]
 release=next(p for p in s['plots'] if p['kind']=='release');candidate=next(p for p in s['plots'] if p['kind']=='candidate');assert release['svg_count']==candidate['svg_count']==1 and not release['candidates'] and not candidate['release_groups']
 hi=max([1]+out['input']['before']+out['input']['after'])+1;near(release['hi'],hi);assert len(release['release_groups'])==3 and len(candidate['candidates'])==3 and candidate['category']==cat
 for i,g in enumerate(release['release_groups']):
  x=95+135*i;assert g['category']==out['input']['categories'][i] and g['before']==str(out['input']['before'][i]) and g['after']==str(out['input']['after'][i]) and g['delta']==str(out['delta'][i]) and len(g['rects'])==2
  for phase,left in [('before',x-34),('after',x+4)]:
   rect=next(p for p in g['rects'] if p['phase']==phase);v=out['input'][phase][i];y=270-v/hi*220;assert rect['value']==str(v) and rect['classes']==phase+'-bar';near(rect['x'],left);near(rect['y'],y);near(rect['width'],30);near(rect['height'],270-y)
  assert g['texts']==[str(out['input']['before'][i]),str(out['input']['after'][i]),g['category']+' Δ'+str(out['delta'][i])]
 for i,g in enumerate(candidate['candidates']):
  label=out['input']['categories'][i];possible=label in out['candidates'];count=out['candidate_witness_counts'][label];assert g['category']==label and g['possible']==str(possible).lower() and g['count']==str(count) and len(g['circle'])==1 and g['texts']==[label,'witness '+str(count),'整合' if possible else '候補なし'];circle=g['circle'][0];near(circle['cx'],85+135*i);near(circle['cy'],115);near(circle['r'],38);assert circle['classes']==('candidate-node' if possible else 'impossible-node')
 assert ('0候補 = 前提不整合（安全ではない）' if cat=='inconsistent' else 'category一意はこの前提下のみ' if cat=='known' else '複数category整合（安全保証ではない）') in candidate['text']
def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json');assert export['mode']=='memory-only' and len(export['requests'])==110;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==110
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(r['revision']>=0 for r in export['requests'])==108
 assert len(e['matrix'])==60 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','known','ambiguous','inconsistent','input']}
 for p in e['matrix']:assert p['state']['prediction']==p['pred'] and p['state']['input']==fixed[p['id']]['input_json'];display(p['state'],fixed[p['id']]['expected'],by_id)
 assert len(e['resets'])==17
 for p in e['resets']:
  opened(p['before']);display(p['before'],fixed['sole-A']['expected'],by_id);empty(p['after'])
  if p['kind']=='prediction':assert p['after']['prediction']==p['value'] and p['after']['input']==p['before']['input']
  else:assert p['after']['scenario']==p['value'] and p['after']['prediction']=='' and p['after']['input']==fixed[p['value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['sole-A']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']=='edited'
 assert len(e['edited'])==8
 for p,o in zip(e['edited'],edits):
  assert p['id']==o['id'] and p['expected']==o['expected'];opened(p['before']);empty(p['reset']);assert p['reset']['input']==o['input_json'];display(p['state'],o['expected'],by_id)
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'].replace('Z','+00:00'))<datetime.datetime.fromisoformat(json.loads(p['state']['trace'])['request_utc'])
 one=e['one_operation'];display(one['before'],fixed['sole-A']['expected'],by_id);empty(one['reset']);display(one['after'],fixed['same-delta-background']['expected'],by_id);assert one['before']['input']==fixed['sole-A']['input_json'] and one['after']['input']==fixed['same-delta-background']['input_json'];pre=json.loads(one['before']['trace'])['run']['result']['summary'];post=json.loads(one['after']['trace'])['run']['result']['summary'];assert pre['input']['before']==post['input']['before'] and pre['input']['after']==post['input']['after'] and pre['candidates']==['A'] and post['candidates']==['A','B','C']
 assert len(e['stale'])==4 and {p['kind'] for p in e['stale']}=={'prediction','scenario','input','reset'}
 for p in e['stale']:opened(p['before']);empty(p['reset']);empty(p['after']);assert p['reset']==p['after'] and p['elapsed_ms']>=600 and '計算中' in p['pending']['message'] and p['pending']['compare_disabled']
 opened(e['host_before']);display(e['host_before'],fixed['sole-A']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for p in e['captures']:
  b=(QA/p['file']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(p['state'],oracle[p['state']['input']],by_id);assert p['state']['scroll_width']<=p['state']['width']
  if p['file'].startswith('mobile'):assert p['state']['width']==390
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-two-release-count-differencing/SKILL.md','view/parent-path':ROOT/'../../../subjects/privacy-engineering/LEARNING_PATH.md'};assert len(e['local_navigation'])==9
 for p in e['local_navigation']:
  shown=p['shown'];assert shown['body'] and shown['scroll_width']<=shown['width']
  if p['href'] in mapping:assert shown['body']==mapping[p['href']].read_text()
  elif p['href']=='view/fixed-raw':assert json.loads(shown['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:raw=json.loads(e['link_raw_before']['trace']);assert json.loads(shown['body'])==raw==by_id[raw['request_id']]
 assert e['primary_navigation']['url']=='https://csrc.nist.gov/pubs/sp/800/188/final' and any('NIST SP 800-188' in h for h in e['primary_navigation']['headings'])
 http=load(QA/'http-links.json');assert http['unit_sha_mtime_unchanged_during_export'] and http['ui_post_count']==108 and http['health']['mode']=='memory-only' and http['health']['request_count']==110
 for p in http['rows']:assert p['status']==(404 if p['path']=='view/not-listed' else 200)
 assert digest(mapping['view/parent-path'])==http['parent_reference_sha256'];setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged'] and all(p['status']==200 for p in setup['get_rows'])
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False
 for n,sha in prior['files'].items():assert digest(ROOT/n)==sha
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['62323'] and all(cleanup['ports_after'][p] for p in ['53478','60285','50835']) and cleanup['server_closed'] and cleanup['memory_receipts_discarded']==110 and cleanup['files_recorded_by_server']==0 and cleanup['owned_tab_closed']=='54' and cleanup['viewport_reset'] and cleanup['protected_ports_untouched']
 assert e['cleanup']['owned_server_stopped'] and e['viewport_reset'] and load(QA/'server-session.json')['record_only'] is False and load(QA/'toolchain.json')['installed'] is False
 for target in re.findall(r'\]\(([^)]+)\)',(ROOT/'skills/atlas-two-release-count-differencing/SKILL.md').read_text()):assert (ROOT/'skills/atlas-two-release-count-differencing'/target).resolve().is_file()
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha,n
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':60,'select_resets':17,'explicit_reset':True,'edited':8,'one_operation_premise':True,'stale':4,'UI_POST':108,'total_memory_receipts':110,'captures':3,'clicked_local_viewers':9,'NIST_clicked':True,'independent_enumeration_oracle':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
