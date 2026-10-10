import json,sys
from fractions import Fraction
def model(x):
 def integer(v):return type(v) is int
 if not integer(x['servers']) or x['servers'] not in (1,2):raise ValueError('invalid servers')
 if not integer(x['service']) or not 1<=x['service']<=10:raise ValueError('invalid service')
 if not integer(x['capacity']) or not 0<=x['capacity']<=20:raise ValueError('invalid capacity')
 if x['policy'] not in ('drop','backpressure'):raise ValueError('invalid policy')
 ids=x['jobs']
 if not isinstance(ids,list) or not 1<=len(ids)<=20 or any(not isinstance(i,str) or not i or len(i)>16 for i in ids):raise ValueError('invalid jobs')
 if len(set(ids))!=len(ids):raise ValueError('duplicate ID')
 if type(x['offeredAt']) is not int or x['offeredAt']!=0:raise ValueError('invalid offeredAt')
 jobs={i:{'id':i,'offered':0,'admitted':None,'start':None,'finish':None,'server':None,'dropped':False} for i in ids}
 pending=list(ids);queue=[];active={};done=[];dropped=[];events=[];states=[];t=0
 def start(i,s):
  jobs[i].update(start=t,finish=t+x['service'],server=s)
  active[s]=i;events.append({'tick':t,'type':'start','id':i,'server':s})
 while True:
  for s in sorted(list(active)):
   i=active[s]
   if jobs[i]['finish']==t:
    del active[s];done.append(i);events.append({'tick':t,'type':'finish','id':i,'server':s})
  for s in range(x['servers']):
   if s not in active and queue:start(queue.pop(0),s)
  while pending:
   free=[s for s in range(x['servers']) if s not in active]
   if not free and len(queue)>=x['capacity']:
    if x['policy']=='backpressure':break
    i=pending.pop(0);jobs[i]['dropped']=True;dropped.append(i)
    events.append({'tick':t,'type':'drop','id':i});continue
   i=pending.pop(0);jobs[i]['admitted']=t;events.append({'tick':t,'type':'admit','id':i})
   if free:start(i,free[0])
   else:queue.append(i)
  states.append({'tick':t,'inService':[active[s] for s in sorted(active)],'queue':list(queue),'producerWaiting':list(pending),'dropped':list(dropped),'finished':list(done)})
  if not active:break
  t=min(jobs[i]['finish'] for i in active.values())
 accepted=[jobs[i] for i in ids if not jobs[i]['dropped']]
 def mean(field):
  vals=[j[field] for j in accepted]
  return str(Fraction(sum(vals),len(vals))) if vals else None
 for j in accepted:
  j.update(producerWait=j['admitted']-j['offered'],queueWait=j['start']-j['admitted'],serviceLatency=j['finish']-j['start'],admittedToFinish=j['finish']-j['admitted'],offeredToFinish=j['finish']-j['offered'])
 n=len(ids);a=len(accepted)
 return {'accepted':True,'jobs':list(jobs.values()),'events':events,'states':states,
 'metrics':{'offeredCount':n,'admittedCount':a,'finishedCount':len(done),'dropCount':len(dropped),'finishedPerOffered':str(Fraction(len(done),n)),'finishedPerAdmitted':str(Fraction(len(done),a)) if a else None,'latencyCohort':'admitted/finished IDs only; dropped have no completion latency','latencyDenominator':a,'allOfferedMeanCompletionLatency':mean('offeredToFinish') if a==n else None,'producerWaitMean':mean('producerWait'),'queueWaitMean':mean('queueWait'),'serviceMean':mean('serviceLatency'),'admittedToFinishMean':mean('admittedToFinish'),'offeredToFinishMean':mean('offeredToFinish')}}
if __name__=='__main__':
 try:
  x=json.load(sys.stdin);out=model(x)
 except (ValueError,KeyError,TypeError) as e:out={'accepted':False,'reason':str(e),'jobs':None,'events':None,'states':None,'metrics':None}
 print(json.dumps(out,ensure_ascii=False))
 sys.exit(0 if out['accepted'] else 2)
