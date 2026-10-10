"""Independent pairwise spread / integer cross-multiplied inequality oracle."""
import copy,json,math,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run,snapshot
HAND=json.loads((ROOT/'hand-oracle.json').read_text())
def expected(a):
 n=len(a);total=sum(a);pair=sum((v-w)**2 for i,v in enumerate(a) for w in a[i+1:]);return F(total,n),F(pair,n*(n-1)),F(pair,n)
def outside(v,a):
 n=len(a);total=sum(a);pair=sum((v-w)**2 for i,v in enumerate(a) for w in a[i+1:]);return (n*v-total)**2*(n-1)>9*pair*n
def metrics(m,a):
 mean,s2,sse=expected(a);assert m['N']==len(a) and F(m['mean'])==mean and F(m['s2'])==s2 and F(m['SSE'])==sse and F(m['radius_squared'])==9*s2
 for n,sign in [('LCL_approx',-1),('UCL_approx',1)]:assert abs(m[n]-(float(mean)+sign*3*math.sqrt(float(s2))))<1e-9
def inspect(r,x):
 assert r['status']=='calculated';s=r['summary'];assert s['input']==x and s['baseline_frozen_before_monitoring'] and s['sigma_known'] is False;metrics(s['frozen'],x['baseline']);assert F(s['frozen']['s2'])>0 and len(s['steps'])==len(x['monitoring'])
 fixed=[];masked=[];spec=[]
 for i,step in enumerate(s['steps']):
  v=x['monitoring'][i];a=x['baseline']+x['monitoring'][:i+1];metrics(step['buggy'],a);f=outside(v,x['baseline']);b=outside(v,a);p=not x['specification'][0]<=v<=x['specification'][1]
  assert step['index']==i+1 and step['value']==v and step['fixed_outside']==f and step['buggy_outside']==b and step['spec_outside']==p and step['current_point_in_buggy_estimation']
  assert F(step['fixed_distance_squared'])==(F(v)-expected(x['baseline'])[0])**2 and F(step['buggy_distance_squared'])==(F(v)-expected(a)[0])**2
  if f:fixed.append(i+1)
  if f and not b:masked.append(i+1)
  if p:spec.append(i+1)
 assert s['fixed_flags']==fixed and s['masked_flags']==masked and s['spec_flags']==spec and s['category']==('masked' if masked else 'alert' if fixed else 'spec-only' if spec else 'quiet')
 assert s['units']=={'response_mean_limits':'arb','s2_squared_distance':'arb^2'} and s['rule']=='distance_squared > 9*s2; equality inside'
 ctx=r['context'];assert ctx['synthetic'] and not any(v for k,v in ctx.items() if isinstance(v,bool) and k!='synthetic')
def handcheck(r,name):
 h=HAND['cases'][name];s=r['summary'];assert s['category']==h['category'] and [p['fixed_outside'] for p in s['steps']]==h['fixed'] and [p['buggy_outside'] for p in s['steps']]==h['buggy'] and [p['spec_outside'] for p in s['steps']]==h['spec']
 for key in ['mean','SSE','s2','radius_squared']:assert s['frozen'][key]==HAND[key]
 if 'first_bug_mean' in h:assert s['steps'][0]['buggy']['mean']==h['first_bug_mean'] and s['steps'][0]['buggy']['s2']==h['first_bug_s2']
def main():
 before=snapshot();rows=json.loads((ROOT/'expected-table.json').read_text())['rows'];valid=[]
 for row in rows:
  p=run(row['input_json']);r=p['result'];assert p['stderr']==''
  if row['expected']['status']=='calculated':assert p['exit']==0;inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case']);valid.append(r)
  else:assert p['exit']==2 and r=={'status':'input_refusal','code':row['expected']['code'],'summary':None}
 rejected=[]
 for name in ['refit-as-fixed','population-denominator','boundary-outside','spec-as-control','shock-unmasked','current-point-excluded','sigma-known','false-alarm-claim','cause-identified','inside-proves-control','units-unsquared','run-rule-claimed']:
  r=copy.deepcopy(valid[1] if name=='boundary-outside' else valid[2] if name=='spec-as-control' else valid[0]);s=r['summary']
  if name=='refit-as-fixed':s['frozen']=copy.deepcopy(s['steps'][0]['buggy'])
  elif name=='population-denominator':s['frozen']['s2']='36/5'
  elif name=='boundary-outside':s['steps'][0]['fixed_outside']=True
  elif name=='spec-as-control':s['steps'][0]['fixed_outside']=True
  elif name=='shock-unmasked':s['steps'][0]['buggy_outside']=True
  elif name=='current-point-excluded':s['steps'][0]['current_point_in_buggy_estimation']=False
  elif name=='sigma-known':s['sigma_known']=True
  elif name=='false-alarm-claim':r['context']['false_alarm_probability_verified']=True
  elif name=='cause-identified':r['context']['cause_identified']=True
  elif name=='inside-proves-control':r['context']['all_inside_proves_control']=True
  elif name=='units-unsquared':s['units']['s2_squared_distance']='arb'
  else:r['context']['run_rules_implemented']=True
  try:inspect(r,s['input'])
  except (AssertionError,ValueError,TypeError,KeyError):rejected.append(name)
  else:raise AssertionError('surviving mutant '+name)
 if (ROOT/'observation-data.js').exists():
  raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.CONTROL_OBSERVATION=').strip().removesuffix(';'));assert raw==json.loads((ROOT/'observations'/raw['run_id']/'raw.json').read_text()) and raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES}
  for row in raw['rows']:
   r=row['run']['result'];assert json.loads(row['run']['stdout'])==r
   if r['status']=='calculated':inspect(r,json.loads(row['input_json']));handcheck(r,row['expected']['hand_case'])
   else:assert r['code']==row['expected']['code'] and row['run']['exit']==2
 assert before==snapshot();print(json.dumps({'hand_cases':5,'refused':7,'mutants_rejected':rejected,'oracle':'pairwise and cross-multiplied integer inequality','unit_sha_mtime_unchanged':True}));return 0
if __name__=='__main__':sys.exit(main())
