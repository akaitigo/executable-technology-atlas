"""Read-only independent raw/computed corruption rejection and subset boundaries."""
import copy,json
from pathlib import Path
from oracle import validate
from checker import verify_qa
from producer import run,FIXTURE
ROOT=Path(__file__).resolve().parent
def checks():
 p=json.loads((ROOT/'evidence/current.json').read_text());raw=json.loads((ROOT/'evidence'/p['raw']).read_text());qa=json.loads((ROOT/'evidence/iab-qa-case-results.json').read_text());rejected=[]
 for name,ci,kind in [('wrong_terminal',0,'terminal'),('changed_blue_not_propagated',1,'value'),('broken_css_reference',0,'css'),('cycle_as_normal',6,'status')]:
  r=copy.deepcopy(raw)
  if kind=='terminal':r['cases'][ci]['resolved']['semantic.action']['terminal']='primitive.green'
  if kind=='value':r['cases'][ci]['resolved']['semantic.focus']['value']['components']=[0,0,1]
  if kind=='css':r['cases'][ci]['css']=r['cases'][ci]['css'].replace('--semantic-action','--wrong-action')
  if kind=='status':r['cases'][ci]['status']='NORMAL'
  try:validate(r)
  except AssertionError:rejected.append(name)
  else:raise AssertionError('accepted '+name)
 for name,case,wrong in [('browser_model_substituted','primitive-red','rgb(0, 0, 255)'),('fault_hidden_by_expected_blue','unresolved-css','rgb(0, 0, 255)')]:
  q=copy.deepcopy(qa);q['cases'][case]['computed']['a']=wrong;q['cases'][case]['ui_computed']=json.dumps(q['cases'][case]['computed'])
  try:verify_qa(raw,q)
  except AssertionError:rejected.append(name)
  else:raise AssertionError('accepted '+name)
 q=copy.deepcopy(qa);q['cases']['alias-green']['answer']='blue変更はA/B/focusへ連動'
 try:verify_qa(raw,q)
 except AssertionError:rejected.append('alias_green_false_blue_answer')
 else:raise AssertionError('accepted false blue answer')
 q=copy.deepcopy(qa);q['prediction_controls']['CSS値の予想']['after']['answer_open']=True
 try:verify_qa(raw,q)
 except AssertionError:rejected.append('prediction_keeps_old_details_open')
 else:raise AssertionError('accepted stale details')
 base=FIXTURE['cases'][0]['tokens'];probes=[]
 for name,field,value,reason in [('component_none','components',['none',0,1],'COMPONENTS'),('component_nan','components',[float('nan'),0,1],'COMPONENTS'),('component_length','components',[0,1],'COMPONENTS'),('alpha_bool','alpha',True,'ALPHA_SUBSET'),('hex_not_supported','hex','#0000ff','COLOR_FIELDS')]:
  doc=copy.deepcopy(base);doc['primitive']['blue']['$value'][field]=value;r=run('blue',json.dumps(doc));assert r['status']=='INPUT_REFUSED' and r['reason']==reason and r['css'] is None, name;probes.append(name)
 assert run('unknown-case')['reason']=='UNKNOWN_CASE';assert run('blue','{bad')['reason']=='TOKEN_JSON'
 return dict(mutants_rejected=rejected,subset_boundary_probes=probes,unknown_case_and_bad_json_refused=True)
if __name__=='__main__':print(json.dumps(checks()))
