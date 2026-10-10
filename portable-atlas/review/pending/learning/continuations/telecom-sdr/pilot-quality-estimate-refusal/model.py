"""合成I/Q receiver。正解payload bitsを受け取らない。"""
import json,sys,re
from fractions import Fraction as F
class Refused(Exception):pass

def scalar(s):
 if type(s)!=str or not re.fullmatch(r'-?\d{1,3}(?:/\d{1,4})?',s):raise Refused('COMPONENT')
 parts=s.split('/');n=int(parts[0]);d=int(parts[1]) if len(parts)>1 else 1
 if abs(n)>100 or not 1<=d<=1000:raise Refused('COMPONENT')
 return F(n,d)
def parse(inp):
 if type(inp)!=dict or set(inp)!={'known_pilot','pilot_rx','payload_rx','min_gain_sq','max_residual'}:raise Refused('SCHEMA')
 arrays=[]
 for name in ['known_pilot','pilot_rx','payload_rx']:
  v=inp[name]
  if type(v)!=list or len(v)!=4 or any(type(p)!=list or len(p)!=2 for p in v):raise Refused('SCHEMA')
  a=[tuple(scalar(c) for c in p) for p in v]
  if any(abs(c)>4 for p in a for c in p):raise Refused('COORDINATE_RANGE')
  arrays.append(a)
 minimum=scalar(inp['min_gain_sq']);maximum=scalar(inp['max_residual'])
 if not 0<=minimum<=4 or not 0<=maximum<=4:raise Refused('THRESHOLD_RANGE')
 return arrays+[minimum,maximum]
def mul(a,b):return (a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def conj(a):return (a[0],-a[1])
def energy(a):return a[0]*a[0]+a[1]*a[1]
def enc(a):return [str(c) for c in a]
def receive(inp):
 p,r,x,minimum,maximum=parse(inp);terms=[mul(conj(a),b) for a,b in zip(p,r)];ek=sum(energy(a) for a in p);er=sum(energy(a) for a in r);num=(sum(a[0] for a in terms),sum(a[1] for a in terms));h=(num[0]/ek,num[1]/ek) if ek else None;h2=energy(h) if h else None;rows=[];sse=F(0) if h else None
 for i,(known,rx) in enumerate(zip(p,r)):
  fit=mul(h,known) if h else None;res=(rx[0]-fit[0],rx[1]-fit[1]) if fit else None;e=energy(res) if res else None
  if e is not None:sse+=e
  rows.append(dict(index=i,known=enc(known),rx=enc(rx),correlation=enc(terms[i]),known_energy=str(energy(known)),rx_energy=str(energy(rx)),fit=enc(fit) if fit else None,residual=enc(res) if res else None,residual_energy=str(e) if e is not None else None))
 nr=sse/er if er and sse is not None else None;mp=h2>=minimum if h2 is not None else None;rp=nr<=maximum if nr is not None else None
 hard=['NO_PILOT_ENERGY'] if not ek else ['ZERO_GAIN'] if not h2 else [];policies={}
 for name in ['gated','naive']:
  reasons=hard[:] if hard else []
  if not reasons and name=='gated':
   if not mp:reasons.append('LOW_MAGNITUDE')
   if not rp:reasons.append('HIGH_RESIDUAL')
  factor=None;corrected=None;decisions=None
  if not reasons:
   factor=(h[0]/h2,-h[1]/h2);corrected=[mul(z,factor) for z in x];decisions=[1 if z[0]<0 else 0 for z in corrected]
  policies[name]=dict(status='REFUSED' if reasons else 'ACCEPTED',reasons=reasons,factor=enc(factor) if factor else None,corrected=[enc(z) for z in corrected] if corrected is not None else None,decisions=decisions,demodulated=not bool(reasons))
 return dict(status='OBSERVED',input=inp,stats=dict(known_energy=str(ek),rx_energy=str(er),numerator=enc(num),h=enc(h) if h else None,h2=str(h2) if h2 is not None else None,sse=str(sse) if sse is not None else None,normalized_residual=str(nr) if nr is not None else None),rows=rows,gates=dict(min_gain_sq=inp['min_gain_sq'],max_residual=inp['max_residual'],magnitude_pass=mp,residual_pass=rp),policies=policies)
if __name__=='__main__':
 try:
  inp=json.load(sys.stdin);parse(inp)
  if '--fail' in sys.argv:raise RuntimeError('injected')
  print(json.dumps(receive(inp)));sys.exit(0)
 except Refused as e:print(json.dumps(dict(status='INPUT_REFUSED',reason=str(e))));sys.exit(2)
 except (ValueError,TypeError):print(json.dumps(dict(status='INPUT_REFUSED',reason='SCHEMA')));sys.exit(2)
 except RuntimeError:print(json.dumps(dict(status='EXECUTION_FAILED',reason='INJECTED_RUNTIME_ERROR')));sys.exit(3)
