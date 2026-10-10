import json,sys,hashlib,datetime
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
def read(n):return json.loads((P/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def core(raw,x,literal):
 assert raw['input_json']==json.dumps(x) or json.loads(raw['input_json'])==x
 assert json.loads(raw['stdout'])==raw['result'] and raw['stderr']==''
 check(raw['result'],x,literal);assert raw['exit']==(0 if raw['result']['status']=='OBSERVED' else 2 if raw['result']['status']=='INPUT_REFUSED' else 1)
 assert datetime.datetime.fromisoformat(raw['completed'])>=datetime.datetime.fromisoformat(raw['started'])
 for f,h in raw['source_sha256'].items():assert sha(P/f)==h,f
 if raw['result']['status']=='OBSERVED':
  a=raw['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])==dict(status='passed',independent=True)
  assert json.loads(a['stdin'])==dict(input=x,result=raw['result'])
 else:assert raw['audit'] is None
FIELDS=['counts','diagram','event-table','trace-table','answerbody','raw']
def blank(o):
 assert o['status']=='未実行' and o['raw'] is None and o['answer']=='' and not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['event_table']==[] and o['trace_table']==[] and o['bars']==[] and o['drops']==[] and o['counts']==''
def ui_state(o,c,literal):
 assert o['raw']['raw']==o['raw']['receipt'];raw=o['raw']['raw'];core(raw,c['input'],literal);r=raw['result'];assert o['status']==r['status']
 if r['status']!='OBSERVED':assert o['answer']=='' and not o['answer_visible'] and not o['answer_open'] and not o['results_visible'] and o['event_table']==[] and o['trace_table']==[];return
 assert o['answer_visible'] and o['results_visible']
 counts=r['counts'];assert o['counts']==f"到着{counts['arrived']} / 受入{counts['accepted']} / drop{counts['dropped']} / 実完了{counts['completed']} / 未完了{counts['unfinished']} / 報告完了{len(r['reportedCompleted'])}"
 assert o['bars']==[dict(id=e['id'],start=str(e['start']),end=str(min(e['plannedEnd'],r['input']['horizon'])),planned=str(e['plannedEnd']),completed=str(e['state']=='COMPLETED').lower()) for e in r['events'] if e['start'] is not None]
 assert o['drops']==r['dropped']
 def val(v):return '未観測' if v is None else ','.join(v) or '—' if isinstance(v,list) else str(v)
 assert o['event_table']==[[val(e[k]) for k in ['id','arrival','priority','service','state','start','plannedEnd','end','wait','response']] for e in r['events']]
 assert o['trace_table']==[[str(t['tick'])]+[val(t[k]) for k in ['arrivals','accepted','dropped','completed','started','queue']]+[t['running']['id']+'/'+str(t['running']['remaining']) if t['running'] else 'idle',str(t['counts']['accepted']),str(t['counts']['completed']),str(t['reportedCompleted'])] for t in r['trace']]
 compact=lambda x:json.dumps(x,separators=(',',':'))
 for s in [f"horizon={r['input']['horizon']}",f"capacity={r['input']['capacity']}",f"policy={r['input']['policy']}",'受入ID='+compact(r['accepted']),'drop ID='+compact(r['dropped']),'実完了順='+compact(r['completed']),'報告完了='+compact(r['reportedCompleted'])]:assert s in o['answer'],s
 for e in r['events']:
  s=e['id']+': '+e['state']+', '+', '.join(k+'='+str(e[k] if e[k] is not None else '未観測') for k in ['start','plannedEnd','end','wait','response'])+'。';assert s in o['answer'],s
 assert '実IRQ/RTOS/WCET/Safety保証ではない' in o['answer']
def browser_verify(b):
 fixtures=read('fixture.json');custom=read('custom-oracle.json');literal=read('oracle.json');assert len(b['cases'])==len(fixtures)+len(custom)==23
 for obs,c in zip(b['cases'],fixtures+custom):assert obs['id']==c['id'];ui_state(obs,c,literal.get(c['id'],c.get('literal')))
 for key in ['prediction-complete','prediction-drop','input-json']:
  before=b['reset'][key]['before'];after=b['reset'][key]['after'];assert before['answer_open'] and before['answer'];blank(after);assert b['reset'][key]['passed']
 blank(b['condition_reset']);assert b['condition_reset']['inputs']==['','','']
 assert b['invalid_json']['status']=='INPUT_REFUSED' and not b['invalid_json']['answer_visible'] and b['invalid_json']['answer']==''
 failure=b['communication_failure'];assert failure['status']=='COMMUNICATION_FAILURE' and failure['answer']=='' and not failure['answer_visible'] and not failure['results_visible'] and failure['bars']==[] and 'HTTP 503' in failure['raw']['reason']
 assert b['stale']['old_ignored'] and b['stale']['new_retained'] and b['stale']['edit_old_ignored'];assert b['console']==[]
def verify():
 current=read('evidence/current.json');path=P/'evidence'/current['raw'];assert sha(path)==current['sha256'];report=json.loads(path.read_text());assert report['status']=='passed' and report['failures']==[]
 fixtures=read('fixture.json');custom=read('custom-oracle.json');literal=read('oracle.json');assert len(report['attempts'])==23
 for attempt,c in zip(report['attempts'],fixtures+custom):assert attempt['id']==c['id'];core(attempt['raw'],c['input'],literal.get(c['id'],c.get('literal')))
 b=read('evidence/browser.json');browser_verify(b)
 for n,t in b['documents'].items():
  target=P/n
  assert target.read_text()==t,n
 initial=read('evidence/run-20261005T172146-f42484d5.json');assert initial['status']=='failed' and initial['failures']==[dict(id='accepted-fault',failure='independent or literal mismatch')]
 manifest=read('revisions/initial-horizon-literal/manifest.json')
 for n,h in manifest.items():assert sha(P/'revisions/initial-horizon-literal'/n)==h
 for n,h in read('evidence/binding.json').items():assert sha(P/n)==h,n
 print(json.dumps(dict(status='passed',fixed=18,editable=5,actual_model_children=23,actual_UI_cases=23,initial_failure_preserved=True,subject_complete=False)))
if __name__=='__main__':
 if sys.argv[1:]==['--record-binding']:
  files={str(f.relative_to(P)):sha(f) for f in P.rglob('*') if f.is_file() and str(f.relative_to(P))!='evidence/binding.json'};(P/'evidence/binding.json').write_text(json.dumps(files,indent=2)+'\n')
 else:verify()
