import json,sys,copy

def run(x):
 def refuse(reason):return {'observed':False,'reason':reason,'summary':None,'trace':[]},2
 if type(x)!=dict or set(x)!={'policy','completion','order','generation','oldPayload','newPayload'} or x['policy'] not in ('guarded','cancel-release-fault'):return refuse('schema/policy; native API not supported')
 if x['completion'] not in ('success','aborted'):return refuse('completion success/aborted only')
 if type(x['generation'])!=int or not 1<=x['generation']<=9:return refuse('generation integer1..9; bool forbidden')
 if type(x['order'])!=list or len(x['order'])!=4 or x['order'][0]!='submit' or any(type(v)!=str for v in x['order']) or sorted(x['order'])!=['cancel','complete','reuse','submit']:return refuse('submit first then one cancel/reuse/complete each')
 for k in ['oldPayload','newPayload']:
  if type(x[k])!=str or not 1<=len(x[k])<=40 or not all(32<=ord(c)<=126 for c in x[k]):return refuse('payload printable ASCII1..40')
 b={'generation':x['generation'],'owner':None,'status':None,'payload':'empty'};op={'submittedGeneration':None,'pending':False,'cancelRequested':False,'status':None};interference=False;allowed=None;trace=[]
 for action in x['order']:
  if action=='submit':b['owner']='A';op['submittedGeneration']=b['generation'];op['pending']=True;result='SUBMITTED'
  elif action=='cancel':
   if op['pending']:
    op['cancelRequested']=True;result='REQUESTED'
    if x['policy']=='cancel-release-fault':b['owner']=None
   else:result='NOT_PENDING'
  elif action=='reuse':
   allowed=b['owner'] is None
   if allowed:b.update(generation=b['generation']+1,owner='application',status=None,payload=x['newPayload']);result='REUSE_ALLOWED'
   else:result='REUSE_REJECTED'
  else:
   interference=b['generation']!=op['submittedGeneration'];op.update(pending=False,status=x['completion']);b.update(owner=None,status=x['completion']);
   if x['completion']=='success':b['payload']=x['oldPayload']
   result='COMPLETED_'+x['completion'].upper()
  state={'buffer':dict(b),'operationA':dict(op),'interference':interference,'reuseAllowed':allowed};trace.append({'action':action,'result':result,'state':copy.deepcopy(state)})
 return {'observed':True,'reason':None,'trace':trace,'summary':state},0
if __name__=='__main__':
 if sys.argv[1:]:sys.exit(2)
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 o,code=run(x);print(json.dumps(o));sys.exit(code)
