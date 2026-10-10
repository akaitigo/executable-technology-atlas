"""独立候補集合・辺parameter順の半平面oracle。producerをimportしない。"""
import json,sys
from fractions import Fraction as Q

def canonical(points):
 out=[]
 for p in points:
  if not out or p!=out[-1]:out.append(p)
 if len(out)>1 and out[-1]==out[0]:out.pop()
 if out:
  k=min(range(len(out)),key=lambda i:out[i]);out=out[k:]+out[:k]
 return out

def encode(points):return [[str(x) for x in p] for p in points]
def area(points):
 if len(points)<3:return Q(0)
 return sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))/2

def geometry(poly):
 p=canonical(poly);ndc=[tuple(a/b[3] for a in b[:3]) for b in p];signed=area(ndc)
 fans=[[0,i,i+1] for i in range(1,len(p)-1)];fa=[area([ndc[i] for i in t]) for t in fans]
 return dict(polygon=encode(p),ndc=encode(ndc),fan=fans,fan_signed_areas=[str(x) for x in fa],signed_area=str(signed),area=str(abs(signed)),state='EMPTY' if not p else 'INSUFFICIENT' if len(p)<3 else 'DEGENERATE' if signed==0 else 'FILLED')

def expected(inp):
 v=[tuple(Q(s) for s in p) for p in inp['vertices']];mask=[p[2]>=0 for p in v];candidates=[];cross=[]
 # 候補集合を入力巡回parameterで並べる。逐次出力clipではない。
 for i,p in enumerate(v):
  if mask[i]:candidates.append((Q(i),p))
  q=v[(i+1)%3]
  if p[2]*q[2]<0:
   t=abs(p[2])/(abs(p[2])+abs(q[2]));hit=tuple((1-t)*p[k]+t*q[k] for k in range(4));candidates.append((i+t,hit));cross.append(dict(edge=[i,(i+1)%3],t=str(t),point=encode([hit])[0]))
 near=[p for _,p in sorted(candidates,key=lambda x:x[0])]
 return dict(status='OBSERVED',input=inp,inside=mask,intersections=cross,strategies={'near_clip':geometry(near),'no_clip':geometry(v),'drop_outside':geometry([p for i,p in enumerate(v) if mask[i]])})

def check(out,inp,literal=None):
 if literal and 'refused' in literal:
  assert out==dict(status='INPUT_REFUSED',reason=literal['refused']);return
 if literal and literal.get('failure'):
  assert out==dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR');return
 assert out==expected(inp),'independent polygon oracle differs'
 for k,s in out['strategies'].items():
  assert sum(Q(x) for x in s['fan_signed_areas'])==Q(s['signed_area'])
 if literal:
  assert [out['strategies'][k]['area'] for k in ['near_clip','no_clip','drop_outside']]==literal['areas'],'hand area'
  if 'mask' in literal:assert out['inside']==literal['mask']
  if 'near_polygon' in literal:assert out['strategies']['near_clip']['polygon']==literal['near_polygon'],'hand intersections/order'
  if 'fan_areas' in literal:assert out['strategies']['near_clip']['fan_signed_areas']==literal['fan_areas']
if __name__=='__main__':
 try:
  x=json.load(sys.stdin);check(x['result'],x['input']);print(json.dumps(dict(status='AUDIT_PASSED')))
 except Exception as e:print(json.dumps(dict(status='AUDIT_FAILED',reason=str(e))));sys.exit(1)
