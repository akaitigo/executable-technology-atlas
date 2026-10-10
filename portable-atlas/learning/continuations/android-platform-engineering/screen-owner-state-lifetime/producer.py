"""Explicit finite owner model. No Android API, saved token or real process restart."""
import copy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
class Refused(Exception):pass
def validate(c):
 if c['mode'] not in ['scoped','global-leak','dead-owner-reuse']:raise Refused('MODE')
 events=c['events']
 if not isinstance(events,list) or len(events)>8:raise Refused('EVENTS_TYPE')
 for e in events:
  if not isinstance(e,dict) or set(e)!= {'op','target'}:raise Refused('EVENT_FIELDS')
  if e['op'] not in ['create','rotate','finish','tap','death','restart']:raise Refused('OP')
  if e['op'] in ['death','restart']:
   if e['target'] is not None:raise Refused('TARGET')
  elif e['target'] not in ['A','B']:raise Refused('TARGET')
def simulate(c):
 process=1;alive=True;serial=3;owners={'A':dict(owner='p1:A:1',view_generation=1,state=2),'B':dict(owner='p1:B:2',view_generation=1,state=1)};dead={};rows=[]
 def snapshot(step,event):return dict(step=step,event=event,process=process,alive=alive,owners=copy.deepcopy(owners))
 rows.append(snapshot(0,None))
 for step,e in enumerate(c['events'],1):
  op,target=e['op'],e['target']
  if op=='restart':
   if alive:raise Refused('PROCESS_ALIVE')
   process+=1;alive=True;serial=1
  elif not alive:raise Refused('PROCESS_DEAD')
  elif op=='death':owners.clear();dead.clear();serial=1;alive=False
  elif op=='create':
   if target in owners:raise Refused('OWNER_EXISTS')
   if c['mode']=='dead-owner-reuse' and target in dead:
    owners[target]=dead.pop(target);owners[target]['view_generation']+=1
   else:
    owners[target]=dict(owner='p%d:%s:%d'%(process,target,serial),view_generation=1,state=0);serial+=1
  else:
   if target not in owners:raise Refused('OWNER_ABSENT')
   if op=='finish':
    removed=owners.pop(target)
    if c['mode']=='dead-owner-reuse':dead[target]=removed
   elif op=='rotate':
    owners[target]['view_generation']+=1
    if c['mode']=='global-leak':
     for v in owners.values():v['state']=owners[target]['state']
   elif op=='tap':
    if owners[target]['state']>=9:raise Refused('STATE_RANGE')
    owners[target]['state']+=1
  rows.append(snapshot(step,e))
 return rows,copy.deepcopy(rows[-1])
def run(case,events_json=None):
 out=dict(case=case,input=None,status='INPUT_REFUSED',reason='',timeline=None,final=None)
 try:
  c=next((copy.deepcopy(c) for c in FIXTURE['cases'] if c['id']==case),None)
  if c is None:raise Refused('UNKNOWN_CASE')
  out['input']=c
  if events_json:
   try:c['events']=json.loads(events_json)
   except ValueError:raise Refused('EVENT_JSON')
  validate(c)
  if c['variant']=='execution-failure':raise RuntimeError('injected owner model failure')
  rows,final=simulate(c);out.update(timeline=rows,final=final,status={'scoped':'NORMAL','global-leak':'FAULT_GLOBAL_LEAK','dead-owner-reuse':'FAULT_DEAD_REUSE'}[c['mode']])
 except Refused as e:out['reason']=str(e)
 except Exception as e:out.update(status='EXECUTION_FAILURE',reason=str(e))
 return out
