"""Atlas: one owned real WASI child, fresh resources and actual priority, bounded recovery."""
import argparse,datetime,hashlib,json,os,signal,subprocess,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NODE=Path('/opt/homebrew/Cellar/node/25.2.1/bin/node')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def text(value):return value.decode('utf-8','replace') if isinstance(value,bytes) else value or ''
def recover_owned(child,report,stdout,stderr,kill_group=os.killpg):
 try:kill_group(child.pid,signal.SIGKILL);report['owned_group_kill_sent']=True
 except Exception as kill:report['kill_error']=str(kill)
 try:stdout,stderr=child.communicate(timeout=2);report.update(child_reaped=True,output_complete=True,exit_code=child.returncode)
 except Exception as reap:
  report['reap_error']=str(reap)
  if getattr(reap,'stdout',None) is not None:stdout=text(reap.stdout)
  if getattr(reap,'stderr',None) is not None:stderr=text(reap.stderr)
 if not report['child_reaped']:report.update(remaining_owned_pid=child.pid,further_launches_allowed=False)
 return stdout,stderr
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true');parser.add_argument('--gate',required=True);a=parser.parse_args()
 if not a.record:parser.error('Atlas: saved results use verify.py; a new calculation requires --record and coordination')
 gate=(ROOT/a.gate).resolve();assert gate.parent==ROOT/'observations','owned resource record required';g=json.loads(gate.read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g['at_utc'])).total_seconds()
 assert g['headroom'] and 0<=age<=60,'fresh resources required'
 assert g['gate_source_sha256']==sha(ROOT/'resource-gate.py') and g['gate_policy_sha256']==sha(ROOT/'gate-policy.json'),'source/policy mismatch'
 now=datetime.datetime.now(datetime.timezone.utc);out=ROOT/'observations'/('runtime-'+now.strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir();names=['module.wasm','module-contract.json','decode_module.py','observe.cjs','run.py','priority_exec.py','verify.py','fixtures.json','hand-oracle.json','contract-lock.json','CONTRACT.md','SOURCE-MAP.md','resource-gate.py','gate-policy.json']
 report={'title':'Atlas WASI read/inheriting execution log','started_at_utc':now.isoformat(),'attempt':1,'retry':0,'resource_gate_file':str(gate.relative_to(ROOT)),'resource_gate_sha256':sha(gate),'resource_gate_age_seconds':age,'sources':{n:sha(ROOT/n) for n in names},'python_executable_sha256':sha(Path(sys.executable)),'node_executable_sha256':sha(NODE),'observation_deadline_seconds':5,'cleanup_grace_seconds':2,'child_started':False,'child_reaped':False,'output_complete':False,'timed_out':False,'exit_code':None,'status':'preparing','stdout_file':'stdout.txt','stderr_file':'stderr.txt','search_engine_executed':False,'browser_executed':False,'server_started':False,'temporary_fixture_created':False,'fixture_cleanup':False,'later_child_started':False}
 child=None;stdout='';stderr='';start=time.monotonic();fixture=out/'fixture'
 try:
  fixture.mkdir();(fixture/'note.txt').write_bytes(bytes.fromhex(json.loads((ROOT/'fixtures.json').read_text())['fixture']['hex']));report['temporary_fixture_created']=True
  cmd=[sys.executable,'-B',str(ROOT/'priority_exec.py'),str(NODE),'--max-old-space-size=64',str(ROOT/'observe.cjs'),str(fixture)];report['command']=cmd
  child=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,env={'PATH':'/usr/bin:/bin','LANG':'C','TZ':'UTC','PYTHONDONTWRITEBYTECODE':'1'});report.update(child_started=True,owned_pid=child.pid,owned_pgid=child.pid,status='running')
  try:stdout,stderr=child.communicate(timeout=5);report.update(child_reaped=True,output_complete=True,exit_code=child.returncode)
  except subprocess.TimeoutExpired as e:
   stdout=text(e.stdout);stderr=text(e.stderr);report.update(timed_out=True,partial_output_retained=True);stdout,stderr=recover_owned(child,report,stdout,stderr)
  if not report['child_reaped'] or report['exit_code']!=0 or report['timed_out']:raise RuntimeError('calculation did not finish successfully')
  for line in stderr.splitlines():
   if line.startswith('ATLAS_PRIORITY '):report['priority_guard']=json.loads(line[len('ATLAS_PRIORITY '):])
  if not report.get('priority_guard',{}).get('ready') or report['priority_guard']['observed_nice']!=10:raise RuntimeError('priority evidence missing')
  lines=[json.loads(line) for line in stdout.splitlines()];assert lines[-1]['kind']=='result';result=lines[-1]['result'];assert result['status']=='observed' and result['priority_observed']==10 and len(result['cases'])==4 and not result['later_cases_not_started'];assert all(c['cleanup']['complete'] for c in result['cases'])
  (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');report.update(status='observed',result_file='result.json',result_sha256=sha(out/'result.json'))
 except Exception as e:
  report.update(status='execution_failed' if child else 'preparation_failed',error={'name':type(e).__name__,'message':str(e)})
  if child and not report['child_reaped'] and 'reap_error' not in report:
   if getattr(e,'stdout',None) is not None:stdout=text(e.stdout)
   if getattr(e,'stderr',None) is not None:stderr=text(e.stderr)
   stdout,stderr=recover_owned(child,report,stdout,stderr)
 finally:
  if child is None or report['child_reaped']:
   try:
    if fixture.exists():shutil.rmtree(fixture)
    report['fixture_cleanup']=not fixture.exists()
   except Exception as e:report.update(fixture_cleanup_error=str(e),status='cleanup_failed')
  else:report['fixture_retained_reason']='owned child exit unconfirmed'
  if child and not report['child_reaped']:report.update(remaining_owned_pid=child.pid,further_launches_allowed=False)
  (out/'stdout.txt').write_text(stdout);(out/'stderr.txt').write_text(stderr);report.update(stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'),elapsed_seconds=time.monotonic()-start,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out.relative_to(ROOT)),'status':report['status'],'child_reaped':report['child_reaped'],'priority_guard':report.get('priority_guard'),'elapsed_seconds':report['elapsed_seconds'],'fixture_cleanup':report['fixture_cleanup']}))
 return 0 if report['status']=='observed' else 1
if __name__=='__main__':raise SystemExit(main())
