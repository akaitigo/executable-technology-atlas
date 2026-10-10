"""Event-driven reference and interval-set literal expansion; no model import."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def expand(x,accepted,dropped,intervals):
 h=x['horizon'];jobs={e['id']:e for e in x['events']};done=[i for i,s,end in sorted(intervals,key=lambda a:a[2]) if end<=h];starts={i:(s,end) for i,s,end in intervals};records=[]
 for e in x['events']:
  id=e['id'];s,end=starts.get(id,(None,None));finished=end is not None and end<=h
  records.append(dict(id=id,arrival=e['tick'],priority=e['priority'],service=e['service'],accepted=id in accepted,start=s,plannedEnd=end,end=end if finished else None,wait=None if s is None else s-e['tick'],response=end-e['tick'] if finished else None,state='DROPPED' if id in dropped else 'COMPLETED' if finished else 'RUNNING' if s is not None else 'WAITING'))
 rows=[]
 for t in range(h+1):
  prioraccepted=[id for id in accepted if jobs[id]['tick']<=t];priordrops=[id for id in dropped if jobs[id]['tick']<=t];priorcompleted=[id for id in done if starts[id][1]<=t];active=[(id,s,end) for id,s,end in intervals if s<=t<end]
  queue=[id for id in prioraccepted if id not in starts or starts[id][0]>t]
  rows.append(dict(tick=t,arrivals=[e['id'] for e in x['events'] if e['tick']==t],accepted=[id for id in accepted if jobs[id]['tick']==t],dropped=[id for id in dropped if jobs[id]['tick']==t],completed=[id for id in done if starts[id][1]==t],started=[id for id,s,end in intervals if s==t],queue=queue,running=None if not active else dict(id=active[0][0],start=active[0][1],plannedEnd=active[0][2],remaining=active[0][2]-t),counts=dict(arrived=sum(e['tick']<=t for e in x['events']),accepted=len(prioraccepted),dropped=len(priordrops),completed=len(priorcompleted)),reportedCompleted=len(prioraccepted) if x['report']=='accept-fault' else len(priorcompleted)))
 return dict(status='OBSERVED',input=x,preemption=False,clock='synthetic integer tick; no wall-time simulation',accepted=accepted,dropped=dropped,completed=done,reportedCompleted=accepted[:] if x['report']=='accept-fault' else done[:],counts=dict(arrived=len(x['events']),accepted=len(accepted),dropped=len(dropped),completed=len(done),unfinished=len(accepted)-len(done)),intervals=[dict(id=id,start=s,end=end,completed=end<=h) for id,s,end in intervals],events=records,trace=rows)
def reference(x):
 # Advance ONLY to arrival, service end, or horizon; no producer tick loop.
 pending=[];admitted=[];lost=[];intervals=[];running=None;t=0
 while True:
  if running and running[2]==t:running=None
  batch=[(n,e) for n,e in enumerate(x['events']) if e['tick']==t]
  for n,e in batch:
   if len(pending)==x['capacity']:lost.append(e['id'])
   else:pending.append((n,e));admitted.append(e['id'])
  if running is None and pending and t<x['horizon']:
   selected=sorted(pending,key=lambda a:a[0] if x['policy']=='fifo' else (-a[1]['priority'],a[0]))[0]
   pending.remove(selected);e=selected[1];running=[e['id'],t,t+e['service']];intervals.append(running)
  if t==x['horizon']:break
  future=[e['tick'] for e in x['events'] if e['tick']>t]+([running[2]] if running else [])+[x['horizon']]
  t=min(n for n in future if n>t)
 return expand(x,admitted,lost,intervals)
def check(result,x,literal=None):
 if literal and literal['reason']:
  expected='EXECUTION_FAILURE' if literal['reason']=='RuntimeError' else 'INPUT_REFUSED'
  assert result['status']==expected and result['reason']==literal['reason'] and result['trace']==[] and result['counts'] is None
  return
 assert result==reference(x),(result,reference(x))
 if literal is not None:assert result==expand(x,literal['accepted'],literal['drops'],literal['intervals'])
def main():
 x=json.loads(sys.stdin.read());r=x['result'];check(r,x['input'],x.get('literal'));print(json.dumps(dict(status='passed',independent=True)))
if __name__=='__main__':main()
