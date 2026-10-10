import sys,json,copy

def reject(reason):return {'observed':False,'reason':reason,'trace':[],'final':None,'summary':None},2
def run(x):
 if not isinstance(x,dict) or set(x)!={'mode','arrivals'} or x['mode'] not in ('epoch','seq-only'):return reject('invalid request')
 arrivals=x['arrivals']
 if not isinstance(arrivals,list) or not 1<=len(arrivals)<=5:return reject('invalid arrivals')
 for m in arrivals:
  if not isinstance(m,dict) or set(m)!={'device','epoch','seq','value'} or m['device']!='a' or any(type(m[k]) is not int for k in ('epoch','seq','value')) or not 1<=m['epoch']<=3 or not 1<=m['seq']<=99 or not 0<=m['value']<=999:return reject('invalid telemetry identity or value')
 latest=None;history=[];identities={};trace=[]
 for i,m in enumerate(arrivals,1):
  before=copy.deepcopy(latest);key=(m['device'],m['epoch'],m['seq']) if x['mode']=='epoch' else (m['device'],m['seq']);payload=json.dumps({'value':m['value']},sort_keys=True,separators=(',',':'));added=False;updated=False
  if key in identities:decision='DUPLICATE' if identities[key]==payload else 'CONFLICT'
  elif x['mode']=='seq-only' and latest is not None and m['seq']<=latest['seq']:decision='STALE_REJECT'
  else:
   identities[key]=payload;history.append(copy.deepcopy(m));added=True
   newer=latest is None or ((m['epoch'],m['seq'])>(latest['epoch'],latest['seq']) if x['mode']=='epoch' else m['seq']>latest['seq'])
   if newer:latest=copy.deepcopy(m);updated=True;decision='ACCEPT_LATEST'
   else:decision='ACCEPT_HISTORY'
  ids=[{'key':list(k),'payload':v} for k,v in identities.items()]
  trace.append({'arrival':i,'input':copy.deepcopy(m),'key':list(key),'decision':decision,'historyAdded':added,'latestUpdated':updated,'beforeLatest':before,'latest':copy.deepcopy(latest),'history':copy.deepcopy(history),'identities':copy.deepcopy(ids)})
 summary={'historyCount':len(history),'latestEpoch':latest['epoch'],'latestSeq':latest['seq'],'latestValue':latest['value'],'lastDecision':trace[-1]['decision'],'duplicateCount':sum(t['decision']=='DUPLICATE' for t in trace),'conflictCount':sum(t['decision']=='CONFLICT' for t in trace),'staleRejectedCount':sum(t['decision']=='STALE_REJECT' for t in trace)}
 return {'observed':True,'reason':None,'trace':trace,'final':{'latest':latest,'history':history,'identities':ids},'summary':summary},0
if __name__=='__main__':
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 try:o,code=run(x)
 except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(4)
 print(json.dumps(o));sys.exit(code)
