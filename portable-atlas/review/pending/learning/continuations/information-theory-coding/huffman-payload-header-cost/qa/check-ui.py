"""Read-only independent finite Huffman UI, geometry and receipt checks."""
import datetime,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from runner import SOURCES,digest,snapshot
from checker import inspect,handcheck
QA=ROOT/'qa/20261005T204422297661Z-iab'
def load(p):return json.loads(p.read_text())
def empty(s):
 for n in ['classification','cards','stage','table','tree','model','trace','run','answer']:assert s[n]=='',n
 assert s['raw'] is None and s['results_hidden'] and s['answer_hidden'] and not any(s[n] for n in ['answer_open','model_open','trace_open'])
 assert not s['table_rows'] and all(p['svg_count']==0 and not p['text'] and not p['groups'] for p in s['plots'])
def opened(s):assert all(s[n] for n in ['answer_open','model_open','trace_open'])
def actual(raw,o):
 assert raw['mode']=='memory-only' and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
 run=raw['run'];r=run['result'];assert raw['input_json']==run['stdin'] and json.loads(run['stdout'])==r and run['stderr']=='' and r['status']==o['status']
 assert datetime.datetime.fromisoformat(raw['request_utc']).tzinfo and run['argv']==['python3','-B','calculate.py']
 assert raw['raw_href']=='view/receipt/'+raw['request_id'] and raw['raw_json_href']=='receipts/'+raw['request_id']+'.json'
 if r['status']=='calculated':
  assert run['exit']==0;inspect(r,json.loads(raw['input_json']));s=r['summary'];assert s['category']==o['category']
  if 'hand_case' in o:handcheck(r,o['hand_case'])
  for k,method in [('huffman_total_bits','huffman'),('fixed_total_bits','fixed')]:
   if k in o:assert s[method]['total_bits']==o[k]
 else:assert run['exit']==2 and r=={'status':'input_refusal','code':o['code'],'summary':None}
 return r
def near(a,b):assert abs(float(a)-float(b))<1e-8,(a,b)
def display(s,o,by_id):
 raw=json.loads(s['trace']);assert raw==by_id[raw['request_id']] and raw['input_json']==s['input'] and raw['raw_href']==s['raw'];r=actual(raw,o)
 assert s['initial_run']=='20261005T204420945944Z-huffman' and not s['results_hidden']
 assert s['run']==f"request {raw['request_id']} · memory-only · exit{raw['run']['exit']}"
 cat='input' if r['status']=='input_refusal' else r['summary']['category'];assert s['message']==('予想未選択。' if not s['prediction'] else '予想と一致。' if s['prediction']==cat else '予想と不一致。')+' 観測: '+cat
 if r['status']=='input_refusal':
  assert s['classification']==f"入力拒否 {o['code']}、exit2。図・codebook・答えなし。" and s['answer_hidden'] and not s['answer'] and not any(s[n] for n in ['cards','stage','table','tree','model']) and not s['table_rows'];assert all(p['svg_count']==0 and not p['text'] for p in s['plots']);return
 a=r['summary'];h=a['huffman'];f=a['fixed'];assert s['classification']=='header込み比較 · '+cat and not s['answer_hidden'] and json.loads(s['model'])==a
 assert s['cards']==f"model加重平均長 L{a['weighted_mean_length']} bit/記号Huffman total{h['total_bits']} bit固定2bit total{f['total_bits']} bit"
 for text in [f"H≈{a['entropy_bits_per_symbol_approx']:.6f}",f"実message {a['message_length']}記号",'実payload平均='+str(a['actual_payload_mean'] or '未定義（空）'),f"payload {h['payload_bits']} vs {f['payload_bits']}bit",f"total差 {a['total_difference_bits']}bit",'誤判定検出='+str(a['wrong_claim_detected']).lower()]:assert text in s['stage'],text
 for text in [f"L={a['weighted_mean_length']}",f"totalは{h['total_bits']} / {f['total_bits']}bit",'固定header8bit、Huffman header16bit','codebook・bitstream・countのみ','原messageやweightsを受け取らず','両harness往復一致=true','空messageの実平均は未定義','標準format・速度・capacity達成・物理channelは未実証']:assert text in s['answer'],text
 assert len(s['table_rows'])==4
 for i,(c,row) in enumerate(zip('ABCD',s['table_rows'])):assert row['symbol']==c and row['cells']==[c,a['probabilities'][i],a['codebook'][c],str(a['lengths'][c]),str(a['symbol_counts'][c])]
 trace='木のmerge: '+' ; '.join(f"{m['left']}({m['left_weight']}) + {m['right']}({m['right_weight']}) → {m['merged_weight']}" for m in a['merge_trace'])+'。同weightは最小leaf alphabet順、codewordは長さ→alphabet順のcanonical。';assert s['tree']==trace
 lp,cp=s['plots'];assert lp['kind']=='length' and cp['kind']=='cost' and lp['svg_count']==cp['svg_count']==1;near(lp['hi'],4);assert len(lp['groups'])==4
 for i,g in enumerate(lp['groups']):
  c='ABCD'[i];n=a['lengths'][c];assert g['symbol']==c and g['code']==a['codebook'][c] and g['length']==str(n) and g['texts']==[str(n)+'bit',c+' '+a['codebook'][c]] and len(g['rects'])==1
  b=g['rects'][0];assert b['class']=='payload-bar';near(b['x'],54+100*i);near(b['y'],270-n*55);near(b['width'],48);near(b['height'],n*55)
 hi=max(h['total_bits'],f['total_bits'])+4;near(cp['hi'],hi);assert len(cp['groups'])==2
 for i,g in enumerate(cp['groups']):
  method=['fixed','huffman'][i];v=a[method];assert g['method']==method and g['total']==str(v['total_bits']) and g['texts']==[str(v['total_bits'])+'bit','固定2bit' if i==0 else 'Huffman'] and len(g['rects'])==2
  for part in ['payload','header']:
   b=next(b for b in g['rects'] if b['data-part']==part);assert b['class']==part+'-bar' and b['data-value']==str(v[part+'_bits']);near(b['x'],85+185*i);near(b['width'],80);near(b['y'],270-v['payload_bits' if part=='payload' else 'total_bits']/hi*220);near(b['height'],v[part+'_bits']/hi*220)
def main():
 before=snapshot();e=load(QA/'ui.json');rows=load(ROOT/'expected-table.json')['rows'];fixed={r['id']:r for r in rows};edits=load(QA/'edited-oracle-before-ui.json')['cases'];oracle={r['input_json']:r['expected'] for r in rows+edits};export=load(QA/'memory-receipts.json');assert export['mode']=='memory-only' and len(export['requests'])==110;by_id={r['request_id']:r for r in export['requests']};assert len(by_id)==110
 for raw in export['requests']:actual(raw,oracle[raw['input_json']])
 assert sum(r['revision']>=0 for r in export['requests'])==108
 assert len(e['matrix'])==60 and {(x['id'],x['pred']) for x in e['matrix']}=={(r['id'],p) for r in rows for p in ['','saved','equal','overhead','input']}
 for p in e['matrix']:assert p['state']['prediction']==p['pred'] and p['state']['input']==fixed[p['id']]['input_json'];display(p['state'],fixed[p['id']]['expected'],by_id)
 assert len(e['resets'])==17
 for p in e['resets']:
  opened(p['before']);display(p['before'],fixed['skew-short']['expected'],by_id);empty(p['after'])
  if p['kind']=='prediction':assert p['after']['prediction']==p['value'] and p['after']['input']==p['before']['input']
  else:assert p['after']['scenario']==p['value'] and p['after']['prediction']=='' and p['after']['input']==fixed[p['value']]['input_json']
 reset=e['explicit_reset'];opened(reset['before']);empty(reset['edited']);empty(reset['after']);assert reset['after']['input']==fixed['skew-short']['input_json'] and reset['after']['prediction']=='' and reset['edited']['input']=='edited'
 assert len(e['edited'])==8
 for p,o in zip(e['edited'],edits):
  assert p['id']==o['id'] and p['expected']==o['expected'];opened(p['before']);empty(p['reset']);assert p['reset']['input']==o['input_json'];display(p['state'],o['expected'],by_id)
  assert datetime.datetime.fromisoformat(load(QA/'edited-oracle-before-ui.json')['created_utc'])<datetime.datetime.fromisoformat(json.loads(p['state']['trace'])['request_utc'])
 one=e['one_operation'];display(one['before'],fixed['skew-short']['expected'],by_id);empty(one['reset']);display(one['after'],fixed['skew-long']['expected'],by_id);pre=json.loads(one['before']['input']);post=json.loads(one['after']['input']);assert post==dict(pre,message=pre['message']*5)
 assert len(e['stale'])==4 and {p['kind'] for p in e['stale']}=={'prediction','scenario','input','reset'}
 for p in e['stale']:opened(p['before']);empty(p['reset']);empty(p['after']);assert p['reset']==p['after'] and p['elapsed_ms']>=600 and '計算中' in p['pending']['message'] and p['pending']['compare_disabled']
 opened(e['host_before']);display(e['host_before'],fixed['skew-short']['expected'],by_id);empty(e['host_after']);assert '実行/通信失敗' in e['host_after']['message'] and e['host_after']['input']==e['host_before']['input']
 assert len(e['captures'])==3
 for p in e['captures']:
  b=(QA/p['file']).read_bytes();assert b[:2]==b'\xff\xd8' and len(b)>20000;display(p['state'],oracle[p['state']['input']],by_id);assert p['state']['scroll_width']<=p['state']['width'] and p['state']['answer_open']
  if p['file'].startswith('mobile'):assert p['state']['width']==390
 mapping={'view/readme':ROOT/'README.md','view/calculate':ROOT/'calculate.py','view/checker':ROOT/'checker.py','view/hand':ROOT/'hand-oracle.json','view/coverage':ROOT/'COVERAGE.md','view/skill':ROOT/'skills/atlas-huffman-payload-header-cost/SKILL.md','view/parent-path':ROOT/'../../../subjects/information-theory-coding/LEARNING_PATH.md'};assert len(e['local_navigation'])==9
 for p in e['local_navigation']:
  if p['href'] in mapping:assert p['body']==mapping[p['href']].read_text()
  elif p['href']=='view/fixed-raw':assert json.loads(p['body'])==load(ROOT/'observations'/e['run_id']/'raw.json')
  else:raw=json.loads(e['link_raw_before']['trace']);assert json.loads(p['body'])==raw==by_id[raw['request_id']]
 assert 'resources/mit6_02f12_chap03/' in e['primary_navigation'][0]['url'] and 'Huffman' in e['primary_navigation'][0]['snapshot']
 http=load(QA/'http-links.json');assert http['unit_unchanged'] and http['health']['mode']=='memory-only' and http['health']['request_count']==110
 for p in http['links']:assert p['status']==(404 if p['path']=='view/not-listed' else 200)
 setup=load(QA/'memory-http-check.json');assert setup['unit_sha_mtime_unchanged']
 for p in setup['get_rows']:assert p['status']==(404 if p['path']=='view/not-listed' else 200)
 for raw in setup['requests']:assert raw==by_id[raw['request_id']] and raw['revision']<0
 prior=load(ROOT/'qa/oracle-before-producer.json');assert prior['producer_exists'] is False and digest(ROOT/'hand-oracle.json')==prior['hand_sha256'] and digest(ROOT/'expected-table.json')==prior['expected_sha256']
 receiver=load(QA/'receiver-boundaries.json');assert receiver['exit']==0 and receiver['stderr']=='' and json.loads(receiver['stdout'])==receiver['result'];v=receiver['result'];assert v['roundtrips_both']==682 and v['messages_all_ABCD_length_0_to_4']==341 and len(v['boundary_rejected'])==13 and v['decoder_parameters']==['codebook','bitstream','count'] and v['unit_sha_mtime_unchanged'];flip=v['valid_bitflip_counterexample'];assert flip['decoded']=='AAAABBCC' and flip['receiver_accepts'] and flip['original']=='AAAABBCD'
 cleanup=load(QA/'cleanup.json');assert not cleanup['ports_after']['51987'] and not cleanup['ports_after']['51839'] and all(cleanup['ports_after'][p] for p in ['53478','60285','50835']) and cleanup['server_closed'] and cleanup['memory_receipts_discarded']==110 and cleanup['files_recorded']==0 and cleanup['owned_tab_closed']=='55' and cleanup['viewport_reset']
 assert e['cleanup']=={k:cleanup[k] for k in e['cleanup']} and load(QA/'server-session.json')['record_only'] is False and load(QA/'toolchain.json')['installed'] is False
 if (QA/'artifact-index.json').exists():
  idx=load(QA/'artifact-index.json');assert idx['excludes_self'] and idx['excludes_future_verification']
  for n,sha in idx['files'].items():assert digest(ROOT/n)==sha,n
 assert before==snapshot(),'QA mutated unit';print(json.dumps({'matrix':60,'select_resets':17,'explicit_reset':True,'edited':8,'one_operation_message':True,'stale':4,'UI_POST':108,'total_memory_receipts':110,'captures':3,'clicked_local_viewers':9,'MIT_clicked':True,'independent_13_assignment_oracle':True,'receiver_negative':13,'receiver_roundtrips':682,'bitflip_valid_counterexample':True,'readonly_GET_POST_export':True,'unit_sha_mtime_unchanged':True}))
if __name__=='__main__':main()
