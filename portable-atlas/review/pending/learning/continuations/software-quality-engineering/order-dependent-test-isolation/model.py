# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,subprocess,datetime
from pathlib import Path
R=Path(__file__).resolve().parent
CODE="exec(compile(open('worker.py').read(),'worker.py','exec'))"
def evaluate(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=dict(inputs=config,status='REFUSED_INPUT',started_utc=start,ended_utc=start,attempts=[],actual_unittest_executed=False)
 if type(config) is not dict or set(config)!=set(['isolation','order']) or type(config['isolation']) is not str or config['isolation'] not in ['shared','fixture'] or type(config['order']) is not str or config['order'] not in ['override-first','default-first']:return out
 attempts=[]
 for number in [1,2]:
  cmd=[sys.executable,'-B','-c',CODE,config['isolation'],config['order']];before=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:p=subprocess.run(cmd,cwd=str(R),capture_output=True,text=True,timeout=5)
  except subprocess.TimeoutExpired as e:
   attempts.append(dict(attempt=number,status='WORKER_TIMEOUT',command=['python3']+cmd[1:],exit_status=None,stdout=e.stdout.decode() if isinstance(e.stdout,bytes) else e.stdout or '',stderr=e.stderr.decode() if isinstance(e.stderr,bytes) else e.stderr or '',started_utc=before,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),worker=None));continue
  try:w=json.loads(p.stdout);status='WORKER_FINISHED'
  except ValueError:w=None;status='WORKER_PROTOCOL_FAILURE'
  attempts.append(dict(attempt=number,status=status,command=['python3']+cmd[1:],exit_status=p.returncode,stdout=p.stdout,stderr=p.stderr,started_utc=before,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),worker=w))
 out.update(status='ATTEMPTS_RECORDED' if all(a['status']=='WORKER_FINISHED' for a in attempts) else 'EXECUTION_INCOMPLETE',attempts=attempts,actual_unittest_executed=any(a['worker'] is not None for a in attempts),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());return out
if __name__=='__main__':print(json.dumps(evaluate(dict(isolation='shared',order='override-first')),indent=2))
