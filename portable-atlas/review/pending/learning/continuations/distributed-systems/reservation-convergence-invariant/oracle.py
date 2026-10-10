"""Independent prefix-set oracle. Imports no model/producer helpers."""
import json,sys

def expected(x,policy):
 req=x['requests'];order=x['serial_order'];cap=x['capacity'];schedule=x['schedule']
 origins={r['id']:r['replica'] for r in req}
 # Decisions from ranks in fixed request list or explicit serial list, no receiver transitions.
 opt={r['id']:('accepted' if sum(t['replica']==r['replica'] for t in req[:i])<cap else 'rejected') for i,r in enumerate(req)}
 serial={v:('accepted' if i<cap else 'rejected') for i,v in enumerate(order)}
 plan=[('init',None)]+[('request',r['id']) for r in req]+[('recover',None)]
 if policy=='deferred':plan += [('adjudicate',v) for v in order]
 plan += [('publish',None)]+[('deliver',m) for m in schedule]
 rows=[]
 for i,(stage,arg) in enumerate(plan):
  prefix=plan[:i+1];responses=[]
  for st,v in prefix:
   if st in ('request','adjudicate'):
    state=(opt[v] if policy=='optimistic' else 'pending') if st=='request' else serial[v]
    responses.append(dict(id=v,replica=origins[v],status=state,phase=st))
  latest={r['id']:r['status'] for r in responses}
  accepted={r['id'] for r in responses if r['status']=='accepted'}
  originsets={n:{v for v in accepted if origins[v]==n} for n in ('A','B')}
  sent=any(st=='publish' for st,v in prefix)
  messages={m:sorted(originsets[m[0]]) for m in ('A>B','B>A')} if sent else {}
  delivered={n:{v for st,v in prefix if st=='deliver' and v[-1]==n} for n in ('A','B')}
  local={n:sorted(originsets[n]|set().union(*(set(messages[m]) for m in delivered[n]))) for n in ('A','B')}
  response=responses[-1] if stage in ('request','adjudicate') else None
  rows.append(dict(step=i,event=stage+(':'+arg if arg is not None else ''),link_up=any(st=='recover' for st,v in prefix),local_decision=response if stage=='request' else None,response_event=response,response_history=responses,latest_responses=latest,accepted_returned=sorted(accepted),local_sets=local,pending_ids=sorted(v for v,s in latest.items() if s=='pending'),messages=messages,delivered_set={n:sorted(delivered[n]) for n in ('A','B')},delivery_count={n:sum(st=='deliver' and v[-1]==n for st,v in prefix) for n in ('A','B')},converged=local['A']==local['B'],global_business_ok=len(accepted)<=cap,replica_bounds={n:len(local[n])<=cap for n in ('A','B')}))
 final=rows[-1]
 return dict(trace=rows,final=final,all_messages_delivered=set(schedule)=={'A>B','B>A'},response_preserved=True)

def check(result,x,literal=None):
 if literal and literal.get('status')=='EXECUTION_FAILED':
  assert result['status']=='EXECUTION_FAILED';return
 assert result==dict(status='OBSERVED',input_echo=x,policies={p:expected(x,p) for p in ('optimistic','deferred')})
 if literal:
  for policy,want in literal.items():
   f=result['policies'][policy]['final'];assert [f['accepted_returned'],f['local_sets'],f['converged'],f['global_business_ok'],len(f['pending_ids'])]==want
 for pol in result['policies'].values():
  before=set()
  for row in pol['trace']:
   assert before<=set(row['accepted_returned']);before=set(row['accepted_returned'])
if __name__=='__main__':
 try:
  a=json.load(sys.stdin);check(a['result'],a['input']);print(json.dumps({'status':'passed'}))
 except Exception as e:print(json.dumps({'status':'failed','reason':type(e).__name__}));sys.exit(1)
