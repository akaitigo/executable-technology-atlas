import sys
sys.dont_write_bytecode=True
import threading,time,datetime,platform
from admission import validate,authenticated

def witness(f,mode,broken=False):
 validate(f)
 if mode not in ('split','atomic'):raise ValueError('thread mode')
 seen=set(f['seen']);barrier=threading.Barrier(2,timeout=2);lock=threading.Lock();log_lock=threading.Lock()
 log=[];result={};errors=[]
 def record(event):
  with log_lock:log.append(event)
 def worker(n,r):
  try:
   good=authenticated(r);record(dict(request=n,event='authenticate',valid=good))
   if mode=='split':
    absent=r['id'] not in seen if good else None
    record(dict(request=n,event='check',cached_absent=absent))
    barrier.wait()
    if good and absent:seen.add(r['id']);result[n]='accepted';record(dict(request=n,event='remember',id=r['id']))
    else:result[n]='replay' if good else 'invalid_mac'
   else:
    barrier.wait()
    if not good:result[n]='invalid_mac';return
    if not lock.acquire(timeout=2):raise TimeoutError('admission lock timeout')
    try:
     absent=r['id'] not in seen;record(dict(request=n,event='check',cached_absent=absent))
     if absent:seen.add(r['id']);record(dict(request=n,event='remember',id=r['id']))
     result[n]='accepted' if absent else 'replay'
    finally:lock.release()
  except Exception as exc:
   with log_lock:errors.append(dict(request=n,type=type(exc).__name__,message=str(exc)))
 if broken:barrier.abort()
 workers=[threading.Thread(target=worker,args=(n,r),name='admission-'+n) for n,r in zip('AB',f['requests'])]
 started=[]
 try:
  for t in workers:t.start();started.append(t)
  deadline=time.monotonic()+5
  for t in started:t.join(max(0,deadline-time.monotonic()))
 finally:
  barrier.abort()
  for t in started:t.join(3)
 alive=[t.name for t in started if t.is_alive()]
 return dict(fixture=f['id'],mode=mode,intentional_broken=broken,status='failed' if errors or alive else 'passed',results=result,accepted_count=sum(v=='accepted' for v in result.values()),seen=sorted(seen),events=log,errors=errors,alive_threads=alive)
def environment():return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),platform=platform.system(),thread_control='Barrier timeout=2s, Lock timeout=2s; total join budget=5s then abort+3s joins; no sleeps')
