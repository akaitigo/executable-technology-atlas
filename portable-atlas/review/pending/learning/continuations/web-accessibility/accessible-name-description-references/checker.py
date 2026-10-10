import json,hashlib,datetime,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent
LITERAL=[('visible','保存',''),('aria-label','送信',''),('labelledby','優先ラベル',''),('describedby','保存','端末へ保存'),('hidden-label','非表示ラベル',''),('hidden-description','保存','非表示の補足'),('unreferenced-hidden','保存',''),('visible-ref-hidden-child','表ラベル',''),('hidden-ref-hidden-child','隠し親 隠し子',''),('reference-order','第二 第一',''),('broken-reference','代替名',''),('unnamed-operable','','名前を付ける必要')]
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def blank(o):assert o['status']=='未実行' and o['raw'] is None and o['answer']=='' and not o['answer_visible'] and not o['answer_open']
def audit(r,b):
 fixtures=read('fixture.json');oracle=read('oracle.json');assert len(r['cases'])==len(b['cases'])==12
 for n,h in r['source_sha256'].items():assert sha(P/n)==h,n
 assert datetime.datetime.fromisoformat(r['completed'].replace('Z','+00:00'))>=datetime.datetime.fromisoformat(r['started'].replace('Z','+00:00'))
 assert r['environment']['browser']=='Codex In-app Browser' and r['environment']['browser_version']=='UNOBSERVED'
 for (cid,name,desc),c,o,u in zip(LITERAL,fixtures,r['cases'],b['cases']):
  assert cid==c['id']==o['id']==u['id'];assert oracle[cid]['name']==name and oracle[cid]['description']==desc
  assert o['dom']['html'].replace(' hidden=""',' hidden')==c['html'];assert o['name']==dict(status='OBSERVED_ROLE_QUERY',value=name,method='exact candidate query and native AX snapshot')
  assert o['queries'][name]==1 and o['queries']['不一致の候補']==0
  for candidate,count in o['queries'].items():assert count==(1 if candidate==name else 0)
  assert re.search(r'^\s+\d+ button'+(' '+re.escape(name) if name else '')+r'$',o['nativeAX'],re.M),cid
  assert o['description']==dict(status='UNOBSERVED',value=None) and o['clicks']=='操作回数: 1'
  assert o['prediction']['name']==o['dom']['visibleText'] and o['prediction']['name_match']==(o['prediction']['name']==name) and o['prediction']['description_verdict']=='UNOBSERVED'
  raw=u['raw'];assert raw==dict(fixture=c,expected=oracle[cid],observation=o,source_sha256=r['source_sha256']);assert u['status']=='SAVED_OBSERVATION' and u['answer_visible'] and u['answer_open']
  for s in ['条件='+cid,'期待name='+json.dumps(name,ensure_ascii=False),'観測name='+json.dumps(name,ensure_ascii=False),'期待description='+json.dumps(desc,ensure_ascii=False),'観測description=UNOBSERVED (null)','保存済み観測の再表示','現在の端末のAX計算を実行した値ではない','名前の予想='+json.dumps(u['inputs'][0],ensure_ascii=False),'説明の予想='+json.dumps(u['inputs'][1],ensure_ascii=False)]:assert s in u['answer'],s
 for i,k in enumerate(['prediction-name','prediction-description']):
  v=b['reset'][k];assert v['before']['answer_open'];blank(v['after']);assert v['after']['inputs']==['編集後' if j==i else v['before']['inputs'][j] for j in range(2)]
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['',''] and b['condition_reset']['clicks']=='操作回数: 0'
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and f['raw']==dict(reason='HTTP 503') and f['answer']=='' and not f['answer_visible'] and not f['answer_open']
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2'
 assert b['console']==[]
 assert len(b['primary_links'])==2 and all(x['heading_found'] and x['title']=='Accessible Name and Description Computation 1.2' and '/2026/WD-accname-1.2-20261002/#' in x['url'] for x in b['primary_links'])
def verify():
 r=read('evidence/observations.json');b=read('evidence/browser.json');audit(r,b)
 cap=read('evidence/capability.json');assert cap['name_role_query_count']==1 and cap['visible_text_role_query_count']==0 and cap['description']['status']=='UNOBSERVED' and cap['description']['value'] is None and not cap['nativeAX_contains_description']
 c=read('evidence/contract-before-producer.json');assert c['fixture_mtime_max_ns']<c['producer_initial_mtime_ns']
 for n,v in c['files'].items():assert sha(P/n)==v['sha256']
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',name_conditions=12,clicks=12,ui=12,description_observed=0,description_unobserved=12,wrong_predictions=sum(not o['prediction']['name_match'] for o in r['cases']),AT='UNRUN',WCAG='UNASSESSED')))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
