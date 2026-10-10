"""Atlas: injected recovery cases; no process, priority, browser or calculation calls."""
import importlib.util,json,hashlib,subprocess,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('browser_runner',ROOT/'run-browser.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
class Fake:
 pid=123456789;returncode=-9
 def __init__(self,error=None):self.error=error;self.timeouts=[]
 def communicate(self,timeout):
  self.timeouts.append(timeout)
  if self.error:raise self.error
  return 'complete stdout','complete stderr'
for name,kill_error,reap_error in [('reaped',None,None),('kill_failed_but_reaped',OSError('kill injected'),None),('kill_and_reap_failed',OSError('kill injected'),RuntimeError('reap injected')),('partial_after_timeout',None,subprocess.TimeoutExpired('fake',2,output=b'partial stdout',stderr=b'partial stderr'))]:
 calls=[]
 def kill(pid,sig):
  calls.append([pid,sig])
  if kill_error:raise kill_error
 c=Fake(reap_error);r={'child_reaped':False,'output_complete':False};stdout,stderr=m.recover_owned(c,r,'prior stdout','prior stderr',kill)
 assert calls==[[c.pid,signal.SIGKILL]] and c.timeouts==[2]
 assert r['child_reaped']==(reap_error is None)
 assert ('kill_error' in r)==(kill_error is not None) and ('reap_error' in r)==(reap_error is not None)
 if reap_error:assert r['remaining_owned_pid']==c.pid and r['further_launches_allowed'] is False
 if isinstance(reap_error,subprocess.TimeoutExpired):assert (stdout,stderr)==('partial stdout','partial stderr')
 elif reap_error:assert (stdout,stderr)==('prior stdout','prior stderr')
 else:assert (stdout,stderr)==('complete stdout','complete stderr')
 checks.append({'case':name,'report':r,'stdout':stdout,'stderr':stderr,'passed':True})
out={'title':'Atlas injected recovery check','checks':checks,'passed':True,'real_processes_started':0,'real_processes_signalled':0,'browser_executed':False,'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['run-browser.py','check-browser-recovery.py']}}
(ROOT/'observations/browser-recovery-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':True,'injected_cases':len(checks),'processes_started':0}))
