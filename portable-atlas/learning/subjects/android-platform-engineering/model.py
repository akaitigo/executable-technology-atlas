"""Finite lifecycle/saved-state model, NOT an Android runtime."""
import copy,json
OPS=('create','start','resume','tap','pause','stop','save','destroy_rotate','process_death','finish','restart','drop_saved')
class Refused(ValueError):pass
def input_spec(spec):
 if type(spec) is not dict or set(spec)!= {'saved','events'}:raise Refused('input_keys')
 if spec['saved'] is not None and type(spec['saved']) is not str:raise Refused('saved_text_or_null')
 if type(spec['events']) is not list or not 1<=len(spec['events'])<=32:raise Refused('events_1_to_32')
 if any(type(e) is not str or e not in OPS for e in spec['events']):raise Refused('unknown_event')
 return spec

def no_duplicates(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise Refused('saved_duplicate_key')
  out[k]=v
 return out

def decode(saved):
 if saved is None:return 0
 try:size=len(saved.encode('utf-8'))
 except UnicodeEncodeError:raise Refused('saved_encoding')
 if size>128:raise Refused('saved_size')
 try:data=json.loads(saved,object_pairs_hook=no_duplicates)
 except (ValueError,TypeError) as e:
  if isinstance(e,Refused):raise
  raise Refused('saved_json')
 if type(data) is not dict or set(data)!= {'version','counter'}:raise Refused('saved_schema')
 if type(data['version']) is not int or data['version']!=1:raise Refused('saved_version')
 if type(data['counter']) is not int or not 0<=data['counter']<=9:raise Refused('saved_counter')
 return data['counter']

def initial(saved):return {'stage':'ABSENT','counter':None,'saved':saved,'instance':0,'process':1,'alive':True}
def step(state,event,variant):
 s=copy.deepcopy(state);stage=s['stage'];callback=None
 if event=='create':
  if stage not in ('ABSENT','DESTROYED','DEAD','FINISHED'):raise Refused('invalid_transition')
  restored=decode(s['saved'])
  if not s['alive']:s['process']+=1;s['alive']=True
  s['counter']=restored if variant=='serialized' else 0;s['instance']+=1;s['stage']='CREATED';callback='onCreate(saved-or-null)'
 elif event=='start':
  if stage!='CREATED':raise Refused('invalid_transition')
  s['stage']='STARTED';callback='onStart'
 elif event=='resume':
  if stage not in ('STARTED','PAUSED'):raise Refused('invalid_transition')
  s['stage']='RESUMED';callback='onResume'
 elif event=='tap':
  if stage!='RESUMED':raise Refused('invalid_transition')
  if s['counter']==9:raise Refused('counter_limit')
  s['counter']+=1
 elif event=='pause':
  if stage!='RESUMED':raise Refused('invalid_transition')
  s['stage']='PAUSED';callback='onPause'
 elif event=='stop':
  if stage!='PAUSED':raise Refused('invalid_transition')
  s['stage']='STOPPED';callback='onStop'
 elif event=='save':
  if stage not in ('PAUSED','STOPPED'):raise Refused('invalid_transition')
  s['saved']=json.dumps({'version':1,'counter':s['counter']},separators=(',',':')) if variant=='serialized' else None;callback='onSaveInstanceState (explicit model event)'
 elif event in ('destroy_rotate','finish'):
  if stage!='STOPPED':raise Refused('invalid_transition')
  s['stage']='DESTROYED' if event=='destroy_rotate' else 'FINISHED';s['counter']=None;callback='onDestroy'
  if event=='finish':s['saved']=None
 elif event=='process_death':
  if stage!='STOPPED':raise Refused('invalid_transition')
  s['stage']='DEAD';s['counter']=None;s['alive']=False
 elif event=='restart':
  if stage!='STOPPED':raise Refused('invalid_transition')
  s['stage']='CREATED';callback='onRestart (then separate start)'
 elif event=='drop_saved':
  if stage not in ('STOPPED','DEAD','DESTROYED'):raise Refused('invalid_transition')
  s['saved']=None
 return s,callback

def run(spec,variant='serialized'):
 state=initial(spec['saved']);trace=[]
 for n,event in enumerate(spec['events']):
  try:after,callback=step(state,event,variant)
  except Refused as e:return {'status':'rejected','state':state,'steps':len(trace),'trace':trace,'fault':{'reason':str(e),'event_index':n,'event':event}}
  trace.append({'step':n,'event':event,'before':state,'after':after,'callback':callback});state=after
 return {'status':'accepted','state':state,'steps':len(trace),'trace':trace,'fault':None}

def analyze(spec):
 try:input_spec(spec)
 except Refused as e:return {'status':'rejected','phase':'input','reason':str(e),'variants':{}}
 variants={v:run(spec,v) for v in ('serialized','ephemeral')}
 return {'status':variants['serialized']['status'],'phase':'execution','variants':variants}
