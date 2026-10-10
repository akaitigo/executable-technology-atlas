import datetime,json,math,re,sys
from fractions import Fraction as F
sys.dont_write_bytecode=True
class Refusal(Exception):pass
def reject(code):raise Refusal(code)
def pairs(items):
 d={}
 for k,v in items:
  if k in d:reject('json_syntax')
  d[k]=v
 return d
def parse(text):
 try:x=json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:reject('json_syntax'))
 except (ValueError,TypeError):reject('json_syntax')
 if not isinstance(x,dict) or set(x)!=set(['unit','baseline','monitoring','specification']):reject('shape')
 if x['unit']!='arb':reject('unit')
 for name,lo,hi in [('baseline',4,12),('monitoring',1,8)]:
  a=x[name]
  if not isinstance(a,list) or not lo<=len(a)<=hi:reject(name+'-count')
  if any(type(v) is not int or not -50<=v<=50 for v in a):reject('values')
 a=x['specification']
 if not isinstance(a,list) or len(a)!=2 or any(type(v) is not int or not -50<=v<=50 for v in a) or a[0]>=a[1]:reject('specification')
 return x
def estimate(values):
 n=len(values);mean=sum(map(F,values))/n;sse=sum((F(v)-mean)**2 for v in values);s2=sse/(n-1);rad=3*math.sqrt(float(s2))
 return {'N':n,'mean':str(mean),'SSE':str(sse),'s2':str(s2),'radius_squared':str(9*s2),'LCL_approx':float(mean)-rad,'UCL_approx':float(mean)+rad}
def signal(v,m):return (F(v)-F(m['mean']))**2>F(m['radius_squared'])
def compute(x):
 frozen=estimate(x['baseline'])
 if F(frozen['s2'])==0:reject('zero-variation')
 history=x['baseline'].copy();steps=[]
 for i,v in enumerate(x['monitoring']):
  history.append(v);bug=estimate(history);fixed=signal(v,frozen);fault=signal(v,bug);spec=v<x['specification'][0] or v>x['specification'][1]
  steps.append({'index':i+1,'value':v,'fixed_outside':fixed,'buggy_outside':fault,'spec_outside':spec,'fixed_distance_squared':str((F(v)-F(frozen['mean']))**2),'buggy_distance_squared':str((F(v)-F(bug['mean']))**2),'buggy':bug,'current_point_in_buggy_estimation':True})
 masked=[s['index'] for s in steps if s['fixed_outside'] and not s['buggy_outside']];flags=[s['index'] for s in steps if s['fixed_outside']];spec=[s['index'] for s in steps if s['spec_outside']]
 category='masked' if masked else 'alert' if flags else 'spec-only' if spec else 'quiet'
 return {'input':x,'category':category,'frozen':frozen,'steps':steps,'fixed_flags':flags,'masked_flags':masked,'spec_flags':spec,'baseline_frozen_before_monitoring':True,'rule':'distance_squared > 9*s2; equality inside','estimator':'mean and sample s2 (N-1), uncorrected s plug-in','sigma_known':False,'specification_source':'separately declared synthetic product bounds','units':{'response_mean_limits':'arb','s2_squared_distance':'arb^2'}}
def main():
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 try:
  x=parse(sys.stdin.read());s=compute(x);r={'status':'calculated','summary':s,'context':{'synthetic':True,'baseline_statistical_control_established':False,'population_sigma_known':False,'normality_verified':False,'false_alarm_probability_verified':False,'ARL_verified':False,'cause_identified':False,'all_inside_proves_control':False,'I_MR_implemented':False,'c4_correction_implemented':False,'run_rules_implemented':False,'physical_process_measured':False,'phase_I':'finite baseline estimation only; not stable-process qualification','phase_II':'frozen baseline point comparison only'},'started_utc':start,'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};code=0
 except Refusal as e:r={'status':'input_refusal','code':str(e),'summary':None};code=2
 except Exception as e:r={'status':'execution_error','error_class':type(e).__name__,'summary':None};code=3
 print(json.dumps(r,ensure_ascii=False));return code
if __name__=='__main__':sys.exit(main())
