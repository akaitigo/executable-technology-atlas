"""Finite logical ISR offload, no real IRQ, RTOS or physical timing."""
import json,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
class Refused(Exception):pass
def validate(c):
 cap=c['capacity'];mode=c['mode'];ev=c['events']
 if type(cap) is not int or not 0<=cap<=3:raise Refused('CAPACITY')
 if mode not in ['queue','slot-overwrite']:raise Refused('MODE')
 if mode=='slot-overwrite' and cap!=2:raise Refused('MODE_CAPACITY')
 if not isinstance(ev,list) or len(ev)>3:raise Refused('EVENTS_TYPE')
 ids=[];ticks=[]
 for e in ev:
  if not isinstance(e,dict) or set(e)!= {'id','tick'}:raise Refused('EVENT_FIELDS')
  if type(e['id']) is not int or not 0<=e['id']<=2:raise Refused('EVENT_ID')
  if type(e['tick']) is not int or not 0<=e['tick']<=2:raise Refused('EVENT_TICK')
  if e['id'] in ids:raise Refused('DUPLICATE_ID')
  if e['tick'] in ticks:raise Refused('DUPLICATE_TICK')
  ids.append(e['id']);ticks.append(e['tick'])
 if ticks!=sorted(ticks):raise Refused('EVENT_ORDER')
def simulate(c):
 q=[];arrived=[];accepted=[];dropped=[];processed=[];lost=[];completions={};timeline=[]
 for tick in range(6):
  for event in c['events']:
   if event['tick']!=tick:continue
   id=event['id'];arrived.append(id)
   if c['mode']=='slot-overwrite':
    if q:lost.append(q[0])
    q=[id];accepted.append(id)
   elif len(q)>=c['capacity']:dropped.append(id)
   else:q.append(id);accepted.append(id)
  if tick>=3 and q:
   id=q.pop(0);processed.append(id);completions[str(id)]=tick
  timeline.append(dict(tick=tick,queue=q[:],arrived=arrived[:],accepted=accepted[:],dropped=dropped[:],processed=processed[:],lost=lost[:],completions=dict(completions)))
 return timeline,dict(arrived=len(arrived),accepted=len(accepted),dropped=len(dropped),processed=len(processed),lost=len(lost),pending=len(q))
def run(case,events_json=None):
 out=dict(case=case,input=None,status='INPUT_REFUSED',reason='',timeline=None,counts=None)
 try:
  c=next((copy.deepcopy(c) for c in FIXTURE['cases'] if c['id']==case),None)
  if c is None:raise Refused('UNKNOWN_CASE')
  out['input']=c
  if events_json:
   try:c['events']=json.loads(events_json)
   except ValueError:raise Refused('EVENT_JSON')
  validate(c)
  if c['variant']=='execution-failure':raise RuntimeError('injected offload model failure')
  out['timeline'],out['counts']=simulate(c);out['status']='FAULT_OVERWRITE' if c['mode']=='slot-overwrite' else 'NORMAL'
 except Refused as e:out['reason']=str(e)
 except Exception as e:out['status']='EXECUTION_FAILURE';out['reason']=str(e)
 return out
