# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import subprocess,json,time,signal,hashlib,platform,datetime,re
from pathlib import Path
R=Path(__file__).resolve().parent
def record(name):
 assert re.fullmatch(r'http-attempt-[0-9]{2}',name);o=R/'observations'/name;assert not o.exists();o.mkdir();worker=None;r=dict(mode='ACTUAL_LOOPBACK_HTTP',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),system=platform.system(),machine=platform.machine(),source_hashes={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in ['http_worker.py','http_client.py','actual_http.py','hand-oracle.json']},clients=[],protected_listeners_no_actions=True)
 try:
  worker=subprocess.Popen([sys.executable,'-B',str(R/'http_worker.py'),str(o/'server.jsonl')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);line=worker.stdout.readline()
  if not line:raise RuntimeError('owned worker did not bind')
  ready=json.loads(line);r['ready']=ready;assert ready['pid']==worker.pid
  for which in ['fast','slow']:
   result=subprocess.run([sys.executable,'-B',str(R/'http_client.py'),str(ready['port']),which],capture_output=True,text=True,timeout=5);assert result.returncode==0;r['clients'].append(json.loads(result.stdout))
  until=time.monotonic()+2
  while time.monotonic()<until:
   events=[json.loads(s) for s in (o/'server.jsonl').read_text().splitlines()]
   if any(e['request_id']=='qe-timeout-01' and e['event'] in ('WRITE_RETURNED','SEND_ERROR') for e in events):break
   time.sleep(.02)
  r['server_events']=events;r['status']='OBSERVED'
 except Exception as e:r.update(status='EXECUTION_FAILURE',error_class=type(e).__name__,error_message=str(e))
 finally:
  if worker:
   if worker.poll() is None:worker.send_signal(signal.SIGINT)
   out,err=worker.communicate(timeout=5);r['owned_server_exit']=worker.returncode;r['server_stderr']=err.replace(str(R),'<module>');r['owned_server_stopped']=worker.poll() is not None
  r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(o/'raw.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r,ensure_ascii=False,indent=2));assert r['status']=='OBSERVED'
if __name__=='__main__':
 assert len(sys.argv)==3 and sys.argv[1]=='--record';record(sys.argv[2])
