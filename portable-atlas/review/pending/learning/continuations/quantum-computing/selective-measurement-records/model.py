"""1qubit Z selective measurement、exact complex-pair density。PRNGなし。"""
import json,sys,re
from fractions import Fraction as F
class Refused(Exception):pass
Z=(F(0),F(0));ONE=(F(1),F(0))
def scalar(s):
 if type(s)!=str or not re.fullmatch(r'-?\d{1,3}(?:/\d{1,4})?',s):raise Refused('COMPONENT')
 v=s.split('/');n=int(v[0]);d=int(v[1]) if len(v)>1 else 1
 if abs(n)>100 or not 1<=d<=1000:raise Refused('COMPONENT')
 return F(n,d)
def parse(inp):
 if type(inp)!=dict or set(inp)!={'rho','record'}:raise Refused('SCHEMA')
 r=inp['record']
 if not ((type(r)==int and r in [0,1]) or (type(r)==str and r=='discard')):raise Refused('RECORD')
 m=inp['rho']
 if type(m)!=list or len(m)!=2 or any(type(row)!=list or len(row)!=2 or any(type(z)!=list or len(z)!=2 for z in row) for row in m):raise Refused('SCHEMA')
 a=[[tuple(scalar(c) for c in z) for z in row] for row in m];x,y,b=a[0][0],a[1][1],a[0][1]
 if x[1]!=0 or y[1]!=0 or a[1][0]!=(b[0],-b[1]) or x[0]+y[0]!=1 or min(x[0],y[0])<0 or x[0]*y[0]<b[0]**2+b[1]**2:raise Refused('DENSITY')
 return a
def add(a,b):return (a[0]+b[0],a[1]+b[1])
def mul(a,b):return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def scale(m,x):return [[(z[0]*x,z[1]*x) for z in row] for row in m]
def product(a,b):
 return [[add(mul(a[i][0],b[0][j]),mul(a[i][1],b[1][j])) for j in range(2)] for i in range(2)]
def sum_matrices(ms):
 out=[[Z,Z],[Z,Z]]
 for m in ms:out=[[add(out[i][j],m[i][j]) for j in range(2)] for i in range(2)]
 return out
def enc(m):return [[[str(c) for c in z] for z in row] for row in m]
def info(m):
 trace=m[0][0][0]+m[1][1][0];det=m[0][0][0]*m[1][1][0]-m[0][1][0]**2-m[0][1][1]**2
 return dict(density=enc(m),trace=str(trace),z_probabilities=[str(m[0][0][0]),str(m[1][1][0])],determinant=str(det),normalized=trace==1)
R=[[ONE,ONE],[ONE,(-F(1),F(0))]]
def h(m):return scale(product(product(R,m),R),F(1,2))
def produce(inp):
 rho=parse(inp);ps=[[[ONE,Z],[Z,Z]],[[Z,Z],[Z,ONE]]];sigmas=[];probs=[];states=[];hs=[];branches=[]
 for k,p in enumerate(ps):
  sigma=product(product(p,rho),p);prob=sigma[0][0][0]+sigma[1][1][0];conditional=scale(sigma,1/prob) if prob>0 else None;after=h(conditional) if conditional is not None else None
  sigmas.append(sigma);probs.append(prob);states.append(conditional);hs.append(after);branches.append(dict(outcome=k,sigma=info(sigma),p=str(prob),status='REACHABLE' if prob>0 else 'UNREACHABLE',conditional=info(conditional) if conditional is not None else None,after_h=info(after) if after is not None else None))
 weighted=sum_matrices([scale(states[k],probs[k]) for k in range(2) if probs[k]>0]);direct=[[rho[0][0],Z],[Z,rho[1][1]]];wh=h(weighted);dh=h(direct);hw=sum_matrices([scale(hs[k],probs[k]) for k in range(2) if probs[k]>0])
 discard=dict(weighted=info(weighted),direct=info(direct),h_of_weighted=info(wh),h_of_direct=info(dh),weighted_after_h=info(hw),full_equal_before=weighted==direct,full_equal_after=wh==dh==hw)
 omit=sum_matrices([scale(sigmas[k],probs[k]) for k in range(2)]);n=sum(p>0 for p in probs);weights=[F(1,n) if p>0 else F(0) for p in probs];equal=sum_matrices([scale(states[k],weights[k]) for k in range(2) if probs[k]>0]);eh=h(equal)
 # 意図的な別fault。正常経路はpk0を割らない。
 try:
  unsafe=[enc(scale(s,F(1)/p)) for s,p in zip(sigmas,probs)];zero=dict(status='NO_FAILURE_IN_THIS_CASE',reason=None,conditionals=unsafe)
 except ZeroDivisionError:zero=dict(status='EXECUTION_FAILED',reason='ZERO_PROBABILITY_DIVISION',conditionals=None)
 faults=dict(omit_normalization=dict(density=info(omit),after_h=info(h(omit)),branch_traces=[str(p) for p in probs],full_equal=omit==weighted),equal_weights=dict(weights=[str(w) for w in weights],density=info(equal),after_h=info(eh),full_equal=equal==weighted,h_probabilities_equal=info(eh)['z_probabilities']==info(wh)['z_probabilities']),zero_division=zero)
 r=inp['record']
 if r=='discard':selection=dict(kind='discard',outcome=None,p=None,status='ENSEMBLE',state=discard['weighted'],after_h=discard['h_of_weighted'])
 else:
  b=branches[r];selection=dict(kind='conditional',outcome=r,p=b['p'],status=b['status'],state=b['conditional'],after_h=b['after_h'])
 return dict(status='OBSERVED',input=inp,input_state=info(rho),branches=branches,discard=discard,faults=faults,selection=selection)
if __name__=='__main__':
 try:
  inp=json.load(sys.stdin);parse(inp)
  if '--fail' in sys.argv:raise RuntimeError('injected')
  print(json.dumps(produce(inp)));sys.exit(0)
 except Refused as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e))));sys.exit(2)
 except (ValueError,TypeError):print(json.dumps(dict(status='INPUT_REFUSED',reason='SCHEMA')));sys.exit(2)
 except RuntimeError:print(json.dumps(dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR')));sys.exit(3)
