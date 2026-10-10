# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform

def valid(t):
 return isinstance(t,list) and len(t)==3 and all(type(v) is int for v in t) and -3<=t[0]<=t[1]<=3 and -4<=t[2]<=4

def rank(t):return [sum(abs(v) for v in t)]+[abs(v) for v in t]+t

def evaluate(t,variant):
 lo,hi,x=t;members=list(range(lo,hi));expected=x in members
 actual={'original':lo<=x<hi,'M1':lo<x<hi,'M2':lo<=x<=hi}[variant]
 return dict(input=t[:],set_members=members,expected=expected,actual=actual,failed=expected!=actual)

def domain():return [[lo,hi,x] for lo in range(-3,4) for hi in range(lo,4) for x in range(-4,5)]

def candidates(t):
 for i,name in enumerate(['lo','hi','x']):
  if t[i]==0:continue
  choices=[0,t[i]-(1 if t[i]>0 else -1)]
  for j,v in enumerate(dict.fromkeys(choices)):
   c=t[:];c[i]=v
   yield name,('zero' if j==0 else 'step'),c

def shrink(t,variant):
 current=t[:];trace=[];round_no=0
 while True:
  accepted=False
  for coordinate,rule,c in candidates(current):
   schema=valid(c);ev=evaluate(c,variant) if schema else None
   decision='SCHEMA_INVALID' if not schema else ('ACCEPT' if ev['failed'] and rank(c)<rank(current) else 'LOST_FAILURE')
   trace.append(dict(round=round_no,from_input=current[:],coordinate=coordinate,rule=rule,candidate=c,valid=schema,expected=ev['expected'] if ev else None,actual=ev['actual'] if ev else None,failed=ev['failed'] if ev else None,decision=decision,rank=rank(c)))
   if decision=='ACCEPT':current=c;accepted=True;round_no+=1;break
  if not accepted:return current,trace

def run(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 out=dict(mode='INDEPENDENT_FINITE_MODEL',started_utc=start,python=platform.python_version(),inputs=config)
 if not isinstance(config,dict) or set(config)!= {'generator','seed','count','variant'} or config.get('generator') not in ('uniform','boundary') or config.get('variant') not in ('original','M1','M2') or type(config.get('seed')) is not int or config['seed'] not in (1,7) or type(config.get('count')) is not int or config['count'] not in (2,4):
  out.update(status='REFUSED_INPUT',reason='exact keys generator/seed/count/variant; generator uniform/boundary, seed integer1/7, count integer2/4, variant original/M1/M2',generated=[],shrink_trace=[],enumeration=[])
 else:
  g,seed,n,v=[config[k] for k in ['generator','seed','count','variant']];d=domain();state=seed;generated=[];draws=[]
  while len(generated)<n:
   state=(5*state+1)%256;draws.append(dict(state=state,accepted=state<252))
   if state>=252:continue
   t=d[state][:]
   if g=='boundary':t[2]=t[len(generated)%2]
   generated.append(dict(index=len(generated),state=state,**evaluate(t,v)))
  first=next((e for e in generated if e['failed']),None)
  final,trace=shrink(first['input'],v) if first else (None,[])
  enumeration=[dict(rank=rank(t),**evaluate(t,v)) for t in sorted(d,key=rank)]
  failures=[e for e in enumeration if e['failed']];minimum=failures[0]['input'] if failures else None
  out.update(status='MODEL_COMPLETE',generated=generated,draws=draws,first_failure_index=first['index'] if first else None,first_failure=first['input'] if first else None,shrink_trace=trace,final_counterexample=final,enumeration=enumeration,global_failures=len(failures),global_minimum=minimum,local_minimal=final is not None,local_equals_global=(final==minimum) if final is not None else None,generated_failures=sum(e['failed'] for e in generated),no_generated_failure_is_proof=False)
 out['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return out

if __name__=='__main__':
 import json
 print(json.dumps(run(dict(generator='boundary',seed=7,count=4,variant='M1')),ensure_ascii=False,indent=2))
