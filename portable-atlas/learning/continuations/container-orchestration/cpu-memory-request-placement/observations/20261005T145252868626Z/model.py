import sys,json,copy
N={'nodeA':{'cpu':4,'memory':4},'nodeB':{'cpu':4,'memory':2}}
def reject():return {'observed':False,'reason':'invalid bounded placement request','trace':[],'placements':None,'remaining':None,'summary':None},2
def run(x):
 if not isinstance(x,dict) or set(x)!={'algorithm','nodes','pods','overhead'} or x['algorithm'] not in ('first-fit','ignore-memory') or x['nodes']!=N:return reject()
 if not isinstance(x['nodes'],dict) or any(type(v) is not int for n in x['nodes'].values() for v in n.values()):return reject()
 oh=x['overhead'];pods=x['pods']
 if not isinstance(oh,dict) or set(oh)!={'cpu','memory'} or any(type(v) is not int or not 0<=v<=4 for v in oh.values()):return reject()
 if not isinstance(pods,list) or not 1<=len(pods)<=3:return reject()
 seen=set()
 for p in pods:
  if not isinstance(p,dict) or set(p)!={'id','cpu','memory'} or not isinstance(p['id'],str) or p['id'] not in ('p1','p2','p3') or p['id'] in seen or any(type(p[k]) is not int or not 1<=p[k]<=4 for k in ('cpu','memory')):return reject()
  seen.add(p['id'])
 remaining=copy.deepcopy(N);trace=[];placements=[]
 for p in pods:
  before=copy.deepcopy(remaining);demand={k:p[k]+oh[k] for k in ('cpu','memory')};candidates=[];node=None
  for n in ('nodeA','nodeB'):
   free=remaining[n];cp=free['cpu']>=demand['cpu'];mp=free['memory']>=demand['memory'];accept=cp and (mp or x['algorithm']=='ignore-memory');candidates.append({'node':n,'remaining':copy.deepcopy(free),'cpuFits':cp,'memoryFits':mp,'acceptedByAlgorithm':accept})
   if accept:
    node=n
    for k in ('cpu','memory'):remaining[n][k]-=demand[k]
    break
  placements.append({'pod':p['id'],'node':node});trace.append({'pod':p['id'],'demand':demand,'beforeRemaining':before,'candidates':candidates,'placement':node,'afterRemaining':copy.deepcopy(remaining)})
 bound=sum(p['node'] is not None for p in placements)
 return {'observed':True,'reason':None,'trace':trace,'placements':placements,'remaining':remaining,'summary':{'bound':bound,'pending':len(pods)-bound,'outcome':'PENDING' if bound<len(pods) else 'BOUND'}},0
if __name__=='__main__':
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 try:o,code=run(x)
 except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(4)
 print(json.dumps(o));sys.exit(code)
