# SPDX-License-Identifier: Apache-2.0
from fractions import Fraction as F
import math,struct,zlib
SIZE=16;BACKGROUND=[18,28,44]
def rational(x):
    if type(x) not in (int,float,str):raise ValueError('numeric rational required; bool rejected')
    if type(x) is float and not math.isfinite(x):raise ValueError('finite value required')
    try:return F(str(x))
    except (ValueError,ZeroDivisionError):raise ValueError('finite rational required')
def validate(f):
    if not isinstance(f,dict):raise ValueError('fixture object required')
    if len(f.get('screen',[]))!=3 or len(f.get('w',[]))!=3 or len(f.get('uv',[]))!=3:raise ValueError('three vertices required')
    if any(len(v)!=2 for v in f['screen']+f['uv']):raise ValueError('two components required')
    s=[[rational(x) for x in v] for v in f['screen']];w=[rational(x) for x in f['w']];uv=[[rational(x) for x in v] for v in f['uv']]
    if any(x<=0 for x in w):raise ValueError('positive w required')
    if any(x<0 or x>1 for v in uv for x in v):raise ValueError('UV in0..1 required')
    a,b,c=s
    area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    if not area:raise ValueError('degenerate screen triangle')
    return s,w,uv,area
def sample(f,point):
    s,w,uv,area=validate(f)
    if not isinstance(point,list) or len(point)!=2:raise ValueError('two-component point required')
    x,y=map(rational,point)
    if not 0<=x<=1 or not 0<=y<=1:raise ValueError('sample outside viewport0..1')
    a,b,c=s
    l=[((b[0]-x)*(c[1]-y)-(b[1]-y)*(c[0]-x))/area,((c[0]-x)*(a[1]-y)-(c[1]-y)*(a[0]-x))/area];l.append(1-sum(l))
    if min(l)<0:return dict(point=[str(x),str(y)],covered=False,screen_weights=[str(v) for v in l],naive=None,correct=None,normalized_weights=None,reciprocal_sum=None)
    reciprocal=[v/z for v,z in zip(l,w)];den=sum(reciprocal);correct_weights=[v/den for v in reciprocal]
    naive=[sum(l[i]*uv[i][j] for i in range(3)) for j in range(2)];correct=[sum(correct_weights[i]*uv[i][j] for i in range(3)) for j in range(2)]
    return dict(point=[str(x),str(y)],covered=True,screen_weights=[str(v) for v in l],reciprocal_weights=[str(v) for v in reciprocal],reciprocal_sum=str(den),normalized_weights=[str(v) for v in correct_weights],naive=[str(v) for v in naive],correct=[str(v) for v in correct])
def color(uv):
    if uv is None:return BACKGROUND[:]
    u,v=map(F,uv);return [(255*u+F(1,2)).numerator//(255*u+F(1,2)).denominator,(255*v+F(1,2)).numerator//(255*v+F(1,2)).denominator,220 if (int(u*8)+int(v*8))%2 else 40]
def render(f):
    rows=[];images={k:[] for k in ['naive','correct','difference']}
    for y in range(SIZE):
        for x in range(SIZE):
            r=sample(f,[str(F(2*x+1,2*SIZE)),str(F(2*y+1,2*SIZE))]);r.update(pixel=[x,y]);a=color(r['naive']);b=color(r['correct']);r['colors']=dict(naive=a,correct=b,difference=[abs(u-v) for u,v in zip(a,b)])
            for k in images:images[k].append(r['colors'][k])
            rows.append(r)
    return dict(id=f['id'],input=f,size=SIZE,samples=rows,images=images,anchor=sample(f,['1/4','1/4']))
def png(pixels):
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    scan=b''.join(b'\0'+bytes(sum(pixels[y*SIZE:(y+1)*SIZE],[])) for y in range(SIZE))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',SIZE,SIZE,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')
