"""Authored finite block/let/use AST. No parser/source eval, JS TDZ or closures."""
class Reject(Exception):
    def __init__(self,details):self.details=details
def execute(ast,mode='strict'):
    bindings={};declarations={};resolution=[];evaluation=[];observations=[];scopes=[];seen=set();count=0
    def fail(phase,reason,node,**values):raise Reject(dict(phase=phase,reason=reason,node=node,**values))
    def schema(node,depth=0):
        nonlocal count
        count+=1
        if count>32 or depth>4 or not isinstance(node,dict):fail('input','AST_LIMIT_SCHEMA',None)
        kind=node.get('kind');required={'kind','id','body'} if kind=='block' else {'kind','id','name','value'} if kind=='let' else {'kind','id','name'} if kind=='use' else None
        if required is None or set(node)!=required or not isinstance(node.get('id'),str) or not node['id'] or node['id'] in seen:fail('input','AST_SCHEMA',node.get('id'))
        seen.add(node['id'])
        if kind=='block':
            if not isinstance(node['body'],list):fail('input','AST_SCHEMA',node['id'])
            names=[n.get('name') for n in node['body'] if isinstance(n,dict) and n.get('kind')=='let']
            if len(set(names))!=len(names):fail('input','DUPLICATE_NAME',node['id'])
            for child in node['body']:schema(child,depth+1)
        else:
            if not isinstance(node['name'],str) or not node['name'].isidentifier():fail('input','NAME_SCHEMA',node['id'])
            if kind=='let' and (type(node['value']) is not int or not 0<=node['value']<=100):fail('input','LITERAL_INT',node['id'])
    def declare(node,scope):
        scopes[-1][node['name']]=node['id'];declarations[node['id']]={'name':node['name'],'scope':scope,'value':node['value']};resolution.append({'event':'declare','node':node['id'],'name':node['name'],'scope':scope})
    def resolve(block):
        if mode!='flat' or not scopes:scopes.append({})
        resolution.append({'event':'enter_scope','scope':block['id']})
        if mode=='pre-register':
            for node in block['body']:
                if node['kind']=='let':declare(node,block['id'])
        try:
            for node in block['body']:
                if node['kind']=='block':resolve(node)
                elif node['kind']=='let':
                    if mode!='pre-register':declare(node,block['id'])
                else:
                    decl=next((scope[node['name']] for scope in reversed(scopes) if node['name'] in scope),None)
                    if decl is None:fail('resolution','UNDECLARED',node['id'],name=node['name'])
                    bindings[node['id']]=decl;resolution.append({'event':'bind','use':node['id'],'name':node['name'],'decl':decl})
        finally:
            resolution.append({'event':'leave_scope','scope':block['id']})
            if mode!='flat':scopes.pop()
    try:
        if mode not in ('strict','pre-register','flat') or ast.get('kind')!='block':fail('input','ROOT_MODE_SCHEMA',None)
        schema(ast);resolve(ast)
    except Reject as error:
        resolution.append({'event':'rejected',**error.details})
        return {'status':'RESOLUTION_REJECTED','bindings':bindings,'declarations':declarations,'values':[],'observations':[],'failure':error.details,'evaluation_started':False,'violation':mode!='strict','resolution_trace':resolution,'evaluation_trace':[]}
    initialized={}
    def evaluate(block):
        evaluation.append({'event':'enter_block','node':block['id']})
        try:
            for node in block['body']:
                if node['kind']=='block':evaluate(node)
                elif node['kind']=='let':
                    initialized[node['id']]=node['value'];evaluation.append({'event':'initialize','decl':node['id'],'value':node['value']})
                else:
                    decl=bindings[node['id']]
                    if decl not in initialized:fail('evaluation','UNINITIALIZED_DECL',node['id'],decl=decl)
                    value=initialized[decl];observations.append({'use':node['id'],'decl':decl,'value':value});evaluation.append({'event':'use','use':node['id'],'decl':decl,'value':value})
        finally:evaluation.append({'event':'leave_block','node':block['id']})
    failure=None
    try:evaluate(ast);status='COMPLETED' if mode=='strict' else 'BAD_COMPLETED'
    except Reject as error:failure=error.details;evaluation.append({'event':'rejected',**failure});status='BAD_EVALUATION_REJECTED' if mode!='strict' else 'EVALUATION_REJECTED'
    return {'status':status,'bindings':bindings,'declarations':declarations,'values':[o['value'] for o in observations],'observations':observations,'failure':failure,'evaluation_started':True,'violation':mode!='strict','resolution_trace':resolution,'evaluation_trace':evaluation}
