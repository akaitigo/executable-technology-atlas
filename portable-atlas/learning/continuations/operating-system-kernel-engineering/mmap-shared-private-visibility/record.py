"""Explicit unique raw runs; preserve partial observations on unexpected execution failure."""
import json,hashlib,datetime,uuid,platform,mmap,os,argparse
from pathlib import Path
from producer import execute_mode,execute_boundary
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute():
 fixture=json.loads((ROOT/'fixture.json').read_text());raw=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B record.py --record',attempt='actual owned file mmap; single-process fresh reads and second readonly mapping',environment=dict(python=platform.python_version(),system=platform.system(),release=platform.release(),machine=platform.machine(),pid=os.getpid(),page_size=mmap.PAGESIZE,allocation_granularity=mmap.ALLOCATIONGRANULARITY),fixture=fixture,input_sha256=sha(ROOT/'fixture.json'),source_sha256={n:sha(ROOT/n) for n in ('fixture.json','oracle.json','EXPECTATIONS.md','producer.py','record.py')},modes=[],boundaries=[],durability_proven=False,crossprocess='not executed',physical_COW_pages='not measured',pagefaults='not measured')
 try:
  for mode in fixture['modes']:
   row={};raw['modes'].append(row);execute_mode(mode,fixture,row)
  for id in fixture['boundary_cases']:
   row={};raw['boundaries'].append(row);execute_boundary(id,fixture,row)
  raw['exit_code']=0;raw['outcomes']=dict(writes_succeeded=sum(r['write_outcome']=='succeeded' for r in raw['modes']),writes_refused=sum(r['write_outcome']=='refused' for r in raw['modes']),boundary_refusals=sum(r['outcome']=='refused' for r in raw['boundaries']),unexpected_acceptances=sum(r['outcome']=='unexpected_acceptance' for r in raw['boundaries']),execution_failures=0)
 except Exception as e:raw.update(exit_code=1,unexpected_execution_failure=repr(e))
 return raw
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  raw=execute();name=('run-' if raw['exit_code']==0 else 'failed-')+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(raw,f,ensure_ascii=False,indent=2);f.write('\n')
  if raw['exit_code']==0:(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name);raise SystemExit(raw['exit_code'])
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/p['raw']).read_text())
