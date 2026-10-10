"""Independent table transitions and canonical save tokens; imports no model."""
import json
EDGES={('ABSENT','create'):'CREATED',('DESTROYED','create'):'CREATED',('DEAD','create'):'CREATED',('FINISHED','create'):'CREATED',('CREATED','start'):'STARTED',('STARTED','resume'):'RESUMED',('PAUSED','resume'):'RESUMED',('RESUMED','tap'):'RESUMED',('RESUMED','pause'):'PAUSED',('PAUSED','stop'):'STOPPED',('PAUSED','save'):'PAUSED',('STOPPED','save'):'STOPPED',('STOPPED','destroy_rotate'):'DESTROYED',('STOPPED','process_death'):'DEAD',('STOPPED','finish'):'FINISHED',('STOPPED','restart'):'CREATED',('STOPPED','drop_saved'):'STOPPED',('DEAD','drop_saved'):'DEAD',('DESTROYED','drop_saved'):'DESTROYED'}
TOKENS=tuple('{"version":1,"counter":'+str(n)+'}' for n in range(10))
NEXT=(1,2,3,4,5,6,7,8,9,None)
CALLBACKS={'create':'onCreate(saved-or-null)','start':'onStart','resume':'onResume','pause':'onPause','stop':'onStop','save':'onSaveInstanceState (explicit model event)','destroy_rotate':'onDestroy','finish':'onDestroy','restart':'onRestart (then separate start)'}
def restore(text):
 if text is None:return 0,None
 try:size=len(text.encode())
 except UnicodeEncodeError:return None,'saved_encoding'
 if size>128:return None,'saved_size'
 duplicates=[]
 def object_table(entries):
  keys=[k for k,v in entries]
  if len(keys)!=len(set(keys)):duplicates.append(True)
  return dict(entries)
 try:obj=json.loads(text,object_pairs_hook=object_table)
 except (ValueError,TypeError):return None,'saved_json'
 if duplicates:return None,'saved_duplicate_key'
 if not isinstance(obj,dict) or set(obj)!= {'counter','version'}:return None,'saved_schema'
 if type(obj['version'])!=int or obj['version']!=1:return None,'saved_version'
 if type(obj['counter'])!=int or obj['counter'] not in range(10):return None,'saved_counter'
 return obj['counter'],None

def expected(spec,variant='serialized'):
 phase='ABSENT';count=None;token=spec['saved'];instance=0;process=1;alive=True;trace=[]
 def snapshot():return dict(stage=phase,counter=count,saved=token,instance=instance,process=process,alive=alive)
 for n,event in enumerate(spec['events']):
  before=snapshot();reason=None;target=EDGES.get((phase,event))
  if target is None:reason='invalid_transition'
  elif event=='tap' and NEXT[count] is None:reason='counter_limit'
  elif event=='create':value,reason=restore(token)
  if reason:return dict(status='rejected',state=before,steps=len(trace),trace=trace,fault=dict(reason=reason,event_index=n,event=event))
  phase=target
  if event=='create':
   count=value if variant=='serialized' else 0;instance+=1
   if not alive:process+=1;alive=True
  if event=='tap':count=NEXT[count]
  if event=='save':token=TOKENS[count] if variant=='serialized' else None
  if event in ('destroy_rotate','process_death','finish'):count=None
  if event=='process_death':alive=False
  if event in ('drop_saved','finish'):token=None
  trace.append(dict(step=n,event=event,before=before,after=snapshot(),callback=CALLBACKS.get(event)))
 return dict(status='accepted',state=snapshot(),steps=len(trace),trace=trace,fault=None)
