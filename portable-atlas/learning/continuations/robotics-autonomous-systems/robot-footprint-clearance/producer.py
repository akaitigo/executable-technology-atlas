"""C-space inflation producer: two rectangle strips plus four circular caps."""
from fractions import Fraction as F
def inflate(rect,radius):
 x0,y0,x1,y1=map(F,rect);r=F(radius)
 return dict(strips=[[x0-r,y0,x1+r,y1],[x0,y0-r,x1,y1+r]],corners=[[x,y,r] for x in (x0,x1) for y in (y0,y1)])
def box_hit(route,box):
 p,q=[[F(v) for v in xy] for xy in route];lower=F(0);upper=F(1)
 for axis,(lo,hi) in enumerate(((box[0],box[2]),(box[1],box[3]))):
  delta=q[axis]-p[axis]
  if delta==0:
   if not lo<=p[axis]<=hi:return False
  else:
   a=(lo-p[axis])/delta;b=(hi-p[axis])/delta;lower=max(lower,min(a,b));upper=min(upper,max(a,b))
   if lower>upper:return False
 return True
def disk_hit(route,circle):
 p,q=[[F(v) for v in xy] for xy in route];cx,cy,r=circle;vx=q[0]-p[0];vy=q[1]-p[1];A=vx*vx+vy*vy;B=2*((p[0]-cx)*vx+(p[1]-cy)*vy);C=(p[0]-cx)**2+(p[1]-cy)**2-r*r
 t=max(F(0),min(F(1),-B/(2*A))) if A else F(0)
 return A*t*t+B*t+C<=0

def evaluate(scene,radius):
 details=[]
 for i,rect in enumerate(scene['obstacles']):
  region=inflate(rect,radius);strips=[box_hit(scene['route'],b) for b in region['strips']];caps=[disk_hit(scene['route'],c) for c in region['corners']]
  details.append(dict(obstacle=i,inflation={k:[[str(v) for v in item] for item in items] for k,items in region.items()},strip_hits=strips,corner_hits=caps,collision=any(strips+caps)))
 collision=any(d['collision'] for d in details)
 return dict(status='COLLISION' if collision else 'CLEAR',radius=radius,details=details,meaning='fixed mathematical route evaluation; no physical motion')

def sampled_bad(scene,radius,samples):
 results=[];p,q=[[F(v) for v in xy] for xy in scene['route']]
 for sample in samples:
  t=F(sample);point=[str(p[i]+t*(q[i]-p[i])) for i in (0,1)];s=dict(scene,route=[point,point]);r=evaluate(s,radius);results.append(dict(t=sample,point=point,status=r['status']))
 return dict(status='COLLISION' if any(r['status']=='COLLISION' for r in results) else 'CLEAR',samples=results,meaning='intentional bad: only discrete poses, no between-sample collision check')
