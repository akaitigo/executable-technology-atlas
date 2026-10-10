"""Finite named capture-avoiding substitution and a deliberate naive alternative."""
import json,re,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
class Refused(Exception):pass
def require(ok,reason):
 if not ok:raise Refused(reason)
def name(n):return isinstance(n,str) and re.fullmatch(r'[a-z][a-z0-9_]{0,15}',n) is not None
def integer(n):return type(n) is int and -1000<=n<=1000
def validate_ast(t):
 count=0
 def visit(n,depth):
  nonlocal count
  count+=1;require(count<=64 and depth<=16,'AST_LIMIT');require(isinstance(n,dict),'AST_TYPE');k=n.get('kind');require(k in ['Int','Var','Lam','App','Add'],'AST_KIND')
  fields={'Int':{'kind','value'},'Var':{'kind','name'},'Lam':{'kind','name','body'},'App':{'kind','fn','arg'},'Add':{'kind','left','right'}}
  require(set(n)==fields[k],'AST_FIELDS')
  if k=='Int':require(integer(n['value']),'INT')
  elif k=='Var':require(name(n['name']),'NAME')
  elif k=='Lam':require(name(n['name']),'NAME');visit(n['body'],depth+1)
  else:
   for field in (['fn','arg'] if k=='App' else ['left','right']):visit(n[field],depth+1)
 visit(t,0)
def free(t):
 k=t['kind']
 if k=='Int':return set()
 if k=='Var':return {t['name']}
 if k=='Lam':return free(t['body'])-{t['name']}
 return free(t['fn'])|free(t['arg']) if k=='App' else free(t['left'])|free(t['right'])
def names(t):
 k=t['kind']
 if k=='Int':return set()
 if k=='Var':return {t['name']}
 if k=='Lam':return {t['name']}|names(t['body'])
 return names(t['fn'])|names(t['arg']) if k=='App' else names(t['left'])|names(t['right'])
def rename_bound(t,old,new):
 k=t['kind']
 if k=='Var':return dict(kind='Var',name=new if t['name']==old else t['name'])
 if k=='Int':return copy.deepcopy(t)
 if k=='Lam':return copy.deepcopy(t) if t['name']==old else dict(kind='Lam',name=t['name'],body=rename_bound(t['body'],old,new))
 fields=['fn','arg'] if k=='App' else ['left','right'];return dict(kind=k,**{field:rename_bound(t[field],old,new) for field in fields})
def substitute(t,target,replacement,safe):
 used=names(t)|names(replacement)|{target};events=[]
 def walk(n):
  k=n['kind']
  if k=='Var':
   if n['name']==target:events.append(dict(action='replace',name=target));return copy.deepcopy(replacement)
   return copy.deepcopy(n)
  if k=='Int':return copy.deepcopy(n)
  if k=='Lam':
   binder=n['name'];body=n['body']
   if binder==target:events.append(dict(action='stop-binder',name=binder));return copy.deepcopy(n)
   if target not in free(body):events.append(dict(action='target-absent',name=binder));return copy.deepcopy(n)
   if safe and binder in free(replacement):
    i=0
    while 'v'+str(i) in used:i+=1
    fresh='v'+str(i);used.add(fresh);events.append(dict(action='alpha-rename',old=binder,fresh=fresh));body=rename_bound(body,binder,fresh);binder=fresh
   return dict(kind='Lam',name=binder,body=walk(body))
  fields=['fn','arg'] if k=='App' else ['left','right'];return dict(kind=k,**{field:walk(n[field]) for field in fields})
 return walk(t),events
def evaluate(t,environment,arguments):
 fuel=400
 def ev(n,env):
  nonlocal fuel
  fuel-=1
  if fuel<0:raise RuntimeError('evaluation-budget')
  k=n['kind']
  if k=='Int':return n['value']
  if k=='Var':
   if n['name'] not in env:raise RuntimeError('unbound-name:'+n['name'])
   return env[n['name']]
  if k=='Lam':return dict(parameter=n['name'],body=n['body'],environment=env.copy())
  if k=='App':return apply(ev(n['fn'],env),ev(n['arg'],env))
  a,b=ev(n['left'],env),ev(n['right'],env)
  if type(a) is not int or type(b) is not int:raise RuntimeError('addition-type')
  return a+b
 def apply(fn,arg):
  if not isinstance(fn,dict):raise RuntimeError('not-callable')
  e=fn['environment'].copy();e[fn['parameter']]=arg;return ev(fn['body'],e)
 value=ev(t,environment)
 for arg in arguments:value=apply(value,arg)
 if type(value) is not int:raise RuntimeError('non-integer-result')
 return value
def run(case_id,term_json=None):
 cases={c['id']:c for c in FIXTURE['cases']};out=dict(case=case_id,status='',reason='',input=None,safe=None,naive=None)
 try:
  require(case_id in cases,'UNKNOWN_CASE');c=copy.deepcopy(cases[case_id])
  if term_json:
   try:c['term']=json.loads(term_json)
   except (ValueError,TypeError):raise Refused('AST_JSON')
  out['input']=c;validate_ast(c['term']);validate_ast(c['replacement']);require(name(c['target']),'NAME');require(isinstance(c['environment'],dict) and all(name(k) and integer(v) for k,v in c['environment'].items()),'ENVIRONMENT');require(isinstance(c['arguments'],list) and 1<=len(c['arguments'])<=3 and all(integer(v) for v in c['arguments']),'ARGUMENTS')
  if c['variant']=='execution-failure':raise RuntimeError('injected substitution failure')
  branches={}
  for mode in ['safe','naive']:
   ast,events=substitute(c['term'],c['target'],c['replacement'],mode=='safe');branches[mode]=dict(ast=ast,free=sorted(free(ast)),value=evaluate(ast,c['environment'],c['arguments']),events=events)
  out.update(status='NORMAL',term_free=sorted(free(c['term'])),replacement_free=sorted(free(c['replacement'])),**branches)
 except Refused as e:out.update(status='INPUT_REFUSED',reason=str(e))
 except Exception as e:out.update(status='EXECUTION_FAILURE',reason=str(e))
 return out
