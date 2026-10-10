import ast,json,pathlib,sys,importlib,hashlib
from policy import judge
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parent
ALLOWED=('root-static','root-dynamic','core-static','core-dynamic')
def execute(root):return root.run()
def run(request):
 if not isinstance(request,dict) or set(request)!=set(['fixture','profile']) or request['fixture'] not in ALLOWED or type(request['profile']) is not bool:
  return {'outcome':'REFUSED','reason':'request outside fixed fixture allowlist','output':None,'edges':None,'trace':None,'judgment':None},2
 directory=R/'fixtures'/request['fixture'];edges=[];hashes={}
 for module in ['root','core','adapter']:
  path=directory/(module+'.py');text=path.read_text();hashes[module+'.py']=hashlib.sha256(path.read_bytes()).hexdigest()
  for node in ast.walk(ast.parse(text)):
   if isinstance(node,ast.Import):
    edges.extend({'from':module,'to':n.name,'syntax':'Import','line':node.lineno} for n in node.names)
   elif isinstance(node,ast.ImportFrom):
    edges.append({'from':module,'to':node.module,'syntax':'ImportFrom','line':node.lineno})
 trace=[]
 def function(frame):
  name=frame.f_code.co_name
  return 'Adapter.'+name if frame.f_globals.get('__name__')=='adapter' and name in ('__init__','add') else name
 def profile(frame,event,arg):
  if event not in ('call','return'):return
  module=frame.f_globals.get('__name__');fn=function(frame);caller=frame.f_back
  if caller is None:return
  selected=module in ('root','core','adapter') and fn in ('run','perform','Adapter.__init__','Adapter.add')
  dynamic=module=='importlib' and fn=='import_module' and caller.f_globals.get('__name__') in ('root','core')
  if not selected and not dynamic:return
  item={'event':event,'callerModule':caller.f_globals.get('__name__'),'callerFunction':function(caller),'calleeModule':module,'calleeFunction':fn}
  if event=='return':item['returnValue']=arg if isinstance(arg,(int,str,bool)) or arg is None else None
  if dynamic:
   name=frame.f_locals.get('name')
   if name!='adapter':raise RuntimeError('dynamic module outside fixed allowlist')
   item['requested']=name
   if event=='return':item['resolvedModule']=getattr(arg,'__name__',None)
  elif event=='call' and fn=='Adapter.add':item['arguments']=[frame.f_locals['x'],frame.f_locals['y']]
  trace.append(item)
 sys.path.insert(0,str(directory))
 for name in ['root','core','adapter']:sys.modules.pop(name,None)
 try:
  if request['profile']:sys.setprofile(profile)
  root=importlib.import_module('root');output=execute(root)
 finally:sys.setprofile(None)
 return {'outcome':'OBSERVED','reason':None,'output':output,'edges':edges,'trace':trace,'fixtureSourceHashes':hashes,'judgment':judge(edges,trace)},0
if __name__=='__main__':
 try:request=json.load(sys.stdin)
 except json.JSONDecodeError as e:
  print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 try:out,code=run(request)
 except Exception as e:
  print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(4)
 print(json.dumps(out));sys.exit(code)
