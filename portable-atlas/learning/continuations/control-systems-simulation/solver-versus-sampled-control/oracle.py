"""Independent high-precision closed form: no float recurrence/model import."""
from decimal import Decimal,localcontext
D=Decimal
def expected(h_text,model):
 with localcontext() as ctx:
  ctx.prec=80;h=D(h_text);N=int(D(8)/h);star=D(2)/3
  # Algebraically derived error multipliers, not the implementation step function.
  if model=='continuous-exact':a=(-3*h).exp()
  elif model=='forward-euler':a=1-3*h
  elif model=='backward-euler':a=1/(1+3*h)
  elif model=='sampled-hold-exact':a=3*(-h).exp()-2
  else:raise ValueError(model)
  ys=[star*(1-(a**n if n else D(1))) for n in range(N+1)]
  initial={'forward-euler':2*h,'backward-euler':2*h/(1+3*h),'sampled-hold-exact':2*(1-(-h).exp()),'continuous-exact':star*(1-(-3*h).exp())}[model]
  return dict(a=str(a),ys=[str(y) for y in ys],u_at_state=[str(2*(1-y)) for y in ys],initial_step=str(initial),continuous_T=str(star*(1-D(-24).exp())),sampled_boundary=str(D(3).ln()))
