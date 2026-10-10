import json,sys,copy

def run(x):
 def refuse(reason):return {'observed':False,'reason':reason,'summary':None,'trace':[]},2
 if type(x)!=dict or set(x)!={'mode','lag','allowedLateness','events'} or x['mode'] not in ('min','max-fault'):return refuse('schema/mode; idle-auto not supported')
 if type(x['lag'])!=int or not 0<=x['lag']<=20 or type(x['allowedLateness'])!=int or not 0<=x['allowedLateness']<=20:return refuse('lag/allowedLateness integer0..20; bool forbidden')
 es=x['events']
 if type(es)!=list or not 1<=len(es)<=12:return refuse('finite event count1..12')
 seen=set()
 for e in es:
  if type(e)!=dict or set(e)!={'id','partition','time','value'}:return refuse('event schema')
  if type(e['id'])!=str or not 1<=len(e['id'])<=40 or e['id'] in seen:return refuse('unique nonempty ID')
  seen.add(e['id'])
  if e['partition'] not in ('p0','p1'):return refuse('fixed partitions p0/p1 only')
  if type(e['time'])!=int or not 0<=e['time']<=100 or type(e['value'])!=int or not 0<=e['value']<=100:return refuse('time/value integer0..100; bool/nonfinite forbidden')
 maxSeen={'p0':None,'p1':None};wm=None;windows={};accepted=[];dropped=[];lateAccepted=[];trace=[]
 for step,e in enumerate(es,1):
  start=(e['time']//10)*10;end=start+10;before=wm;late=before is not None and e['time']<before;admit=before is None or before<end+x['allowedLateness'];fires=[];finals=[]
  if admit:
   w=windows.setdefault(start,{'start':start,'end':end,'sum':0,'ids':[],'initialFired':False,'finalized':False,'finalizedStep':None});w['sum']+=e['value'];w['ids'].append(e['id']);accepted.append(e['id'])
   if late:lateAccepted.append(e['id'])
   if w['initialFired']:fires.append({'start':start,'sum':w['sum'],'kind':'late-update'})
  else:dropped.append(e['id'])
  p=e['partition'];maxSeen[p]=e['time'] if maxSeen[p] is None else max(maxSeen[p],e['time']);part={p:(t-x['lag'] if t is not None else None) for p,t in maxSeen.items()};values=[t for t in part.values() if t is not None]
  candidate=(min(values) if len(values)==2 else None) if x['mode']=='min' else max(values);wm=candidate if wm is None else max(wm,candidate) if candidate is not None else wm
  for start,w in sorted(windows.items()):
   if wm is not None and wm>=w['end'] and not w['initialFired']:w['initialFired']=True;fires.append({'start':start,'sum':w['sum'],'kind':'initial'})
   if wm is not None and wm>=w['end']+x['allowedLateness'] and not w['finalized']:w['finalized']=True;w['finalizedStep']=step;finals.append(start)
  trace.append({'step':step,'event':copy.deepcopy(e),'windowStart':(e['time']//10)*10,'beforeWatermark':before,'late':late,'decision':'ACCEPT' if admit else 'DROP_FINALIZED','maxSeen':dict(maxSeen),'partitionWatermarks':part,'watermark':wm,'firedNow':fires,'finalizedNow':finals,'windows':copy.deepcopy([w for _,w in sorted(windows.items())])})
 return {'observed':True,'reason':None,'trace':trace,'summary':{'accepted':accepted,'dropped':dropped,'lateAccepted':lateAccepted,'watermark':wm,'windows':[w for _,w in sorted(windows.items())],'mode':x['mode'],'lag':x['lag'],'allowedLateness':x['allowedLateness'],'endFlush':False}},0
if __name__=='__main__':
 if sys.argv[1:]:sys.exit(2)
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 o,code=run(x);print(json.dumps(o));sys.exit(code)
