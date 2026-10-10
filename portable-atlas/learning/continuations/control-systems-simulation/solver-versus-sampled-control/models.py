"""Float recurrence paths; no oracle imports. Mathematical models, not hardware."""
import math
MODELS=('continuous-exact','forward-euler','backward-euler','sampled-hold-exact')
def simulate(h_text,model):
 h=float(h_text);N=round(8/h);assert model in MODELS and abs(N*h-8)<1e-12
 a={'continuous-exact':math.exp(-3*h),'forward-euler':1-3*h,'backward-euler':1/(1+3*h),'sampled-hold-exact':3*math.exp(-h)-2}[model]
 y=0.;points=[];intervals=[];curve=[]
 for n in range(N+1):
  t=n*h;u=2*(1-y);points.append(dict(n=n,t=t,y=y,u_at_state=u));curve.append(dict(t=t,y=y))
  if n==N:break
  if model=='continuous-exact':
   yn=2/3*(-math.expm1(-3*(n+1)*h));used=None;meaning='continuous feedback varies within interval'
  elif model=='forward-euler':yn=y+h*(-y+u);used=u;meaning='explicit numerical slope at old state; not held plant exact'
  elif model=='backward-euler':yn=(y+2*h)/(1+3*h);used=2*(1-yn);meaning='implicit numerical slope at new state; not held controller'
  else:yn=math.exp(-h)*y+(-math.expm1(-h))*u;used=u;meaning='sampled control held constant on [t0,t1)'
  mid=None
  for fraction in (.25,.5,.75):
   s=fraction*h
   if model=='continuous-exact':v=2/3*(-math.expm1(-3*(t+s)))
   elif model=='sampled-hold-exact':v=math.exp(-s)*y+(-math.expm1(-s))*u
   else:continue
   curve.append(dict(t=t+s,y=v))
   if fraction==.5:mid=v
  intervals.append(dict(n=n,t0=t,t1=(n+1)*h,u_used=used,u_semantics=meaning,y_next=yn,y_mid=mid));y=yn
 return dict(model=model,h=h,N=N,T=8,a=a,behavior='stable' if abs(a)<1 else 'boundary' if abs(a)==1 else 'unstable',points=points,intervals=intervals,curve=curve,final_y=y,continuous_reference=2/3*(-math.expm1(-24)),difference_kind='controller model difference' if model=='sampled-hold-exact' else 'continuous closed-loop numerical difference',signed_difference=y-2/3*(-math.expm1(-24)))
