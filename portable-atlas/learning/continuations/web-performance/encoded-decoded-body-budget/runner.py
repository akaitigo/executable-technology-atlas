"""Live owned loopback only. Explicit --record appends raw; default never writes."""
import argparse,json,datetime,uuid,subprocess,sys,hashlib
from pathlib import Path
from producer import run,FIXTURE,utc
ROOT=Path(__file__).resolve().parent
SOURCES=['fixture.json','oracle.json','EXPECTATIONS.md','producer.py','runner.py','server.py','index.html','ui.js']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def exit_for(r):return 0 if r['status'] in ['NORMAL','FAULT_DECODED_BUDGET'] else 2 if r['status']=='INPUT_REFUSED' else 3 if r['status'] in ['BROWSER_REQUIRED','UNSUPPORTED_LIVE_PORT','UNSUPPORTED_TIMING'] else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',default='plain8');p.add_argument('--port',type=int);p.add_argument('--input-json');p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  attempts=[];cases=[]
  for c in FIXTURE['cases']:
   cmd=['python3','-B','runner.py','--case',c['id'],'--port',str(a.port)];start=utc();s=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);attempts.append(dict(case=c['id'],command=cmd,started_utc=start,ended_utc=utc(),exit=s.returncode,stdout=s.stdout,stderr=s.stderr));
   try:x=json.loads(s.stdout)
   except ValueError:x=dict(result=dict(case=c['id'],status='EXECUTION_FAILURE',reason='child stdout not JSON'),wire=None)
   cases.append(x)
  raw=dict(utc=utc(),port=a.port,source_sha256={n:sha(ROOT/n) for n in SOURCES},fixture=FIXTURE,attempts=attempts,cases=cases);name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(raw,f,ensure_ascii=False,indent=2);f.write('\n')
  if all(x['result']['status']!='EXECUTION_FAILURE' or x['result']['reason']=='HTTP_500' for x in cases) and all(s['exit']==exit_for(x['result']) and not s['stderr'] for s,x in zip(attempts,cases)):(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name)
 else:
  x=run(a.case,a.port,a.input_json);print(json.dumps(x,ensure_ascii=False,indent=2));sys.exit(exit_for(x['result']))
