import json,hashlib,datetime,sys
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def core(raw,c,lit):
 assert json.loads(raw['input_json'])==c['input'] and raw['stderr']=='' and json.loads(raw['stdout'])==raw['result'];check(raw['result'],c['input'],lit)
 assert raw['exit']==(0 if raw['result']['status']=='OBSERVED' else 2 if raw['result']['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for n,h in raw['source_sha256'].items():assert sha(P/n)==h,n
 if raw['result']['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True) and json.loads(a['stdin'])==dict(input=c['input'],result=raw['result'])
 else:assert raw['audit'] is None

def blank(o):
 assert o['status']=='未実行' and o['raw'] is None and not o['results_visible'] and not o['answer_visible'] and not o['answer_open'] and o['answer']=='' and o['counts']=='' and o['thresholds']=='' and o['decision_table']==[] and o['sample_table']==[] and o['points']==[] and o['deadlines']==[] and o['excluded']==''
def ui(o,c,lit):
 assert o['raw']['raw']==o['raw']['receipt'];raw=o['raw']['raw'];core(raw,c,lit);r=raw['result'];actual_input=json.loads(raw['input_json']);assert o['status']==r['status']
 if r['status']!='OBSERVED':assert not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['answer']=='' and o['points']==[] and o['deadlines']==[] and o['decision_table']==[] and o['sample_table']==[];return
 assert o['results_visible'] and o['answer_visible'] and o['answer_open'];compact=lambda x:json.dumps(x,separators=(',',':'));val=lambda x:'未観測' if x is None else str(x).lower() if isinstance(x,bool) else str(x)
 assert o['thresholds']=='R-CORRECT: 正答数/3 >= accuracy_bp/10000。R-TIMELY: 全elapsed <= deadline_ms。旧='+compact(actual_input['old'])+' / 新='+compact(actual_input['new'])
 assert o['counts']=='旧受入='+compact(r['accepted']['old'])+' / 新受入='+compact(r['accepted']['new'])+' / 変化='+compact(r['changed'])+' / Pareto='+compact(r['pareto'])+' / dominance='+compact(r['dominance'])
 assert o['excluded']=='不足/未観測でPareto除外='+compact(r['excluded'])
 table=[]
 for row in r['rows']:
  m=row['metrics'];table.append([row['id'],str(m['correct_count'])+'/'+str(m['observed_outputs']),str(m['observed_times']),val(m['accuracy_bp']),val(m['worst_ms']),row['old']['R_CORRECT']+'/'+row['old']['R_TIMELY'],row['old']['acceptance'],row['new']['R_CORRECT']+'/'+row['new']['R_TIMELY'],row['new']['acceptance'],'front' if row['id'] in r['pareto'] else 'dominated' if m['eligible'] else '未観測除外'])
 assert o['decision_table']==table
 assert o['sample_table']==[[row['id']]+[val(s[k]) for k in ['sample','present','expected','output','elapsed_ms','correct']] for row in r['rows'] for s in row['samples']]
 assert o['points']==[dict(id=row['id'],correct=str(row['metrics']['correct_count']),worst=str(row['metrics']['worst_ms']),front=str(row['id'] in r['pareto']).lower(),acceptance=row['new']['acceptance']) for row in r['rows'] if row['metrics']['eligible']]
 assert o['deadlines']==[dict(generation=k,deadline=str(r['thresholds'][k]['deadline_ms'])) for k in ['old','new']]
 for s in ['実入力 old='+compact(actual_input['old'])+' / new='+compact(actual_input['new']),'旧受入='+compact(r['accepted']['old']),'新受入='+compact(r['accepted']['new']),'変化='+compact(r['changed']),'Pareto='+compact(r['pareto']),'dominance='+compact(r['dominance']),'除外='+compact(r['excluded']),'正しさAND期限','製品test再実行=false、承認/実利用validation=UNCONFIRMED']+[row['id']+': old='+row['old']['acceptance']+', new='+row['new']['acceptance']+', quality='+row['new']['R_CORRECT']+', time='+row['new']['R_TIMELY']+', correct='+str(row['metrics']['correct_count'])+'/3, observed='+str(row['metrics']['observed_outputs'])+'/'+str(row['metrics']['observed_times'])+', worst='+str(row['metrics']['worst_ms'] if row['metrics']['worst_ms'] is not None else 'null')+'。' for row in r['rows']]:assert s in o['answer'],s

def browser(b):
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json');assert len(b['cases'])==24
 for o,c in zip(b['cases'],cs):assert o['id']==c['id'];ui(o,c,lits.get(c['id'],c.get('literal')))
 for k in ['prediction-acceptance','prediction-pareto','input-json']:
  reset=b['reset'][k];assert reset['before']['answer_open'] and reset['before']['answer'];blank(reset['after']);idx=['prediction-acceptance','prediction-pareto','input-json'].index(k)
  for i in range(3):assert reset['after']['inputs'][i]==(reset['new_value'] if i==idx else reset['before']['inputs'][i])
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['','','']
 r=b['invalid_json'];assert r['status']=='INPUT_REFUSED' and r['raw']['raw']['result']['reason']=='JSON' and not r['answer_visible'] and not r['results_visible'] and r['answer']==''
 f=b['communication_failure'];assert f['status']=='COMMUNICATION_FAILURE' and 'HTTP 503' in f['raw']['reason'] and not f['answer_visible'] and not f['results_visible'] and f['answer']=='' and f['points']==[]
 s=b['stale'];assert s['before_release']['raw']==s['after_release']['raw'] and s['before_release']['answer']==s['after_release']['answer'] and s['after_release']['ignored']=='古い結果の無視: 1';blank(s['edit_after_release']);assert s['edit_after_release']['ignored']=='古い結果の無視: 2';assert b['console']==[]
def verify():
 pointer=read('evidence/current.json');f=P/'evidence'/pointer['raw'];assert sha(f)==pointer['sha256'];report=json.loads(f.read_text());assert report['status']=='passed' and report['failures']==[] and len(report['attempts'])==24
 cs=read('fixture.json')+read('custom-oracle.json');lits=read('oracle.json')
 for a,c in zip(report['attempts'],cs):assert a['id']==c['id'];core(a['raw'],c,lits.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser(b)
 for n,t in b['documents'].items():assert (P/n).read_text()==t,n
 contract=read('evidence/contract-before-producer.json');assert contract['fixture_mtime_max_ns']<contract['producer_initial_mtime_ns']
 for n,d in contract['files'].items():assert sha(P/n)==d['sha256']
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',fixed=20,editable=4,ui=24,measurementSource='synthetic-fixture',approval='UNCONFIRMED',validation='UNCONFIRMED',subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:(P/'evidence/binding.json').write_text(json.dumps({str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'},indent=2)+'\n')
 else:verify()
