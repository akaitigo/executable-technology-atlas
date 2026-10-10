import json,hashlib,datetime,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def core(raw,c,lit):
 assert json.loads(raw['input_json'])==c['input'] and raw['stderr']=='' and json.loads(raw['stdout'])==raw['result'];check(raw['result'],c['input'],lit);assert raw['exit']==(0 if raw['result']['status']=='OBSERVED' else 2 if raw['result']['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for n,h in raw['source_sha256'].items():assert sha(P/n)==h,n
 if raw['result']['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True) and json.loads(a['stdin'])==dict(input=c['input'],result=raw['result'])
 else:assert raw['audit'] is None

def blank(o):assert o['status']=='未実行' and o['raw'] is None and not o['results_visible'] and not o['answer_visible'] and not o['answer_open'] and o['answer']=='' and o['counts']=='' and o['digests']=='' and o['test_table']==[] and o['points']==[] and o['facts']==[]
def ui(o,c,lit):
 assert o['raw']['raw']==o['raw']['receipt'];raw=o['raw']['raw'];core(raw,c,lit);r=raw['result'];assert o['status']==r['status']
 if r['status']!='OBSERVED':assert not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['points']==[] and o['facts']==[] and o['test_table']==[];return
 assert o['answer_open'] and o['answer_visible'] and o['results_visible'];v=lambda x:str(x).lower() if isinstance(x,bool) else str(x);compact=lambda x:json.dumps(x,separators=(',',':'))
 assert o['counts']=='decision='+r['decision']+' / behavior verified='+v(r['behaviorVerified'])+' / action effective='+v(r['actionEffective'])+' / 実test子process='+str(r['testsExecuted'])+' / missing='+compact(r['missingTests'])
 assert o['facts']==[dict(fact=k,value=v(value)) for k,value in [('done',r['input']['action_done']),('matches',r['matchesCurrent']),('complete',r['completeSuite']),('decision',r['decision'])]]
 assert o['points']==[dict(generation=g,test=t['id'],build=r[g]['build'],passed=v(t['passed'])) for g in ['evidence','current'] if r[g] for t in r[g]['tests']]
 expected=[(g,r[g],t) for g in ['evidence','current'] if r[g] for t in r[g]['tests']];assert len(o['test_table'])==len(expected)
 for cells,(g,record,t) in zip(o['test_table'],expected):assert cells[:3]==[g,record['build'],t['id']] and json.loads(cells[3])==t['expected'] and json.loads(cells[4])==t['actual'] and cells[5:]==[str(t['exit']),'PASS' if t['passed'] else 'FAIL']
 assert r['currentSourceDigest'] in o['digests']
 if r['evidence']:assert r['evidence']['source_sha256'] in o['digests']
 for text in ['current='+r['input']['current_build'],'action_done='+v(r['input']['action_done']),'evidence='+str(r['input']['evidence_build'] or 'null'),'retest='+v(r['input']['retest']),'decision='+r['decision'],'matchesCurrent='+v(r['matchesCurrent']),'completeSuite='+v(r['completeSuite']),'allPassed='+v(r['allPassed']),'behaviorVerified='+v(r['behaviorVerified']),'actionEffective='+v(r['actionEffective']),'missing='+compact(r['missingTests']),'本番有効性/人の承認=UNCONFIRMED']+[g+': '+('build='+r[g]['build']+', failed='+compact(r[g]['failed'])+', passed='+compact(r[g]['passed']) if r[g] else '未実行')+'。' for g in ['current','evidence']]:assert text in o['answer'],text

def browser(b):
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json');assert len(b['cases'])==20
 for o,c in zip(b['cases'],cs):assert o['id']==c['id'];ui(o,c,lits.get(c['id'],c.get('literal')))
 for k in ['prediction-action','prediction-proof','input-json']:
  q=b['reset'][k];assert q['before']['answer_open'] and q['before']['answer'];blank(q['after']);idx=['prediction-action','prediction-proof','input-json'].index(k)
  for i in range(3):assert q['after']['inputs'][i]==(q['new_value'] if i==idx else q['before']['inputs'][i])
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['','','']
 r=b['invalid_json'];assert r['status']=='INPUT_REFUSED' and r['raw']['raw']['result']['reason']=='JSON' and not r['answer_visible'] and not r['results_visible'] and r['answer']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and 'HTTP 503' in f['raw']['reason'] and not f['answer_visible'] and not f['results_visible'] and f['answer']=='' and f['points']==[]
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2';assert b['console']==[]
def verify():
 q=read('evidence/current.json');f=P/'evidence'/q['raw'];assert sha(f)==q['sha256'];report=json.loads(f.read_text());assert report['status']=='passed' and report['failures']==[] and len(report['attempts'])==20;cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json')
 for a,c in zip(report['attempts'],cs):assert a['id']==c['id'];core(a['raw'],c,lits.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser(b)
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 contract=read('evidence/contract-before-producer.json');assert contract['fixture_mtime_max_ns']<contract['producer_initial_mtime_ns']
 for n,d in contract['files'].items():assert sha(P/n)==d['sha256']
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 children=sum(a['raw']['result'].get('testsExecuted',0) for a in report['attempts']);print(json.dumps(dict(status='passed',fixed=17,editable=3,ui=20,actual_build_test_children=children,approval='UNCONFIRMED',productionEffectiveness='UNCONFIRMED',subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
