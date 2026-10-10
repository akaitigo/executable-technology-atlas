import json,sys,copy
class Refusal(Exception):pass
def model(x):
 stores={'A':{'revision':0,'value':'v0','available':True},'B':{'revision':0,'value':'v0','available':True}}
 queue=[];partition=False;router='A';trace=[];reads=[];acks=[]
 def refuse(reason):raise Refusal(reason)
 try:
  if not isinstance(x,dict) or set(x)!=set(['steps']) or not isinstance(x['steps'],list) or not 1<=len(x['steps'])<=20:refuse('invalid steps')
  for step,s in enumerate(x['steps']):
   if not isinstance(s,dict) or 'op' not in s:refuse('invalid step')
   op=s['op'];ack=None;reading=None;status=op
   if op=='write':
    if set(s)!=set(['op','value']) or not isinstance(s['value'],str) or not 1<=len(s['value'])<=32:refuse('invalid value')
    if not stores['A']['available']:refuse('unavailable:A')
    stores['A']['revision']+=1;stores['A']['value']=s['value']
    queue.append({'revision':stores['A']['revision'],'value':s['value']})
    ack={'store':'A','revision':stores['A']['revision'],'value':s['value'],'scope':'local model ack; no B/durability guarantee'};acks.append(ack);status='ack-a'
   elif op=='route':
    if set(s)!=set(['op','target']) or s['target'] not in ('A','B'):refuse('invalid target')
    router=s['target']
   elif op=='partition':
    if set(s)!=set(['op','enabled']) or type(s['enabled']) is not bool:refuse('invalid partition')
    partition=s['enabled']
   elif op=='availability':
    if set(s)!=set(['op','target','available']) or s['target'] not in ('A','B') or type(s['available']) is not bool:refuse('invalid availability')
    stores[s['target']]['available']=s['available']
   elif op=='deliver':
    if set(s)!=set(['op']):refuse('invalid delivery')
    if partition:status='delivery-blocked'
    elif not stores['B']['available']:status='delivery-blocked-unavailable'
    elif not queue:status='delivery-empty'
    else:
     message=queue.pop(0)
     if message['revision']!=stores['B']['revision']+1:refuse('delivery gap')
     stores['B'].update(message);status='delivered'
   elif op=='read':
    if set(s)!=set(['op']):refuse('invalid read')
    if not stores[router]['available']:refuse('unavailable:'+router)
    reading={'step':step,'store':router,'available':True,'revision':stores[router]['revision'],'value':stores[router]['value'],'requiredRevision':stores['A']['revision'],'fresh':stores[router]['revision']==stores['A']['revision']}
    reads.append(reading)
   else:refuse('unknown operation')
   trace.append({'step':step,'operation':copy.deepcopy(s),'status':status,'stores':copy.deepcopy(stores),'deliveryQueue':copy.deepcopy(queue),'partition':partition,'router':router,'ack':ack,'read':reading})
  return {'accepted':True,'reason':None,'trace':trace,'reads':reads,'acks':acks,'answer':reads[-1] if reads else None}
 except Refusal as e:
  return {'accepted':False,'reason':str(e),'failedStep':len(trace),'trace':trace,'reads':reads,'acks':acks,'answer':None}
if __name__=='__main__':
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:
  print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 out=model(x);print(json.dumps(out,ensure_ascii=False));sys.exit(0 if out['accepted'] else 2)
