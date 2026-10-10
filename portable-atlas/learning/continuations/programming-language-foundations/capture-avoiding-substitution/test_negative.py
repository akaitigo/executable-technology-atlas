"""Read-only altered raw rejection and exact finite AST validation boundaries."""
import copy,json
from pathlib import Path
from oracle import validate
from producer import validate_ast,Refused,run
ROOT=Path(__file__).resolve().parent
def checks():
 pointer=json.loads((ROOT/'evidence/current.json').read_text());raw=json.loads((ROOT/'evidence'/pointer['raw']).read_text());rejected=[]
 mutations=[('captured_result_as_safe',0,'value',3),('free_y_erased',0,'free',[]),('fresh_collision_v0',3,'ast',{'kind':'Lam','name':'v0','body':{'kind':'Add','left':{'kind':'Var','name':'y'},'right':{'kind':'Var','name':'v0'}}}),('same_binder_crossed',1,'ast',{'kind':'Lam','name':'x','body':{'kind':'Var','name':'y'}}),('naive_as_correct',0,'naive-value',10),('rename_crosses_inner_shadow',5,'value',13)]
 for name,ci,key,value in mutations:
  r=copy.deepcopy(raw)
  if key=='naive-value':r['cases'][ci]['naive']['value']=value
  else:r['cases'][ci]['safe'][key]=value
  try:validate(r)
  except AssertionError:rejected.append(name)
  else:raise AssertionError('accepted '+name)
 i=lambda n:dict(kind='Int',value=n);lam=lambda t:dict(kind='Lam',name='z',body=t);add=lambda a,b:dict(kind='Add',left=a,right=b)
 validate_ast(i(-1000));validate_ast(i(1000));depth=i(0)
 for _ in range(16):depth=lam(depth)
 validate_ast(depth)
 tree=i(0)
 for _ in range(5):tree=add(copy.deepcopy(tree),copy.deepcopy(tree))
 validate_ast(lam(tree)) # 63-node binary tree plus lambda = exactly 64
 refused=[]
 for name,t,reason in [('literal_1001',i(1001),'INT'),('negative_1001',i(-1001),'INT'),('boolean',i(True),'INT'),('depth_17',lam(depth),'AST_LIMIT'),('node_65',lam(lam(tree)),'AST_LIMIT'),('non_dict',[],'AST_TYPE'),('missing_body',{'kind':'Lam','name':'x'},'AST_FIELDS'),('bad_name',{'kind':'Var','name':'Bad'},'NAME')]:
  try:validate_ast(t)
  except Refused as e:assert str(e)==reason;refused.append(name)
  else:raise AssertionError('accepted '+name)
 assert run('unknown-case')['reason']=='UNKNOWN_CASE';assert run('capture','{bad')['status']=='INPUT_REFUSED' and run('capture','{bad')['reason']=='AST_JSON'
 return dict(oracle_mutants_rejected=rejected,exact_allowed_boundaries=['literal -1000/1000','depth16','node64'],input_boundaries_refused=refused,unknown_case_and_bad_json_refused=True)
if __name__=='__main__':print(json.dumps(checks()))
