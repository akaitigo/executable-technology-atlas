"""Atlas: one owned browser checker after a fresh approved resource record; no calculation."""
import argparse,datetime,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
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
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--gate',required=True);a=parser.parse_args();gate=(ROOT/a.gate).resolve()
 assert gate.parent==ROOT/'observations','owned resource record required'
 g=json.loads(gate.read_text());age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(g['at_utc'])).total_seconds()
 assert g['headroom'] and 0<=age<=60,'fresh resources required'
 assert g['gate_source_sha256']==sha(ROOT/'browser-resource-gate.py') and g['gate_policy_sha256']==sha(ROOT/'browser-gate-policy.json'),'gate source/policy mismatch'
 assert json.loads((ROOT/'browser-gate-policy.json').read_text())['root_browser_slot_approved'],'root browser slot required'
 now=datetime.datetime.now(datetime.timezone.utc);out=ROOT/'observations'/('browser-process-'+now.strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
 report={'title':'Atlas browser owner process log','at_utc':now.isoformat(),'resource_gate':str(gate.relative_to(ROOT)),'resource_gate_sha256':sha(gate),'gate_age_seconds':age,'child_started':False,'child_reaped':False,'timed_out':False,'output_complete':False,'exit_code':None,'status':'preparing','observation_deadline_seconds':90,'recovery_grace_seconds':2,'calculation_executed':False,'source_sha256':{n:sha(ROOT/n) for n in ['run-browser.py','check-reader-browser.cjs','priority_exec.py','browser-resource-gate.py','browser-gate-policy.json']}}
 child=None;stdout='';stderr='';start=time.monotonic()
 try:
  cmd=[sys.executable,'-B',str(ROOT/'priority_exec.py'),'/opt/homebrew/bin/node',str(ROOT/'check-reader-browser.cjs')];report['command']=cmd
  child=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True);report.update(child_started=True,owned_pid=child.pid,owned_pgid=child.pid,status='running')
  try:stdout,stderr=child.communicate(timeout=90);report.update(child_reaped=True,output_complete=True,exit_code=child.returncode)
  except subprocess.TimeoutExpired as e:
   stdout=text(e.stdout);stderr=text(e.stderr);report.update(timed_out=True,status='deadline',partial_output_retained=True)
   stdout,stderr=recover_owned(child,report,stdout,stderr)
  report['status']='completed' if report['child_reaped'] and report['exit_code']==0 and not report['timed_out'] else 'failed'
 except Exception as e:
  report.update(status='running_failed' if child else 'preparation_failed',error=str(e))
  if child and not report['child_reaped']:
   if getattr(e,'stdout',None) is not None:stdout=text(e.stdout)
   if getattr(e,'stderr',None) is not None:stderr=text(e.stderr)
   stdout,stderr=recover_owned(child,report,stdout,stderr)
 finally:
  if child and not report['child_reaped']:report['remaining_owned_pid']=child.pid
  (out/'stdout.txt').write_text(stdout);(out/'stderr.txt').write_text(stderr);report.update(elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(out/'stdout.txt'),stderr_sha256=sha(out/'stderr.txt'),finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  for line in stderr.splitlines():
   if line.startswith('ATLAS_PRIORITY '):report['priority_guard']=json.loads(line[len('ATLAS_PRIORITY '):])
  if report['status']=='completed' and not report.get('priority_guard',{}).get('ready'):report['status']='failed_priority_evidence'
  (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'path':str(out.relative_to(ROOT)),**report},ensure_ascii=False))
 return 0 if report['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
