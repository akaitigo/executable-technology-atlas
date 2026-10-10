"""Actual child attempts/exit/stdout; --record alone appends immutable raw."""
import argparse,json,hashlib,datetime,uuid,subprocess,sys
from pathlib import Path
from producer import run,FIXTURE
ROOT=Path(__file__).resolve().parent
SOURCES=['fixture.json','oracle.json','EXPECTATIONS.md','producer.py','runner.py','server.py','index.html','ui.js']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def exit_for(r):return {'NORMAL':0,'FAULT_UNRESOLVED_CSS':0,'INPUT_REFUSED':2,'EXECUTION_FAILURE':1}[r['status']]
def observe():
 attempts=[];cases=[]
 for c in FIXTURE['cases']:
  start=utc();args=[sys.executable,'-B','runner.py','--case',c['id']];p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
  attempts.append(dict(case=c['id'],command=['python3','-B','runner.py','--case',c['id']],started_utc=start,ended_utc=utc(),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
  try:r=json.loads(p.stdout)
  except ValueError:r=dict(case=c['id'],input=c,status='EXECUTION_FAILURE',reason='child stdout is not JSON',safe=None,naive=None)
  cases.append(r)
 return dict(utc=utc(),command='python3 -B runner.py --record',source_sha256={n:sha(ROOT/n) for n in SOURCES},fixture=FIXTURE,cases=cases,attempts=attempts)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',default='blue');p.add_argument('--tokens-json');p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  r=observe();name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
  expected_failure={c['id'] for c in FIXTURE['cases'] if c['variant']=='execution-failure'}
  if not any(c['status']=='EXECUTION_FAILURE' and c['case'] not in expected_failure for c in r['cases']) and all(a['exit']==exit_for(c) and not a['stderr'] for a,c in zip(r['attempts'],r['cases'])):(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name)
 else:
  r=run(a.case,a.tokens_json);print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(exit_for(r))
