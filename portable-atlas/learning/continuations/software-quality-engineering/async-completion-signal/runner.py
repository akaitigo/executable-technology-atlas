"""Actual owned Node test processes; normal mode only reads saved raw."""
import json,subprocess,os,datetime,uuid,hashlib,argparse,platform,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute(case):
 row=dict(id=case['id'],input=case,command=['node','--test','--test-reporter=tap','case.test.mjs'],env=dict(ATLAS_SCHEDULE=case['schedule'],ATLAS_VARIANT=case['variant']))
 env=dict(os.environ);env.update(row['env']);env.pop('NODE_OPTIONS',None)
 temporary=None
 try:
  temporary=tempfile.TemporaryDirectory(prefix='atlas-async-',dir='/private/tmp');copied=Path(temporary.name)/'case.test.mjs';shutil.copyfile(ROOT/'case.test.mjs',copied);row['copied_source_sha256']=sha(copied)
  p=subprocess.Popen(row['command'],cwd=temporary.name,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);row['test_runner_pid']=p.pid
  try:out,err=p.communicate(timeout=5)
  except subprocess.TimeoutExpired:
   p.kill();out,err=p.communicate();row['execution_failure']='owned child timeout'
  row.update(stdout=out,stderr=err,exit_code=p.returncode,child_reaped=p.poll() is not None)
  for f in [p.stdout,p.stderr]:f.close()
  row['streams_closed']=p.stdout.closed and p.stderr.closed;row['events']=[]
  for line in out.splitlines():
   if line.startswith('# ATLAS_EVENT '):row['events'].append(json.loads(line[len('# ATLAS_EVENT '):]))
   elif line.startswith('ATLAS_EVENT '):row['events'].append(json.loads(line[len('ATLAS_EVENT '):]))
  if row['events']:row['test_file_pid']=row['events'][0]['pid']
 except Exception as e:row['execution_failure']=repr(e)
 finally:
  if temporary is not None:
   path=Path(temporary.name);temporary.cleanup();row['temp_removed']=not path.exists()
 return row

def run():
 f=json.loads((ROOT/'fixture.json').read_text());version=subprocess.run(['node','--version'],capture_output=True,text=True,check=True).stdout.strip();r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B runner.py --record',environment=dict(node=version,system=platform.system(),release=platform.release()),fixture=f,source_sha256={n:sha(ROOT/n) for n in ['fixture.json','oracle.json','EXPECTATIONS.md','case.test.mjs','runner.py']},cases=[])
 for case in f['cases']:r['cases'].append(execute(case))
 r['execution_failures']=sum('execution_failure' in c for c in r['cases']);return r
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');args=a.parse_args()
 if args.record:
  try:r=run()
  except Exception as e:r=dict(execution_failures=1,execution_failure=repr(e),cases=[])
  name=('failed-' if r['execution_failures'] else 'run-')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
  if not r['execution_failures']:(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name);raise SystemExit(1 if r['execution_failures'] else 0)
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/p['raw']).read_text())
