# SPDX-License-Identifier: Apache-2.0
# Independent Decimal velocity-area construction; no motion/model imports.
from decimal import Decimal,localcontext
D=Decimal
def expected(f,mode,h):
 with localcontext() as c:
  c.prec=70;v=D(str(f['v']));tau=D(str(f['tau'])) if mode=='delayed' else D(0);a=D(str(f['a']));L=D(str(f['obstacle_m']));T=D(str(f['horizon_s']));h=D(str(h));instant=mode=='instant'
  brake_time=D(0) if instant else v/a;delay_area=D(0) if instant else v*tau;triangle=D(0) if instant else v*brake_time/D(2);distance=delay_area+triangle;stop=D(0) if instant or v==0 else tau+brake_time
  def state(t):
   if instant or v==0 or t>=stop:return dict(t=t,x_m=distance,v_mps=D(0),phase='STOPPED')
   delay_time=min(t,tau);braking_time=max(D(0),t-tau);end_v=v-a*braking_time
   x=v*delay_time+(v+end_v)*braking_time/D(2)
   return dict(t=t,x_m=x,v_mps=end_v,phase='DELAY' if t<tau else 'BRAKING')
  times=[i*h for i in range(int(T/h)+1)]
  if times[-1]!=T:times.append(T)
  rows=[state(t) for t in times]
  if L==0:classification='INITIAL_CONTACT';contact=D(0)
  elif L>distance:classification='NO_CONTACT_IN_MODEL';contact=None
  elif L==distance:classification='TOUCH_AT_STOP';contact=stop
  else:
   classification='CONTACT_BEFORE_STOP'
   if L<=delay_area:contact=L/v
   else:
    # Rationalized root of braking displacement, separate from subtractive production root.
    rem=L-delay_area;contact=tau+D(2)*rem/(v+(v*v-D(2)*a*rem).sqrt())
  def event(kind,t):
   within=t<=T;sampled=t in times
   bracket=([t,t] if sampled else [max(x for x in times if x<t),min(x for x in times if x>t)]) if within else None
   return dict(kind=kind,time_s=t,within_window=within,on_sample=sampled,bracketing_samples_s=bracket,state=state(t),source='analytical event, not sample scan')
  events=[]
  if not instant and v>0 and tau>0:events.append(event('DELAY_END',tau))
  events.append(event('STOP',stop))
  if contact is not None:events.append(event('CONTACT',contact))
  return dict(rows=rows,events=events,delay_distance_m=delay_area,braking_distance_m=triangle,stop_distance_m=distance,stop_time_s=stop,contact_classification=classification,first_contact_time_s=contact,event_status='NO_CONTACT_EVENT' if contact is None else ('EVENT_IN_WINDOW' if contact<=T else 'FUTURE_EVENT_OUTSIDE_WINDOW'),horizon_motion='STOPPED_BY_HORIZON' if T>=stop else 'NOT_STOPPED_BY_HORIZON',final_state=rows[-1],effective_tau_s=tau,instant_velocity_jump_mps=v if instant else None,obstacle_m=L,horizon_s=T,units=dict(x='m',v='m/s',a='m/s^2',t='s'))
