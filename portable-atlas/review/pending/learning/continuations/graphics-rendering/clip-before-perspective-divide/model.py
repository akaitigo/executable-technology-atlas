"""正w / side・far内、近面z>=0だけのFraction CPUモデル。"""
import json,sys,re
from fractions import Fraction as F
class Refused(Exception):pass

def parse(inp):
 if type(inp)!=dict or set(inp)!={'vertices'}:raise Refused('SCHEMA')
 v=inp['vertices']
 if type(v)!=list or len(v)!=3 or any(type(p)!=list or len(p)!=4 for p in v):raise Refused('SCHEMA')
 out=[]
 for p in v:
  q=[]
  for s in p:
   if type(s)!=str or not re.fullmatch(r'-?\d{1,2}(?:/\d{1,2})?',s):raise Refused('COMPONENT')
   ns=s.split('/');n=int(ns[0]);d=int(ns[1]) if len(ns)>1 else 1
   if abs(n)>20 or not 1<=d<=10:raise Refused('COMPONENT')
   q.append(F(n,d))
  out.append(tuple(q))
 if any(p[3]<=0 for p in out):raise Refused('W_NOT_POSITIVE')
 if any(not(-p[3]<=p[0]<=p[3] and -p[3]<=p[1]<=p[3] and p[2]<=p[3]) for p in out):raise Refused('SIDE_OR_FAR')
 return out

def rotate(poly):
 out=[]
 for p in poly:
  if not out or p!=out[-1]:out.append(p)
 if len(out)>1 and out[0]==out[-1]:out.pop()
 if out:
  i=out.index(min(out));out=out[i:]+out[:i]
 return out

def encode(poly):return [[str(c) for c in p] for p in poly]
def signed(poly):
 s=F(0)
 for i in range(len(poly)):
  a,b=poly[i],poly[(i+1)%len(poly)];s+=a[0]*b[1]-b[0]*a[1]
 return s/2 if len(poly)>=3 else F(0)
def geometry(poly):
 poly=rotate(poly);ndc=[tuple(p[k]/p[3] for k in range(3)) for p in poly];area=signed(ndc);fan=[[0,i,i+1] for i in range(1,len(poly)-1)]
 return dict(polygon=encode(poly),ndc=encode(ndc),fan=fan,fan_signed_areas=[str(signed([ndc[k] for k in f])) for f in fan],signed_area=str(area),area=str(abs(area)),state='EMPTY' if len(poly)==0 else 'INSUFFICIENT' if len(poly)<3 else 'DEGENERATE' if area==0 else 'FILLED')
def produce(inp):
 vertices=parse(inp);near=[];intersections=[]
 # Sutherland–Hodgman: 前頂点から現在頂点へ逐次clip
 for i,cur in enumerate(vertices):
  j=(i-1)%3;prev=vertices[j];a=prev[2]>=0;b=cur[2]>=0
  if a!=b:
   t=prev[2]/(prev[2]-cur[2]);hit=tuple(prev[k]+t*(cur[k]-prev[k]) for k in range(4));near.append(hit)
   if prev[2]*cur[2]<0:intersections.append(dict(edge=[j,i],t=str(t),point=encode([hit])[0]))
  if b:near.append(cur)
 intersections.sort(key=lambda x:x['edge'][0]);inside=[p[2]>=0 for p in vertices]
 return dict(status='OBSERVED',input=inp,inside=inside,intersections=intersections,strategies={'near_clip':geometry(near),'no_clip':geometry(vertices),'drop_outside':geometry([p for p in vertices if p[2]>=0])})
if __name__=='__main__':
 try:
  inp=json.load(sys.stdin);parse(inp)
  if '--fail' in sys.argv:raise RuntimeError('injected')
  print(json.dumps(produce(inp)));sys.exit(0)
 except Refused as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e))));sys.exit(2)
 except (ValueError,TypeError,json.JSONDecodeError):print(json.dumps(dict(status='INPUT_REFUSED',reason='SCHEMA')));sys.exit(2)
 except RuntimeError:print(json.dumps(dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR')));sys.exit(3)
