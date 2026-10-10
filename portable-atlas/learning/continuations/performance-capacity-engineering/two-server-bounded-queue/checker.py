import pathlib,json,hashlib,sys
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parent
# Independent hand timing: no producer import and no event-loop reuse.
TIMES={'one-server':[(0,0,2),(0,2,4),(0,4,6),(0,6,8),(0,8,10)],'two-server':[(0,0,2),(0,0,2),(0,2,4),(0,2,4),(0,4,6)],'bounded-drop':[(0,0,2),(0,0,2),(0,2,4),None,None],'bounded-backpressure':[(0,0,2),(0,0,2),(0,2,4),(2,2,4),(2,4,6)]}
REFUSALS={'invalid-servers':'invalid servers','invalid-service':'invalid service','invalid-capacity':'invalid capacity','duplicate-id':'duplicate ID','unknown-policy':'invalid policy'}
IDS=list('ABCDE')
BASE={'jobs':IDS,'offeredAt':0,'service':2,'servers':2,'capacity':5,'policy':'drop'}
PATCH={'one-server':{'servers':1},'two-server':{},'bounded-drop':{'capacity':1},'bounded-backpressure':{'capacity':1,'policy':'backpressure'},'invalid-servers':{'servers':True},'invalid-service':{'service':0},'invalid-capacity':{'capacity':-1},'duplicate-id':{'jobs':['A','A']},'unknown-policy':{'policy':'retry'}}
def sha(b):return hashlib.sha256(b).hexdigest()
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
 assert (run/'stdout.json').read_bytes()==(run/'result.json').read_bytes()
 for name,h in d['sourceHashes'].items():assert sha((root/name).read_bytes())==h,name
 for name,v in json.loads((run/'artifacts.json').read_text())['files'].items():
  b=(run/name).read_bytes();assert sha(b)==v['sha256'] and len(b)==v['bytes'],name
 o=json.loads((root/'oracle.json').read_text())
 assert o['timings']=={k:[list(z) if z else None for z in v] for k,v in TIMES.items()} and o['refusals']==REFUSALS
 assert len(d['cases'])==9 and [c['id'] for c in d['cases']]==list(PATCH)
 for c in d['cases']:
  name=c['id'];folder=run/name
  inp=(folder/'input.json').read_bytes()
  assert json.loads(inp)=={**BASE,**PATCH[name]} and sha(inp)==c['inputSha256']
  assert (folder/'stdout.json').read_text()==c['stdout'] and (folder/'stderr.txt').read_text()==c['stderr']==''
  out=json.loads(c['stdout']);assert out==c['result']
  if name in REFUSALS:
   assert c['exitCode']==2 and out=={'accepted':False,'reason':REFUSALS[name],'jobs':None,'events':None,'states':None,'metrics':None};continue
  assert c['exitCode']==0 and out['accepted']
  times=TIMES[name];accepted=[i for i,z in enumerate(times) if z];dropped=[IDS[i] for i,z in enumerate(times) if not z]
  for i,j in enumerate(out['jobs']):
   z=times[i];assert j['id']==IDS[i] and j['offered']==0
   if z:
    a,s,f=z
    expected={'id':IDS[i],'offered':0,'admitted':a,'start':s,'finish':f,'server':i%2 if name!='one-server' else 0,'dropped':False,'producerWait':a,'queueWait':s-a,'serviceLatency':f-s,'admittedToFinish':f-a,'offeredToFinish':f}
    # In bounded-backpressure C,D start on servers0,1 and E on0, same index parity.
    assert j==expected,(name,j,expected)
   else:assert j=={'id':IDS[i],'offered':0,'admitted':None,'start':None,'finish':None,'server':None,'dropped':True}
  # Unit tick oracle: derive membership from fixed half-open time intervals.
  unit=[]
  for t in range(max(z[2] for z in times if z)+1):
   state={'tick':t,'inService':[IDS[i] for i,z in enumerate(times) if z and z[1]<=t<z[2]],'queue':[IDS[i] for i,z in enumerate(times) if z and z[0]<=t<z[1]],'producerWaiting':[IDS[i] for i,z in enumerate(times) if z and t<z[0]],'dropped':dropped,'finished':[IDS[i] for i,z in enumerate(times) if z and z[2]<=t]}
   unit.append(state)
  expectedStates=[v for v in unit if v['tick']%2==0]
  assert out['states']==expectedStates,(name,out['states'],expectedStates)
  for state in unit:
   observed=max((v for v in out['states'] if v['tick']<=state['tick']),key=lambda v:v['tick'])
   assert {k:v for k,v in observed.items() if k!='tick'}=={k:v for k,v in state.items() if k!='tick'}
  # Hand timeline event phases finish -> start existing queue -> admit/start.
  expectedEvents=[]
  servers={IDS[i]:i%2 if name!='one-server' else 0 for i,z in enumerate(times) if z}
  for t in range(0,len(unit),2):
   finishing=[i for i,z in enumerate(times) if z and z[2]==t]
   for i in sorted(finishing,key=lambda i:servers[IDS[i]]):expectedEvents.append({'tick':t,'type':'finish','id':IDS[i],'server':servers[IDS[i]]})
   for i,z in enumerate(times):
    if z and z[1]==t and z[0]<t:expectedEvents.append({'tick':t,'type':'start','id':IDS[i],'server':servers[IDS[i]]})
   for i,z in enumerate(times):
    if z and z[0]==t:
     expectedEvents.append({'tick':t,'type':'admit','id':IDS[i]})
     if z[1]==t:expectedEvents.append({'tick':t,'type':'start','id':IDS[i],'server':servers[IDS[i]]})
    elif not z and t==0:expectedEvents.append({'tick':0,'type':'drop','id':IDS[i]})
  assert out['events']==expectedEvents,(name,out['events'],expectedEvents)
  a=len(accepted)
  def avg(f):return str(Fraction(sum(f(times[i]) for i in accepted),a))
  expected={'offeredCount':5,'admittedCount':a,'finishedCount':a,'dropCount':5-a,'finishedPerOffered':str(Fraction(a,5)),'finishedPerAdmitted':'1','latencyCohort':'admitted/finished IDs only; dropped have no completion latency','latencyDenominator':a,'allOfferedMeanCompletionLatency':avg(lambda z:z[2]) if a==5 else None,'producerWaitMean':avg(lambda z:z[0]),'queueWaitMean':avg(lambda z:z[1]-z[0]),'serviceMean':'2','admittedToFinishMean':avg(lambda z:z[2]-z[0]),'offeredToFinishMean':avg(lambda z:z[2])}
  assert out['metrics']==expected,(name,out['metrics'],expected)
 return len(d['cases'])
if __name__=='__main__':
 check();print('PASS 9 fixtures; hand timeline + independent unit-tick states/events/cohorts/latency')
