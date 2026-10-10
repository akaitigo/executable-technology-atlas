"""Two actual processes, deterministic pipe barriers, owned files/processes only."""
import subprocess,sys,json,selectors,tempfile,datetime,platform,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Child:
 def __init__(self,root,name):
  self.p=subprocess.Popen([sys.executable,'-B',str(ROOT/'worker.py'),str(root),name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1);self.lines=[];self.events=[]
 def receive(self,timeout=3):
  with selectors.DefaultSelector() as s:
   s.register(self.p.stdout,selectors.EVENT_READ)
   if not s.select(timeout):raise TimeoutError('owned child response deadline')
  line=self.p.stdout.readline()
  if not line:raise RuntimeError('child exited before response')
  self.lines.append(line);e=json.loads(line);self.events.append(e);return e
 def command(self,op):
  self.p.stdin.write(json.dumps({'op':op})+'\n');self.p.stdin.flush();return self.receive()
 def cleanup(self):
  if self.p.poll() is None:self.p.terminate()
  try:self.p.wait(timeout=2)
  except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=2)
  stderr=self.p.stderr.read()
  for f in (self.p.stdin,self.p.stdout,self.p.stderr):f.close()
  return dict(pid=self.p.pid,exit_code=self.p.returncode,reaped=True,stderr=stderr)
def execute(case):
 children={};events=[];visible=[0];out=None
 with tempfile.TemporaryDirectory(prefix='.owned-locking-',dir=ROOT) as d:
  root=Path(d);(root/'config').write_bytes(b'0\n')
  try:
   for name in ('A','B'):
    children[name]=Child(root,name);events.append(children[name].receive())
   for name,op,wanted in case['schedule']:
    e=children[name].command(op);events.append(e)
    if e['event']!=wanted:raise AssertionError((name,op,wanted,e))
    if op in ('replace','abort'):visible.append(int((root/'config').read_bytes()))
   final=(root/'config').read_bytes().decode()
   for c in children.values():events.append(c.command('close'));c.p.wait(timeout=3)
   out=dict(id=case['id'],events=events,visible=visible,finalbytes=final)
  finally:
   cleanup={name:c.cleanup() for name,c in children.items()}
   raw={name:''.join(c.lines) for name,c in children.items()}
  out.update(children=cleanup,raw_stdout=raw)
 out['temp_removed']=not root.exists();return out
def timeout_probe():
 with tempfile.TemporaryDirectory(prefix='.owned-timeout-',dir=ROOT) as d:
  root=Path(d);c=Child(root,'timeout');ready=c.receive()
  try:c.receive(.15);raise AssertionError('unexpected response')
  except TimeoutError:result=dict(event='controller_timeout',bound_seconds=.15,ready=ready)
  finally:result['child']=c.cleanup()
 result['temp_removed']=not root.exists();return result
def record():
 oracle=json.loads((ROOT/'oracle.json').read_text());raw=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment=dict(system=platform.system(),release=platform.release(),machine=platform.machine(),python=platform.python_version()),cases=[execute(c) for c in oracle['cases']],timeout=timeout_probe(),durability_proven=False,unrun=['power loss','NFS/SMB','Linux kernel','speedup','target inode locking','non-cooperating writers','continuous reader stress'])
 raw['source_sha256']={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('worker.py','experiment.py','oracle.json')}
 return raw
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  try:
   raw=record();(ROOT/'evidence/raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');print('explicitly recorded actual owned process execution')
  except Exception as e:
   (ROOT/'evidence/failed-run.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':repr(e)},indent=2)+'\n');raise
 else:print((ROOT/'evidence/raw.json').read_text())
