"""Actual subprocess stdin/stdout protocol. Explicit record writes new evidence only."""
import json,sys,os,subprocess,datetime,platform,hashlib,uuid,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def event(name,seq):return dict(event=name,seq=seq,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
def execute(case):
 row=dict(id=case['id'],request=case['request'],parent_pid=os.getpid(),parent=json.loads((ROOT/'fixture.json').read_text())['parent'],command=['python3','-B','child.py'],parent_events=[],cleanup={})
 p=subprocess.Popen([sys.executable,'-B','child.py'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);row['child_pid']=p.pid
 try:
  payload=json.dumps(case['request'],separators=(',',':'))+'\n';row['stdin']=payload;row['parent_events'].append(event('parentwrite_start',0));p.stdin.write(payload);p.stdin.flush();row['parent_events'].append(event('parentwrite_completed',1));p.stdin.close();p.stdin=None
  stdout,stderr=p.communicate(timeout=5);row.update(stdout=stdout,stderr=stderr,exit_code=p.returncode);row['parent_events'].append(event('parentreceive',2));lines=stdout.splitlines();row['child']=json.loads(lines[0]);row['emit_ack']=json.loads(lines[1]);assert len(lines)==2
 except Exception as e:
  row['execution_failure']=repr(e)
 finally:
  if p.poll() is None:p.kill();p.communicate()
  for f in [p.stdin,p.stdout,p.stderr]:
   if f is not None:f.close()
  row['cleanup']=dict(child_reaped=p.poll() is not None,owned_streams_closed=all(f is None or f.closed for f in [p.stdin,p.stdout,p.stderr]))
 return row
def run():
 f=json.loads((ROOT/'fixture.json').read_text());r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B runner.py --record',environment=dict(python=platform.python_version(),system=platform.system(),release=platform.release(),parent_pid=os.getpid()),fixture=f,source_sha256={n:sha(ROOT/n) for n in ['fixture.json','oracle.json','EXPECTATIONS.md','child.py','runner.py']},cases=[],scope='owned local subprocess; custom JSON carrier; fixed case IDs; no clock sort')
 for case in f['cases']:
  try:r['cases'].append(execute(case))
  except Exception as e:r['cases'].append(dict(id=case['id'],request=case['request'],execution_failure=repr(e),phase='process creation/setup before protocol',cleanup=dict(no_created_process_handle=True)))
 r['execution_failures']=sum('execution_failure' in c for c in r['cases']);return r
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');args=a.parse_args()
 if args.record:
  r=run();name=('failed-' if r['execution_failures'] else 'run-')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
  if not r['execution_failures']:(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name);sys.exit(1 if r['execution_failures'] else 0)
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/p['raw']).read_text())
