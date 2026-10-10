"""Atlas: one explicitly requested, bounded, sequential score-calculation child."""
import argparse,datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true');parser.add_argument('--gate',required=True);args=parser.parse_args()
 if not args.record:parser.error('Atlas: use verify.py for saved records; --record requires an allocated execution slot')
 gate_path=(ROOT/args.gate).resolve()
 if gate_path.parent!=ROOT/'observations':raise ValueError('owned gate path required')
 gate=json.loads(gate_path.read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(gate['at_utc'])).total_seconds()
 if not gate['headroom'] or not 0<=age<=60 or gate['gate_source_sha256']!=sha(ROOT/'resource-gate.py') or gate['gate_policy_sha256']!=sha(ROOT/'gate-policy.json'):raise ValueError('fresh matching resource gate required; no child started')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'observations'/('calculation-'+stamp);out.mkdir()
 names=['model.py','observe.py','run.py','priority_exec.py','verify.py','fixtures.json','hand-oracle.json','contract-lock.json','CONTRACT.md','SOURCE-MAP.md','resource-gate.py','gate-policy.json']
 cmd=[sys.executable,'-B',str(ROOT/'priority_exec.py'),sys.executable,'-B',str(ROOT/'observe.py')]
 record={'title':'Atlas 検索順位の計算実行ログ','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':1,'retry':0,'resource_gate_file':str(gate_path.relative_to(ROOT)),'resource_gate_sha256':sha(gate_path),'resource_gate_age_seconds':age,'sources':{n:sha(ROOT/n) for n in names},'python_executable_sha256':sha(Path(sys.executable)),'command':cmd,'observation_deadline_seconds':5,'cleanup_grace_seconds':2,'child_started':False,'child_reaped':False,'output_complete':False,'timed_out':False,'exit_code':None,'status':'preparing','stdout_file':'stdout.txt','stderr_file':'stderr.txt','search_engine_executed':False,'WASI_executed':False,'browser_executed':False,'server_started':False,'temporary_fixture_created':False}
 proc=None;stdout=stderr=b'';start=time.monotonic()
 try:
  proc=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin','LANG':'C','TZ':'UTC','PYTHONDONTWRITEBYTECODE':'1'})
  record.update(child_started=True,owned_child_pid=proc.pid)
  try:
   stdout,stderr=proc.communicate(timeout=5);record['output_complete']=True
  except subprocess.TimeoutExpired as e:
   stdout=e.output or b'';stderr=e.stderr or b'';record['timed_out']=True;record['kill_attempted']=True
   try:proc.kill();record['kill_error']=None
   except Exception as error:record['kill_error']=str(error)
   try:stdout,stderr=proc.communicate(timeout=2);record['output_complete']=True
   except subprocess.TimeoutExpired as error:stdout=error.output or stdout;stderr=error.stderr or stderr;record['reap_error']='cleanup deadline exceeded'
   except Exception as error:record['reap_error']=str(error)
  except Exception as e:
   record['communication_error']=str(e)
   try:proc.kill();stdout,stderr=proc.communicate(timeout=2);record['output_complete']=True
   except Exception as error:record['reap_error']=str(error)
  record.update(child_reaped=proc.poll() is not None,exit_code=proc.returncode)
  lines=[json.loads(line[len('ATLAS_PRIORITY '):]) for line in stderr.decode(errors='replace').splitlines() if line.startswith('ATLAS_PRIORITY ')]
  record['priority_guard']=lines[-1] if lines else None
  if not record['priority_guard'] or not record['priority_guard'].get('ready'):raise RuntimeError('priority unavailable; calculation must not start')
  if not record['child_reaped'] or not record['output_complete'] or record['timed_out'] or record['exit_code']!=0:raise RuntimeError('calculation child did not finish successfully')
  result=json.loads(stdout);assert result['priority_observed']==10 and result['status']=='observed'
  (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');record.update(result_file='result.json',result_sha256=sha(out/'result.json'),status='observed')
 except Exception as e:record.update(status='preparation_or_execution_failed',error={'name':type(e).__name__,'message':str(e)})
 finally:
  if proc is not None:record.update(child_reaped=proc.poll() is not None,exit_code=proc.returncode)
  (out/'stdout.txt').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
  record.update(stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'),elapsed_seconds=time.monotonic()-start,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),later_child_started=False)
  if record['child_started'] and not record['child_reaped']:record['unreaped_owned_child']=proc.pid
  (out/'report.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'title':'Atlas 計算の終端','run':str(out.relative_to(ROOT)),'status':record['status'],'child_started':record['child_started'],'child_reaped':record['child_reaped'],'priority_guard':record.get('priority_guard'),'elapsed_seconds':record['elapsed_seconds']},ensure_ascii=False))
 return 0 if record['status']=='observed' and record['child_reaped'] else 1
if __name__=='__main__':raise SystemExit(main())
