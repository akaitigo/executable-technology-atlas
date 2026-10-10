import json,sys,re,copy

def validate(x):
 if type(x)!=dict or set(x)!={'capacity','requests','serial_order','schedule'}:raise ValueError('FIELDS')
 if type(x['capacity'])!=int or not 0<=x['capacity']<=3:raise ValueError('CAPACITY')
 req=x['requests'];order=x['serial_order'];schedule=x['schedule']
 if type(req)!=list or len(req)>4:raise ValueError('REQUESTS')
 ids=[]
 for r in req:
  if type(r)!=dict or set(r)!={'replica','id'} or r['replica'] not in ('A','B') or type(r['id'])!=str or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,15}',r['id']):raise ValueError('REQUEST')
  ids.append(r['id'])
 if len(set(ids))!=len(ids):raise ValueError('DUPLICATE_ID')
 if type(order)!=list or any(type(v)!=str for v in order) or len(order)!=len(ids) or set(order)!=set(ids):raise ValueError('SERIAL_ORDER')
 if type(schedule)!=list or len(schedule)>6 or any(type(v)!=str or v not in ('A>B','B>A') for v in schedule):raise ValueError('SCHEDULE')
 return x

def simulate(x,policy):
 cap=x['capacity'];local={'A':set(),'B':set()};history=[];latest={};delivered={'A':set(),'B':set()};count={'A':0,'B':0};messages={};trace=[];link=False;global_accepted=set()
 def response(r,status,phase):
  e=dict(id=r['id'],replica=r['replica'],status=status,phase=phase);history.append(e);latest[r['id']]=status
  if status=='accepted':global_accepted.add(r['id']);local[r['replica']].add(r['id'])
  return e
 def record(event,decision=None,resp=None):
  trace.append(copy.deepcopy(dict(step=len(trace),event=event,link_up=link,local_decision=decision,response_event=resp,response_history=history,latest_responses=latest,accepted_returned=sorted(global_accepted),local_sets={n:sorted(local[n]) for n in local},pending_ids=sorted(v for v,s in latest.items() if s=='pending'),messages=messages,delivered_set={n:sorted(delivered[n]) for n in delivered},delivery_count=count,converged=local['A']==local['B'],global_business_ok=len(global_accepted)<=cap,replica_bounds={n:len(local[n])<=cap for n in local})))
 record('init')
 for r in x['requests']:
  status='pending' if policy=='deferred' else ('accepted' if len(local[r['replica']])<cap else 'rejected')
  e=response(r,status,'request');record('request:'+r['id'],e,e)
 link=True;record('recover')
 if policy=='deferred':
  for v in x['serial_order']:
   r=next(r for r in x['requests'] if r['id']==v);e=response(r,'accepted' if len(global_accepted)<cap else 'rejected','adjudicate');record('adjudicate:'+v,resp=e)
 messages={m:sorted(local[m[0]]) for m in ('A>B','B>A')};record('publish')
 for m in x['schedule']:
  n=m[-1];local[n].update(messages[m]);delivered[n].add(m);count[n]+=1;record('deliver:'+m)
 return dict(trace=trace,final=trace[-1],all_messages_delivered=all(m in x['schedule'] for m in messages),response_preserved=True)

def run(x):
 validate(x);return dict(status='OBSERVED',input_echo=x,policies={p:simulate(x,p) for p in ('optimistic','deferred')})
if __name__=='__main__':
 try:
  x=validate(json.load(sys.stdin))
  if sys.argv[1:]==['--fail']:raise RuntimeError('INJECTED_PRODUCER_FAILURE')
  if sys.argv[1:]:raise ValueError('ARGUMENT')
  print(json.dumps(run(x)))
 except (ValueError,TypeError,KeyError) as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e))));sys.exit(2)
 except Exception as e:print(json.dumps(dict(status='EXECUTION_FAILED',reason=type(e).__name__)));sys.exit(3)
