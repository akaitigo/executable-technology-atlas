import json,hashlib,datetime,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
KEYS=['prediction-return','prediction-freshness','ttl-override','policy-override','input-json']
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def val(x):return 'null' if x is None else str(x).lower() if type(x)==bool else str(x)
def core(raw,c,lit):
 assert json.loads(raw['input_json'])==c['input'] and raw['stderr']=='' and json.loads(raw['stdout'])==raw['result'];r=json.loads(raw['stdout']);check(r,c['input'],lit)
 assert raw['exit']==(0 if r['status']=='OBSERVED' else 2 if r['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for n,h in raw['source_sha256'].items():assert sha(P/n)==h,n
 if r['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True) and json.loads(a['stdin'])==dict(input=c['input'],result=r)
 else:
  assert raw['audit'] is None
  if r['status']=='INPUT_REFUSED':assert not r['sql_executed']
 return r
def blank(o):assert o['status']=='未実行' and o['raw'] is None and not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['stats']=='' and o['step']=='' and o['client'] is None and o['harness'] is None and o['sql'] is None and o['timeline']==[] and o['nodes']==[]
def ui(o,c,lit,index=None):
 assert o['raw']['raw']==o['raw']['receipt'];r=core(o['raw']['raw'],c,lit);assert o['status']==r['status']
 if r['status']!='OBSERVED':assert not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['nodes']==[] and o['timeline']==[];return
 assert o['answer_visible'] and o['answer_open'] and o['results_visible']
 assert o['stats']=='ttl='+str(r['ttl'])+' / policy='+r['policy']+' / '+compact(r['stats'])
 idx=max(0,len(r['steps'])-1) if index is None else index;s=r['steps'][idx] if r['steps'] else None
 assert o['step']==('event '+str(idx)+' / t='+str(s['event']['t'])+' / '+s['event']['op'] if s else 'eventなし / 空cache')
 assert o['client']==(s['client'] if s else None) and o['harness']==(s['harness'] if s else None)
 assert o['sql']==(dict(sql=s['sql'],trace=s['trace']) if s else dict(startup=r['startup_trace'],final_source_rows=r['final_source_rows']))
 rows=[];nodes=[]
 for s in r['steps'][:idx+1]:
  rows.append([str(s['event']['t'])+'/'+s['event']['op'],compact(s['source_rows']),compact(s['cache_after']),compact(s['client']['returned']),s['client']['result']+'/'+val(s['client']['authoritative_freshness']),val(s['harness']['version_stale'])+'/'+val(s['harness']['value_stale'])])
  nodes.append(dict(index=str(s['index']),t=str(s['event']['t']),kind=s['client']['result'],sourceVersion=str(s['harness']['source_version']),cacheVersion=val(s['cache_after']['version'] if s['cache_after'] else None),returnVersion=val(s['client']['returned']['version'] if s['client']['returned'] else None),expires=val(s['cache_after']['expires_at'] if s['cache_after'] else None),harnessStale=val(s['harness']['version_stale'])))
 assert o['timeline']==rows and o['nodes']==nodes and o['previous_disabled']==(idx==0) and o['next_disabled']==(idx>=len(r['steps'])-1)
 for t in ['実入力ttl='+str(r['ttl'])+', policy='+r['policy'],compact(r['stats']),'最終source='+compact(r['final_source_rows']),'最終cache='+compact(r['final_cache']),'予想return='+compact(o['inputs'][0]),'予想鮮度='+compact(o['inputs'][1]),'harness auditをcacheの未受信情報へ流用しない','fake時刻は実clockではない','refill期限はそのfake時刻+TTL']:assert t in o['answer'],t
def browser(b):
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json');assert len(b['cases'])==19
 for o,c in zip(b['cases'],cs):assert o['id']==c['id'];ui(o,c,lits.get(c['id'],c.get('literal')))
 for o in b['event_steps']:ui(o,cs[0],lits['strict-timeline'],o['index'])
 assert [o['index'] for o in b['event_steps']]==[2,3]
 stale=b['event_steps'][0];assert stale['inputs'][:2]==['t4 blue/v2','TTL内なら常にfresh'] and stale['client']['returned']==dict(value='red',version=1) and stale['harness']['version_stale'] and stale['client']['authoritative_freshness']=='UNOBSERVED_ON_HIT'
 ui(b['policy_override'],cs[1],lits['inclusive-timeline']);assert b['policy_override']['inputs'][3]=='inclusive'
 for i,k in enumerate(KEYS):
  v=b['reset'][k];assert v['before']['answer_open'];blank(v['after']);assert v['after']['inputs']==[v['new_value'] if j==i else v['before']['inputs'][j] for j in range(5)]
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['']*5
 f=b['invalid_json'];assert f['status']=='INPUT_REFUSED' and f['raw']['raw']['result']==dict(status='INPUT_REFUSED',reason='JSON',sql_executed=False) and not f['answer_visible'] and f['answer']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and f['raw']==dict(reason='HTTP 503') and not f['answer_visible'] and not f['results_visible'] and f['answer']=='' and f['nodes']==[]
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2'
 assert b['console']==[] and len(b['primary_links'])==3
def verify():
 p=read('evidence/current.json');f=P/'evidence'/p['raw'];assert sha(f)==p['sha256'];report=json.loads(f.read_text());assert report['status']=='passed' and report['failures']==[] and len(report['attempts'])==19
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json')
 for a,c in zip(report['attempts'],cs):assert a['id']==c['id'];core(a['raw'],c,lits.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser(b)
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 c=read('evidence/contract-before-producer.json');assert c['fixture_mtime_max_ns']<c['producer_initial_mtime_ns']
 for n,v in c['files'].items():assert sha(P/n)==v['sha256']
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',fixed=15,editable=4,ui=19,policy_override=1,event_steps=2,SQL='actual-memory',clock='fake',productionGuarantee='UNCONFIRMED',subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
