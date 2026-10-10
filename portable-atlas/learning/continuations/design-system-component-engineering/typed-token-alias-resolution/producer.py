"""Fixed typed alias DFS followed by color-only CSS translation."""
import copy,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
IDS=['primitive.blue','primitive.green','semantic.action','semantic.focus','semantic.positive']
class Refused(Exception):pass
def require(ok,reason):
 if not ok:raise Refused(reason)
def number(x):return type(x) in [int,float] and math.isfinite(x)
def flatten(doc):
 require(isinstance(doc,dict) and set(doc)=={'primitive','semantic'},'GROUP_SET');require(all(isinstance(doc[g],dict) for g in doc),'GROUP_TYPE');flat={g+'.'+n:t for g,group in doc.items() for n,t in group.items()};require(set(flat)==set(IDS),'TOKEN_SET')
 for t in flat.values():
  require(isinstance(t,dict) and set(t)=={'$type','$value'},'TOKEN_FIELDS');require(t['$type'] in ['color','number'],'TYPE_SUBSET');v=t['$value']
  if isinstance(v,str):require(re.fullmatch(r'\{[a-z]+\.[a-z]+\}',v) is not None,'ALIAS_SYNTAX');continue
  if t['$type']=='number':require(number(v),'NUMBER_VALUE');continue
  require(isinstance(v,dict) and {'colorSpace','components'}<=set(v) and set(v)<={'colorSpace','components','alpha'},'COLOR_FIELDS');require(v['colorSpace']=='srgb','COLOR_SPACE_SUBSET');channels=v['components'];require(isinstance(channels,list) and len(channels)==3 and all(number(x) and 0<=x<=1 for x in channels),'COMPONENTS');alpha=v.get('alpha',1);require(number(alpha) and alpha==1,'ALPHA_SUBSET')
 return flat
def resolve(flat,trace):
 cache={};visiting=[]
 def one(path):
  require(path in flat,'MISSING_REFERENCE');require(path not in visiting,'CYCLE')
  if path in cache:return cache[path]
  visiting.append(path);t=flat[path];v=t['$value']
  if isinstance(v,str):
   target=v[1:-1];trace.append(dict(action='reference',token=path,target=target));require(target in flat,'MISSING_REFERENCE');require(flat[target]['$type']==t['$type'],'TYPE_MISMATCH');result=copy.deepcopy(one(target))
  else:
   value=copy.deepcopy(v)
   if t['$type']=='color':value['alpha']=value.get('alpha',1)
   result=dict(terminal=path,type=t['$type'],value=value)
  visiting.pop();cache[path]=result;trace.append(dict(action='resolved',token=path,terminal=result['terminal']));return result
 result={path:one(path) for path in IDS};require(all(t['type']=='color' for t in result.values()),'CSS_TYPE_SUBSET');return result
def emit(flat,resolved,fault):
 properties={}
 for path in IDS:
  value=resolved[path]['value'];channels=[math.floor(x*255+0.5) for x in value['components']];css='rgb('+str(channels[0])+' '+str(channels[1])+' '+str(channels[2])+')'
  if fault and isinstance(flat[path]['$value'],str):css='var(--unresolved-'+flat[path]['$value'][1:-1].replace('.','-')+')'
  properties[path.replace('.','-')]=css
 return '#token-scope {\n'+''.join('  --'+key+': '+value+';\n' for key,value in properties.items())+'}\n'
def run(case_id,tokens_json=None):
 cases={c['id']:c for c in FIXTURE['cases']};out=dict(case=case_id,status='',reason='',input=None,css=None,resolved=None,trace=[])
 try:
  require(case_id in cases,'UNKNOWN_CASE');c=copy.deepcopy(cases[case_id])
  if tokens_json:
   try:c['tokens']=json.loads(tokens_json)
   except (TypeError,ValueError):raise Refused('TOKEN_JSON')
  out['input']=c;flat=flatten(c['tokens'])
  if c['variant']=='execution-failure':raise RuntimeError('injected token translation failure')
  values=resolve(flat,out['trace']);css=emit(flat,values,c['variant']=='unresolved-css');out.update(status='FAULT_UNRESOLVED_CSS' if c['variant']=='unresolved-css' else 'NORMAL',resolved=values,css=css)
 except Refused as e:out.update(status='INPUT_REFUSED',reason=str(e))
 except Exception as e:out.update(status='EXECUTION_FAILURE',reason=str(e))
 return out
