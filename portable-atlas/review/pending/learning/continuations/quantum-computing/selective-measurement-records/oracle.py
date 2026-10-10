"""独立2×2閉式と係数和。producerの行列helperをimportしない。"""
import json,sys
from fractions import Fraction as F
Z=(F(0),F(0))
def parse(m):return [[tuple(F(x) for x in z) for z in row] for row in m]
def enc(m):return [[[str(c) for c in z] for z in row] for row in m]
def diagonal(a,b):return [[(a,F(0)),Z],[Z,(b,F(0))]]
def h_closed(m):
 a,b,c,d=m[0][0],m[0][1],m[1][0],m[1][1]
 return [[tuple((a[k]+b[k]+c[k]+d[k])/2 for k in range(2)),tuple((a[k]-b[k]+c[k]-d[k])/2 for k in range(2))],[tuple((a[k]+b[k]-c[k]-d[k])/2 for k in range(2)),tuple((a[k]-b[k]-c[k]+d[k])/2 for k in range(2))]]
def info(m):
 t=m[0][0][0]+m[1][1][0];det=m[0][0][0]*m[1][1][0]-sum(x*x for x in m[0][1]);return dict(density=enc(m),trace=str(t),z_probabilities=[str(m[0][0][0]),str(m[1][1][0])],determinant=str(det),normalized=t==1)
def expected(inp):
 rho=parse(inp['rho']);p=[rho[0][0][0],rho[1][1][0]];branches=[]
 for k in range(2):
  sigma=diagonal(p[k] if k==0 else F(0),p[k] if k==1 else F(0));conditional=diagonal(F(1-k),F(k)) if p[k]>0 else None
  hm=[[(F(1,2),F(0)),(F(1 if k==0 else -1,2),F(0))],[(F(1 if k==0 else -1,2),F(0)),(F(1,2),F(0))]] if conditional else None
  branches.append(dict(outcome=k,sigma=info(sigma),p=str(p[k]),status='REACHABLE' if p[k]>0 else 'UNREACHABLE',conditional=info(conditional) if conditional else None,after_h=info(hm) if hm else None))
 weighted=diagonal(p[0],p[1]);direct=diagonal(rho[0][0][0],rho[1][1][0]);hm=h_closed(weighted)
 # 各H後branchの係数和はdiag=Σpk/2、off=(p0−p1)/2。
 mh=[[(sum(p)/2,F(0)),((p[0]-p[1])/2,F(0))],[((p[0]-p[1])/2,F(0)),(sum(p)/2,F(0))]]
 discard=dict(weighted=info(weighted),direct=info(direct),h_of_weighted=info(hm),h_of_direct=info(h_closed(direct)),weighted_after_h=info(mh),full_equal_before=True,full_equal_after=True)
 omit=diagonal(p[0]**2,p[1]**2);count=sum(x>0 for x in p);w=[F(1,count) if x>0 else F(0) for x in p];equal=diagonal(*w)
 faults=dict(omit_normalization=dict(density=info(omit),after_h=info(h_closed(omit)),branch_traces=[str(x) for x in p],full_equal=omit==weighted),equal_weights=dict(weights=[str(x) for x in w],density=info(equal),after_h=info(h_closed(equal)),full_equal=equal==weighted,h_probabilities_equal=True),zero_division=dict(status='EXECUTION_FAILED' if 0 in p else 'NO_FAILURE_IN_THIS_CASE',reason='ZERO_PROBABILITY_DIVISION' if 0 in p else None,conditionals=None if 0 in p else [b['conditional']['density'] for b in branches]))
 record=inp['record']
 if record=='discard':selection=dict(kind='discard',outcome=None,p=None,status='ENSEMBLE',state=discard['weighted'],after_h=discard['h_of_weighted'])
 else:
  b=branches[record];selection=dict(kind='conditional',outcome=record,p=b['p'],status=b['status'],state=b['conditional'],after_h=b['after_h'])
 return dict(status='OBSERVED',input=inp,input_state=info(rho),branches=branches,discard=discard,faults=faults,selection=selection)
def check(out,inp,literal=None):
 if literal and literal.get('failure'):assert out==dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR');return
 assert out==expected(inp),'independent density paths differ'
 assert sum(F(b['p']) for b in out['branches'])==1
 for b in out['branches']:
  assert F(b['sigma']['trace'])==F(b['p'])
  if F(b['p'])==0:assert b['conditional'] is None and b['after_h'] is None and b['status']=='UNREACHABLE'
  else:assert b['conditional']['trace']=='1' and b['after_h']['trace']=='1'
 if literal:
  assert [b['p'] for b in out['branches']]==literal['p'];assert out['discard']['h_of_weighted']['density'][0][1]==literal['h01'];assert out['faults']['omit_normalization']['density']['trace']==literal['omit_trace'];assert out['faults']['equal_weights']['full_equal']==literal['equal_full'];assert out['selection']['status']==literal['selection']
if __name__=='__main__':
 try:
  x=json.load(sys.stdin);check(x['result'],x['input']);print(json.dumps(dict(status='AUDIT_PASSED')))
 except Exception as e:print(json.dumps(dict(status='AUDIT_FAILED',reason=str(e))));sys.exit(1)
