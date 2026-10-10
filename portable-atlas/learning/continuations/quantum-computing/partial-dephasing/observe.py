"""Atlas: one bounded exact classical calculation; no quantum runtime or random shots."""
import copy,datetime,hashlib,json,os,platform,sys
from pathlib import Path
from model import validate,calculate,wrong_phase_flip,Refusal
ROOT=Path(__file__).resolve().parent
def main():
 x=json.loads((ROOT/'fixtures.json').read_text());r={'title':'Atlas partial-dephasing classical calculation','status':'preparing','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'priority_observed':os.getpriority(os.PRIO_PROCESS,0),'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'runtime':{'python':platform.python_version(),'system':platform.system(),'architecture':platform.machine(),'arithmetic':'stdlib Fraction complex pairs'},'cases':[],'wrong_phase_flip':[],'input_refusals':[],'shots':0,'quantum_hardware_used':False,'browser_executed':False}
 try:
  assert r['priority_observed']==10,'actual nice 10 required';states=validate(x)
  for name,rho in states.items():
   for p in x['p_values']:r['cases'].append(calculate(rho,name,p))
  for p in x['wrong_phase_flip_cases']:r['wrong_phase_flip'].append(wrong_phase_flip(states['plus'],p))
  edits=[('extra_key','input_keys',lambda z:z.update(extra=0)),('bool_schema','schema',lambda z:z.update(schema=True)),('basis_reversed','basis',lambda z:z.update(basis=['1','0'])),('p_is_phase_flip','channel_semantics',lambda z:z.update(p_semantics='phase_flip_probability')),('bool_p','rational_type',lambda z:z['p_values'].__setitem__(1,True)),('float_p','rational_type',lambda z:z['p_values'].__setitem__(1,.5)),('negative_p','p_range',lambda z:z['p_values'].__setitem__(1,'-1/2')),('p_over_one','p_range',lambda z:z['p_values'].__setitem__(1,'2')),('unsupported_p','p_not_fixed',lambda z:z['p_values'].__setitem__(1,'1/3')),('zero_denominator','rational_syntax',lambda z:z['p_values'].__setitem__(1,'1/0')),('matrix_shape','matrix_shape',lambda z:z['states'][0]['rho'].pop()),('complex_shape','complex_shape',lambda z:z['states'][0]['rho'][0][0].pop()),('not_hermitian','not_hermitian',lambda z:z['states'][0]['rho'][0][1].__setitem__(1,'1')),('wrong_trace','trace_not_one',lambda z:z['states'][0]['rho'][0][0].__setitem__(0,'1')),('negative_eigenvalue','not_positive_semidefinite',lambda z:[z['states'][0]['rho'][i][j].__setitem__(0,'1') for i,j in [(0,1),(1,0)]]),('unknown_state','state_id',lambda z:z['states'][0].__setitem__('id','other')),('shots_not_zero','shots',lambda z:z.update(shots=1))]
  for name,reason,edit in edits:
   y=copy.deepcopy(x);edit(y)
   try:validate(y)
   except Refusal as e:
    assert str(e)==reason,(name,str(e));r['input_refusals'].append({'case':name,'status':'expected_refusal','reason':reason})
   else:raise AssertionError('invalid input accepted: '+name)
  r['status']='observed'
 except Exception as e:r.update(status='execution_failed',error={'name':type(e).__name__,'message':str(e)})
 print(json.dumps(r,ensure_ascii=False,indent=2,allow_nan=False));return 0 if r['status']=='observed' else 1
if __name__=='__main__':sys.exit(main())
