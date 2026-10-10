"""Original-obstacle separation oracle. No inflation or producer imports."""
from fractions import Fraction as Q
def gap(a,b,c,d):return max(Q(0),c-b,a-d)
def distance_squared(route,rect):
 p,q=[[Q(v) for v in xy] for xy in route]
 if p[0]!=q[0] and p[1]!=q[1]:raise ValueError('axis-aligned fixed fixture only')
 x0,y0,x1,y1=map(Q,rect);dx=gap(min(p[0],q[0]),max(p[0],q[0]),x0,x1);dy=gap(min(p[1],q[1]),max(p[1],q[1]),y0,y1)
 return dx*dx+dy*dy

def expected(scene,radius):
 r=Q(radius);distances=[distance_squared(scene['route'],rect) for rect in scene['obstacles']];d2=min(distances)
 return dict(status='COLLISION' if d2<=r*r else 'CLEAR',distance_squared=str(d2),radius_squared=str(r*r),relation='contact' if d2==r*r else 'overlap' if d2<r*r else 'positive clearance',obstacle_distance_squared=[str(d) for d in distances])
