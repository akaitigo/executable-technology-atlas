import sys
sys.dont_write_bytecode=True
import re,hmac,hashlib,copy
KEY=b'atomic-admission-public-fixture-key-v1'
SCHEDULES={
 'split-1':['Ac','Aw','Bc','Bw'], 'split-2':['Ac','Bc','Aw','Bw'],
 'split-3':['Ac','Bc','Bw','Aw'], 'split-4':['Bc','Ac','Aw','Bw'],
 'split-5':['Bc','Ac','Bw','Aw'], 'split-6':['Bc','Bw','Ac','Aw'],
 'atomic-AB':['A','B'],'atomic-BA':['B','A']}
def valid_id(v):return type(v) is str and re.fullmatch(r'[A-Z0-9_-]{1,16}',v) is not None
def validate(f):
 if type(f) is not dict or set(f)!={'id','label','requests','seen'}:raise ValueError('exact fixture keys')
 if type(f['id']) is not str or type(f['label']) is not str:raise ValueError('fixture metadata')
 if type(f['seen']) is not list or len(f['seen'])>16 or not all(valid_id(v) for v in f['seen']) or len(set(f['seen']))!=len(f['seen']):raise ValueError('seen IDs')
 if type(f['requests']) is not list or len(f['requests'])!=2:raise ValueError('two requests')
 for r in f['requests']:
  if type(r) is not dict or set(r)!={'id','payload','tag'}:raise ValueError('exact request keys')
  if not valid_id(r['id']):raise ValueError('request ID')
  if type(r['payload']) is not str:raise ValueError('payload string')
  try:p=r['payload'].encode('utf-8')
  except UnicodeError:raise ValueError('payload UTF-8')
  if len(p)>64:raise ValueError('payload bytes')
  if type(r['tag']) is not str or re.fullmatch('[0-9a-f]{64}',r['tag']) is None:raise ValueError('tag hex64')
def authenticated(r):
 actual=hmac.new(KEY,r['id'].encode('ascii')+b'\0'+r['payload'].encode('utf-8'),hashlib.sha256).hexdigest()
 return hmac.compare_digest(actual,r['tag'])
def run(f,schedule):
 validate(f)
 if type(schedule) is not str or schedule not in SCHEDULES:raise ValueError('schedule')
 seen=set(f['seen']);states={n:dict(id=r['id'],authenticated=authenticated(r),cached_absent=None,status='pending') for n,r in zip('AB',f['requests'])}
 count=0;trace=[]
 def snapshot(event):trace.append(dict(event=event,requests=copy.deepcopy(states),accepted_count=count,seen=sorted(seen)))
 snapshot('initial')
 for event in SCHEDULES[schedule]:
  s=states[event[0]]
  if not s['authenticated']:s['status']='invalid_mac'
  elif len(event)==1:
   s['cached_absent']=s['id'] not in seen
   s['status']='accepted' if s['cached_absent'] else 'replay'
   if s['cached_absent']:seen.add(s['id']);count+=1
  elif event[1]=='c':s['cached_absent']=s['id'] not in seen;s['status']='checked'
  else:
   s['status']='accepted' if s['cached_absent'] else 'replay'
   if s['cached_absent']:seen.add(s['id']);count+=1
  snapshot(event)
 return dict(fixture=f['id'],schedule=schedule,accepted_count=count,seen=sorted(seen),trace=trace)
