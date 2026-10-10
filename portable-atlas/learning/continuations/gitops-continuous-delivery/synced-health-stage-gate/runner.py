# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform,json
CASES={'healthy':'Healthy','degraded':'Degraded','desired-only-fault':'Degraded','progressing':'Progressing','rollback':'Degraded','refusal':'Invalid','failure':'Healthy'}
_DEFAULT=object()
def run(case,health=_DEFAULT):
 h=CASES.get(case) if health is _DEFAULT else health;r=dict(case=case,health_input=h,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),events=[],status='OK',model='finite Python stage gate; no Argo/probe/cluster')
 if case not in CASES or type(h) is not str or h not in ('Healthy','Degraded','Progressing') or case=='refusal':r.update(status='REFUSED_INPUT',stage='validation',error='fixed case and Healthy/Degraded/Progressing string required')
 else:
  try:
   if case=='failure':raise RuntimeError('injected stage executor failure')
   generation=1;desired='v1';actual='v1';current_health='Healthy';starts=0
   def event(name):r['events'].append(dict(event=name,generation=generation,desired=desired,actual=actual,health=current_health,synced=desired==actual,stage2_starts=starts))
   event('initial');generation=2;desired='v2';current_health='Progressing';event('publish-v2');actual=desired;event('reconcile-v2');current_health=h;event('health')
   def gate():
    nonlocal starts
    allowed=desired==actual and (case=='desired-only-fault' or current_health=='Healthy')
    if not allowed:event('gate-block')
    elif starts:event('gate-already-started')
    else:starts+=1;event('gate-start')
   gate()
   if case=='healthy':gate()
   if case=='rollback':
    generation=3;desired='v1';event('publish-rollback');actual=desired;current_health='Progressing';event('reconcile-rollback');current_health='Healthy';event('health-rollback')
   r['stage']='complete'
  except Exception as e:r.update(status='EXECUTION_FAILURE',stage='executor',error_class=type(e).__name__,error_message=str(e))
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r
if __name__=='__main__':print(json.dumps(run(sys.argv[1] if len(sys.argv)>1 else 'healthy'),ensure_ascii=False))
