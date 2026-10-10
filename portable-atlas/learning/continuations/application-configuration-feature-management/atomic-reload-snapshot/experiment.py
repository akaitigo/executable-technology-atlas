"""Actual fixture reads and deterministic Event-gated thread interleavings."""
import dataclasses,json,sys,threading
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
@dataclasses.dataclass(frozen=True)
class Snapshot:
 version:str
 timeout_ms:int
 retries:int
class Rejected(Exception):pass

def load(name,trace):
 trace.append({'event':'json-read','fixture':name})
 try:
  with (ROOT/'fixtures'/name).open(encoding='utf-8') as f:d=json.load(f)
 except json.JSONDecodeError:raise Rejected('json-syntax')
 except OSError:raise OSError('candidate-read-failed') from None
 if type(d) is not dict:raise Rejected('object-required')
 if set(d)!={'version','timeout_ms','retries'}:raise Rejected('field-set')
 if type(d['version']) is not str or d['version'] not in ('v1','v2','v3'):raise Rejected('version-type-or-value')
 if type(d['timeout_ms']) is not int:raise Rejected('timeout-type')
 if not 1<=d['timeout_ms']<=5000:raise Rejected('timeout-range')
 if type(d['retries']) is not int:raise Rejected('retries-type')
 if not 0<=d['retries']<=5:raise Rejected('retries-range')
 s=Snapshot(**d);trace.append({'event':'validated','version':s.version});return s

def run(spec,mode):
 trace=[];active=load('v1.json',trace); fields={'timeout_ms':(active.timeout_ms,active.version),'retries':(active.retries,active.version)}
 mutation_blocked=False
 try:active.timeout_ms=999
 except dataclasses.FrozenInstanceError:mutation_blocked=True
 def commit(candidate,pause=None):
  nonlocal active
  if mode=='normal':
   trace.append({'event':'ready-reference-swap','version':candidate.version})
   if pause:pause()
   active=candidate
   trace.append({'event':'reference-swap','version':active.version})
  else:
   fields['timeout_ms']=(candidate.timeout_ms,candidate.version);trace.append({'event':'field-write','field':'timeout_ms','version':candidate.version})
   if pause:pause()
   fields['retries']=(candidate.retries,candidate.version);active=candidate
   trace.append({'event':'field-write','field':'retries','version':candidate.version})
 def reader(pause=None):
  captured=active if mode=='normal' else None
  trace.append({'event':'request-start','snapshot':captured.version if captured else 'field-wise'})
  a=(captured.timeout_ms,captured.version) if captured else fields['timeout_ms']
  trace.append({'event':'field-read','field':'timeout_ms','value':a[0],'version':a[1]})
  if pause:pause()
  b=(captured.retries,captured.version) if captured else fields['retries']
  trace.append({'event':'field-read','field':'retries','value':b[0],'version':b[1]})
  return {'tuple':[a[0],b[0]],'field_versions':[a[1],b[1]],'request_snapshot':captured.version if captured else None}
 def gated(worker,between):
  reached=threading.Event();release=threading.Event();box={}
  def pause():
   reached.set()
   if not release.wait(5):raise RuntimeError('gate-release-timeout')
  def target():
   try:box['result']=worker(pause)
   except Exception as e:box['error']=type(e).__name__+':'+str(e)
  t=threading.Thread(target=target,name='fixture-gate');t.start()
  if not reached.wait(5):
   release.set();t.join(5);raise RuntimeError('gate-reached-timeout')
  try:middle=between()
  finally:release.set();t.join(5)
  if t.is_alive() or 'error' in box:raise RuntimeError(box.get('error','thread-not-finished'))
  return box.get('result'),middle
 status='accepted';reason=None;candidate=None
 try:
  if spec['schedule']=='candidate-after-v2':commit(load('v2.json',trace))
  candidate=load(spec['fixture'],trace)
  schedule=spec['schedule']
  if schedule=='before-reload':observed=reader();commit(candidate)
  elif schedule=='after-reload':commit(candidate);observed=reader()
  elif schedule=='between-reads':observed,_=gated(reader,lambda:commit(candidate))
  elif schedule=='before-commit':_,observed=gated(lambda pause:commit(candidate,pause),reader)
  else:commit(candidate);observed=reader()
 except Rejected as e:status='expected-refusal';reason=str(e);trace.append({'event':'rejected','reason':reason,'retained':active.version});observed=reader()
 except (OSError,RuntimeError) as e:status='execution-error';reason=str(e);trace.append({'event':'execution-error','reason':reason,'retained':active.version});observed=None
 next_request=reader() if status!='execution-error' else None
 return {'status':status,'candidate_label':spec['candidate'],'validated_candidate_version':candidate.version if candidate else None,'adopted_version':active.version,'reason':reason,'request':observed,'next_request':next_request,'immutable_mutation_blocked':mutation_blocked,'trace':trace}

def main():
 specs=json.loads((ROOT/'contracts.json').read_text())['cases']
 rows=[]
 for spec in specs:rows.append({'id':spec['id'],'normal':run(spec,'normal'),'faulty':run(spec,'field-wise')})
 print(json.dumps({'rows':rows},ensure_ascii=False))
if __name__=='__main__':main()
