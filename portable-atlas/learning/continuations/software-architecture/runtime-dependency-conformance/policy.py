def judge(edges,trace):
 def find(event,module,function):return [t for t in trace if t['event']==event and t['calleeModule']==module and t['calleeFunction']==function]
 business=find('call','adapter','Adapter.add')
 businessEdges=[{'caller':t['callerModule']+'.'+t['callerFunction'],'callee':'adapter.Adapter.add','arguments':t['arguments']} for t in business]
 constructors=find('call','adapter','Adapter.__init__')
 dynamic=find('return','importlib','import_module')
 observations={'businessEdges':businessEdges,'constructors':[{'callerModule':t['callerModule'],'callerFunction':t['callerFunction'],'calleeModule':t['calleeModule'],'calleeFunction':t['calleeFunction']} for t in constructors],
 'dynamicSelections':[{'callerModule':t['callerModule'],'callerFunction':t['callerFunction'],'requested':t['requested'],'resolvedModule':t['resolvedModule']} for t in dynamic]}
 missing=[]
 for module,function in [('root','run'),('core','perform'),('adapter','Adapter.__init__'),('adapter','Adapter.add')]:
  if len(find('call',module,function))!=1 or len(find('return',module,function))!=1:missing.append(module+'.'+function+' call/return')
 for actor in [e['from'] for e in edges if e['to']=='importlib']:
  calls=[t for t in find('call','importlib','import_module') if t['callerModule']==actor and t.get('requested')=='adapter']
  returns=[t for t in dynamic if t['callerModule']==actor and t.get('requested')=='adapter' and t.get('resolvedModule')=='adapter']
  if len(calls)!=1 or len(returns)!=1:missing.append(actor+' dynamic adapter resolution')
 if missing:return {'verdict':'INDETERMINATE','reason':'required trace missing','missing':missing,'observations':observations}
 if any(t['callerModule']!='core' or t['callerFunction']!='perform' for t in business):
  return {'verdict':'INDETERMINATE','reason':'unrecognized business caller','missing':[],'observations':observations}
 actors=[t['callerModule'] for t in constructors]+[t['callerModule'] for t in dynamic]
 violation=any(actor=='core' for actor in actors)
 return {'verdict':'RESPONSIBILITY_VIOLATION' if violation else 'CONFORMING' if all(actor=='root' for actor in actors) else 'INDETERMINATE',
 'reason':'core selected or constructed concrete adapter' if violation else 'root selected/constructed; core called injected port' if all(actor=='root' for actor in actors) else 'unrecognized actor','missing':[],'observations':observations}
