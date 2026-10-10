import json,sys,datetime
class Refused(Exception):pass
def require(ok,code):
 if not ok:raise Refused(code)
def validate(x):
 require(type(x) is dict and set(x)=={'capacity','horizon','policy','report','events'},'SCHEMA')
 require(type(x['capacity']) is int and 0<=x['capacity']<=3,'CAPACITY')
 require(type(x['horizon']) is int and 0<=x['horizon']<=12,'HORIZON')
 require(x['policy'] in ['fifo','priority'],'POLICY');require(x['report'] in ['actual','accept-fault'],'REPORT')
 require(type(x['events']) is list and len(x['events'])<=6,'EVENTS')
 ids=set();last=0
 for e in x['events']:
  require(type(e) is dict and set(e)=={'id','tick','priority','service'},'EVENT_SCHEMA')
  require(type(e['id']) is str and e['id'] in list('ABCDEF') and e['id'] not in ids,'ID');ids.add(e['id'])
  require(type(e['tick']) is int and 0<=e['tick']<=x['horizon'],'ARRIVAL');require(e['tick']>=last,'ARRIVAL_ORDER');last=e['tick']
  require(type(e['priority']) is int and 0<=e['priority']<=3,'PRIORITY');require(type(e['service']) is int and 1<=e['service']<=6,'SERVICE')
 return x
def simulate(x):
 validate(x);queue=[];running=None;accepted=[];drops=[];completed=[];intervals=[];trace=[];stats={e['id']:dict(id=e['id'],arrival=e['tick'],priority=e['priority'],service=e['service'],accepted=False,start=None,plannedEnd=None,end=None,wait=None,response=None,state='NOT_ARRIVED') for e in x['events']};arrived=0
 for t in range(x['horizon']+1):
  finished=[];starts=[];a=[];d=[];arrivals=[]
  if running and running['end']==t:
   id=running['id'];finished.append(id);completed.append(id);stats[id].update(end=t,response=t-stats[id]['arrival'],state='COMPLETED');running['completed']=True;running=None
  for e in x['events']:
   if e['tick']!=t:continue
   id=e['id'];arrivals.append(id);arrived+=1
   if len(queue)<x['capacity']:
    queue.append(e);accepted.append(id);a.append(id);stats[id].update(accepted=True,state='WAITING')
   else:drops.append(id);d.append(id);stats[id]['state']='DROPPED'
  if running is None and queue and t<x['horizon']:
   at=0 if x['policy']=='fifo' else max(range(len(queue)),key=lambda i:queue[i]['priority'])
   e=queue.pop(at);id=e['id'];running=dict(id=id,start=t,end=t+e['service'],completed=False);intervals.append(running);starts.append(id);stats[id].update(start=t,plannedEnd=running['end'],wait=t-e['tick'],state='RUNNING')
  trace.append(dict(tick=t,arrivals=arrivals,accepted=a,dropped=d,completed=finished,started=starts,queue=[e['id'] for e in queue],running=None if not running else dict(id=running['id'],start=running['start'],plannedEnd=running['end'],remaining=running['end']-t),counts=dict(arrived=arrived,accepted=len(accepted),dropped=len(drops),completed=len(completed)),reportedCompleted=len(accepted) if x['report']=='accept-fault' else len(completed)))
 return dict(status='OBSERVED',input=x,preemption=False,clock='synthetic integer tick; no wall-time simulation',accepted=accepted,dropped=drops,completed=completed,reportedCompleted=accepted[:] if x['report']=='accept-fault' else completed[:],counts=dict(arrived=arrived,accepted=len(accepted),dropped=len(drops),completed=len(completed),unfinished=len(accepted)-len(completed)),intervals=intervals,events=list(stats.values()),trace=trace)
def main():
 try:
  text=sys.stdin.read(30001);require(len(text.encode())<=30000,'INPUT_SIZE');x=json.loads(text);validate(x)
  if sys.argv[1:]==['--inject-failure']:raise RuntimeError('injected consumer failure')
  r=simulate(x);code=0
 except (json.JSONDecodeError,Refused) as e:r=dict(status='INPUT_REFUSED',reason=e.args[0] if isinstance(e,Refused) else 'JSON_PARSE',trace=[],intervals=[],events=[],counts=None);code=2
 except Exception as e:r=dict(status='EXECUTION_FAILURE',reason=type(e).__name__,message=str(e),trace=[],intervals=[],events=[],counts=None);code=1
 print(json.dumps(r,ensure_ascii=False,separators=(',',':')));return code
if __name__=='__main__':sys.exit(main())
