# SPDX-License-Identifier: Apache-2.0
# Independent Decimal recurrence; no imports of controller/model/metrics.
from decimal import Decimal,localcontext
D=Decimal
def expected(c):
 with localcontext() as context:
  context.prec=70;h=D(str(c['h']));a=(-h).exp();y=D(0);z=D(0);rows=[]
  for i in range(int(D(8)/h)):
   t=i*h;reference=D(4) if t<D(4) else D('.5');e=reference-y;q=e+D(c['ki'])*z
   u=q if c['mode']=='free' else (D(1) if q>D(1) else (D(-1) if q<D(-1) else q))
   if c['mode']=='conditional':blocked=(q>=D(1) and e>D(0)) or (q<=D(-1) and e<D(0))
   else:blocked=False
   yn=a*y+(1-a)*u;zn=z+(D(0) if blocked else h*e)
   rows.append(dict(step=i,t=t,r=reference,y=y,z=z,e=e,u_requested=q,u_actual=u,clipped=u!=q,integral_stopped=blocked,y_next=yn,z_next=zn));y,z=yn,zn
  rows.append(dict(step=len(rows),t=D(8),r=D('.5'),y=y,z=z,e=D('.5')-y,u_requested=None,u_actual=None,clipped=None,integral_stopped=None,y_next=None,z_next=None))
  post=[x for x in rows if x['t']>=D(4)];outside=[i for i,x in enumerate(post) if abs(x['y']-D('.5'))>D('.05')]
  first=next((x['t'] for i,x in enumerate(post) if i not in outside),None)
  candidate=(max(outside)+1) if outside else 0
  settled=post[candidate]['t'] if candidate<len(post) and D(8)-post[candidate]['t']>=D(1) else None
  reexit=[post[i]['t'] for i in outside if i>0 and i-1 not in outside]
  metrics=dict(first_entry_time=first,settled_time=settled,settling_status='SETTLED_IN_OBSERVATION_WINDOW' if settled is not None else 'NOT_SETTLED_IN_WINDOW',reexit_times=reexit,peak_excess_after_drop=max(D(0),max(x['y']-D('.5') for x in post)),high_clipped_steps=len([x for x in rows[:-1] if x['t']<4 and x['clipped']]),low_clipped_steps=len([x for x in rows[:-1] if x['t']>=4 and x['clipped']]),stopped_steps=len([x for x in rows[:-1] if x['integral_stopped']]),y_at_drop=post[0]['y'],z_at_drop=post[0]['z'],y_final=y,z_final=z,observation_window=[D(4),D(8)],band=D('.05'),minimum_remaining_duration=D(1),classification='sample points only')
  return rows,metrics
