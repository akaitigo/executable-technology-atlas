"""Atlas: finite exact classical calculation of partial dephasing, without shots."""
from fractions import Fraction as F
from math import isqrt
import re

class Refusal(ValueError):pass
Z0=(F(0),F(0))
def c(real=0,imag=0):return (F(real),F(imag))
def plus(a,b):return (a[0]+b[0],a[1]+b[1])
def times(a,b):return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def conjugate(a):return (a[0],-a[1])
def zero():return [[Z0,Z0],[Z0,Z0]]
def add(a,b):return [[plus(a[i][j],b[i][j]) for j in range(2)] for i in range(2)]
def scale(a,w):return [[times(c(w),a[i][j]) for j in range(2)] for i in range(2)]
def product(a,b):return [[plus(times(a[i][0],b[0][j]),times(a[i][1],b[1][j])) for j in range(2)] for i in range(2)]
def adjoint(a):return [[conjugate(a[j][i]) for j in range(2)] for i in range(2)]
def trace(a):return plus(a[0][0],a[1][1])
def determinant(a):return plus(times(a[0][0],a[1][1]),times(c(-1),times(a[0][1],a[1][0])))
def pack(a):return [[[str(v[0]),str(v[1])] for v in row] for row in a]
def rational(s):
 if type(s) is not str:raise Refusal('rational_type')
 if len(s)>32 or not re.fullmatch(r'-?\d+(?:/\d+)?',s):raise Refusal('rational_syntax')
 try:v=F(s)
 except (ValueError,ZeroDivisionError):raise Refusal('rational_syntax')
 if abs(v.numerator)>10000 or v.denominator>10000:raise Refusal('rational_bound')
 return v
def parse_matrix(raw):
 if type(raw) is not list or len(raw)!=2 or any(type(row) is not list or len(row)!=2 for row in raw):raise Refusal('matrix_shape')
 if any(type(v) is not list or len(v)!=2 for row in raw for v in row):raise Refusal('complex_shape')
 a=[[(rational(v[0]),rational(v[1])) for v in row] for row in raw]
 if a!=adjoint(a):raise Refusal('not_hermitian')
 if trace(a)!=c(1):raise Refusal('trace_not_one')
 det=determinant(a)
 if a[0][0][0]<0 or a[1][1][0]<0 or det[1]!=0 or det[0]<0:raise Refusal('not_positive_semidefinite')
 return a
def parameter(p):
 v=rational(p)
 if not 0<=v<=1:raise Refusal('p_range')
 if p not in ['0','1/2','1']:raise Refusal('p_not_fixed')
 return v
def fixed_states():return {'plus':[[c('1/2'),c('1/2')],[c('1/2'),c('1/2')]],'phase-i':[[c('1/2'),c(0,'-1/2')],[c(0,'1/2'),c('1/2')]],'zero':[[c(1),c()],[c(),c()]]}
def validate(x):
 if type(x) is not dict or set(x)!={'schema','basis','channel','p_semantics','p_values','states','wrong_phase_flip_cases','shots'}:raise Refusal('input_keys')
 if type(x['schema']) is not int or x['schema']!=1:raise Refusal('schema')
 if x['basis']!=['0','1']:raise Refusal('basis')
 if x['channel']!='E_p=(1-p)*rho+p*diag(rho)' or x['p_semantics']!='mixture_weight_of_complete_Z_dephasing':raise Refusal('channel_semantics')
 if type(x['p_values']) is not list:raise Refusal('p_values')
 for p in x['p_values']:parameter(p)
 if x['p_values']!=['0','1/2','1']:raise Refusal('p_sequence')
 if type(x['shots']) is not int or x['shots']!=0:raise Refusal('shots')
 if x['wrong_phase_flip_cases']!=['1/2','1']:raise Refusal('comparison_parameters')
 if type(x['states']) is not list or len(x['states'])!=3:raise Refusal('state_count')
 expected=fixed_states();out={}
 for state,name in zip(x['states'],expected):
  if type(state) is not dict or set(state)!={'id','rho'}:raise Refusal('state_keys')
  if state['id']!=name:raise Refusal('state_id')
  a=parse_matrix(state['rho'])
  if a!=expected[name]:raise Refusal('state_not_fixed')
  out[name]=a
 return out
def exact_sqrt(v):
 n,d=isqrt(v.numerator),isqrt(v.denominator)
 if n*n!=v.numerator or d*d!=v.denominator:raise Refusal('nonrational_sqrt_outside_fixed_scope')
 return F(n,d)
def metrics(a):
 herm=a==adjoint(a);t=trace(a);det=determinant(a);positive=herm and a[0][0][0]>=0 and a[1][1][0]>=0 and det[1]==0 and det[0]>=0
 assert herm and positive and t==c(1)
 magnitude=exact_sqrt(sum(v*v for v in a[0][1]));gap=exact_sqrt((a[0][0][0]-a[1][1][0])**2+4*magnitude*magnitude)
 return {'trace':str(t[0]),'hermitian':herm,'positive_semidefinite':positive,'determinant':str(det[0]),'eigenvalues':[str((t[0]-gap)/2),str((t[0]+gap)/2)],'coherence_z':str(magnitude),'rho01':[str(v) for v in a[0][1]],'purity':str(trace(product(a,a))[0]),'probabilities_z':[str(a[i][i][0]) for i in range(2)]}
R=[[c(1),c(1)],[c(1),c(-1)]]
def hadamard(a):return scale(product(product(R,a),R),F(1,2))
def stage(a):return {'density':pack(a),**metrics(a)}
def calculate(rho,name,p_text):
 p=parameter(p_text);diagonal=[[rho[0][0],c()],[c(),rho[1][1]]];direct=add(scale(rho,1-p),scale(diagonal,p));branches=[];combined=zero();combined_h=zero()
 for label,weight,unscaled in [('unchanged',1-p,rho),('Z-result-0',p*rho[0][0][0],product(product([[c(1),c()],[c(),c()]],rho),[[c(1),c()],[c(),c()]])),('Z-result-1',p*rho[1][1][0],product(product([[c(),c()],[c(),c(1)]],rho),[[c(),c()],[c(),c(1)]]))]:
  conditional=scale(unscaled,1/trace(unscaled)[0]) if weight else None
  contribution=scale(conditional,weight) if weight else zero();after_h=hadamard(conditional) if weight else None;contribution_h=scale(after_h,weight) if weight else zero()
  branches.append({'branch':label,'weight':str(weight),'reachable':bool(weight),'conditional':pack(conditional) if conditional is not None else None,'after_h_conditional':pack(after_h) if after_h is not None else None,'contribution':pack(contribution),'after_h_contribution':pack(contribution_h),'observed_measurement_record':False})
  combined=add(combined,contribution);combined_h=add(combined_h,contribution_h)
 transformed=hadamard(direct);assert combined==direct and combined_h==transformed
 return {'case_id':name+'@'+p_text,'state_id':name,'p':p_text,'equivalent_phase_flip_q':str(p/2),'before':stage(rho),'after_e':stage(direct),'after_h':stage(transformed),'branches':branches,'branch_sum':pack(combined),'branch_sum_after_h':pack(combined_h),'branch_weights_sum':str(sum(F(b['weight']) for b in branches)),'paths_equal':True,'shots':0,'quantum_hardware_used':False}
def wrong_phase_flip(rho,p_text):
 q=parameter(p_text);z=[[c(1),c()],[c(),c(-1)]];a=add(scale(rho,1-q),scale(product(product(z,rho),z),q));correct=calculate(rho,'plus',p_text)
 return {'p_mistaken_as_q':p_text,'meaning':'phase_flip_probability; not intended E_p','after_e':stage(a),'after_h':stage(hadamard(a)),'matches_intended':pack(a)==correct['after_e']['density'],'hardware_failure':False}
