import json,hashlib,datetime,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def core(raw,c,lit):
 assert json.loads(raw['input_json'])==c['input'];assert raw['stderr']=='' and json.loads(raw['stdout'])==raw['result'];check(raw['result'],c['input'],lit)
 assert raw['exit']==(0 if raw['result']['status']=='OBSERVED' else 2 if raw['result']['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for n,h in raw['source_sha256'].items():assert sha(P/n)==h,n
 if raw['result']['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True) and json.loads(a['stdin'])==dict(input=c['input'],result=raw['result'])
 else:assert raw['audit'] is None

def blank(o):
 assert o['status']=='未実行' and o['raw'] is None and not o['results_visible'] and not o['answer_visible'] and not o['answer_open'] and o['answer']=='' and o['counts']=='' and o['reach_table']==[] and o['proof_table']==[] and o['edges']==[] and o['nodes']==[] and o['baseline']==''
def ui(o,c,lit):
 assert o['raw']['raw']==o['raw']['receipt'];raw=o['raw']['raw'];core(raw,c,lit);r=raw['result'];assert o['status']==r['status']
 if r['status']!='OBSERVED':assert not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['edges']==[] and o['nodes']==[] and o['reach_table']==[] and o['proof_table']==[];return
 assert o['results_visible'] and o['answer_visible'] and o['answer_open'];v=lambda b:str(b).lower()
 assert o['counts']=='graph再計算='+v(r['recompute'])+' / 旧cache適用='+v(r['oldCacheApplicable'])+' / trace完備='+v(r['traceComplete'])+' / 実test再実行=false / 承認=UNCONFIRMED'
 assert o['reach_table']==[[id,','.join(r['oldReach'][id]),','.join(r['newReach'][id])] for id in ['R-CAP','R-FIFO']]
 compact=lambda a:json.dumps(a,separators=(',',':'))
 assert o['proof_table']==[[p['test'],p['storedResult'] or 'なし',p['status'],','.join(p['ancestors']),compact(p['missing'])] for p in r['proofs']]
 assert o['edges']==[dict(generation=g,source=e['source'],target=e['target'],rev=str(e['rev'])) for g in ['old','new'] for e in c['input'][g]['links']]
 assert o['nodes']==[dict(generation=g,id=n['id'],rev=str(n['rev'])) for g in ['old','new'] for n in c['input'][g]['nodes']]
 for text in ['graph再計算='+v(r['recompute']),'旧cache適用='+v(r['oldCacheApplicable']),'旧到達='+compact(r['oldReach']),'新到達='+compact(r['newReach']),'impact='+compact(r['impact']),'missing='+compact(r['missing']),'実test再実行=false、承認=UNCONFIRMED']+[p['test']+': '+p['status']+' / stored='+str(p['storedResult'] or 'null')+' / ancestors='+compact(p['ancestors'])+' / missing='+compact(p['missing'])+'。' for p in r['proofs']]:assert text in o['answer'],text
 for d in [r['oldGraphDigest'],r['newGraphDigest']]+[p[k] for p in r['proofs'] for k in ['storedDigest','currentDigest'] if p[k]]:assert d in o['baseline']

def browser(b):
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json');assert len(b['cases'])==26
 for o,c in zip(b['cases'],cs):assert o['id']==c['id'];ui(o,c,lits.get(c['id'],c.get('literal')))
 for k in ['prediction-graph','prediction-proof','input-json']:
  reset=b['reset'][k];assert reset['before']['answer_open'] and reset['before']['answer'];blank(reset['after']);idx=['prediction-graph','prediction-proof','input-json'].index(k)
  for i in range(3):assert reset['after']['inputs'][i]==(reset['new_value'] if i==idx else reset['before']['inputs'][i])
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['','','']
 r=b['invalid_json'];assert r['status']=='INPUT_REFUSED' and r['raw']['raw']['result']['reason']=='JSON' and not r['answer_visible'] and not r['results_visible'] and r['answer']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and 'HTTP 503' in f['raw']['reason'] and not f['answer_visible'] and not f['results_visible'] and f['answer']=='' and f['edges']==[]
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2';assert b['console']==[]

def verify():
 pointer=read('evidence/current.json');f=P/'evidence'/pointer['raw'];assert sha(f)==pointer['sha256'];report=json.loads(f.read_text());assert report['status']=='passed' and report['failures']==[] and len(report['attempts'])==26
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json')
 for a,c in zip(report['attempts'],cs):assert a['id']==c['id'];core(a['raw'],c,lits.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser(b)
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 contract=read('evidence/contract-before-producer.json');assert contract['fixture_mtime_max_ns']<contract['producer_initial_mtime_ns']
 for n,d in contract['files'].items():assert sha(P/contract['snapshot']/n)==d['sha256']
 for n,h in read('revisions/before-ancestor-clarification/manifest.json').items():assert sha(P/'revisions/before-ancestor-clarification'/n)==h
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',fixed=22,editable=4,ui=26,initial_failure_preserved=(P/'evidence/initial-build-failure.json').exists(),testsExecuted=False,approval='UNCONFIRMED',subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
