# SPDX-License-Identifier: Apache-2.0
import math
def valid_physics(s):
 if type(s) is not dict or set(s)!={'v','tau','a','obstacle_m','horizon_s','h'}:return False
 if any(type(x) not in [int,float] or not math.isfinite(x) for x in s.values()):return False
 return s['v']>=0 and s['tau']>=0 and s['a']>0 and s['obstacle_m']>=0 and s['horizon_s']>=0 and s['h']>0
def calculate(s,mode):
 if not valid_physics(s) or mode not in ['delayed','zero-delay','instant']:raise ValueError('physics/mode')
 v,a,L,T,h=[s[k] for k in ['v','a','obstacle_m','horizon_s','h']];tau=s['tau'] if mode=='delayed' else 0.
 instant=mode=='instant';stop=0. if instant or v==0 else tau+v/a;delay_d=0. if instant else v*tau;brake_d=0. if instant else v*v/(2*a);distance=delay_d+brake_d
 def state(t):
  if instant or v==0 or t>=stop:return dict(t=t,x_m=distance,v_mps=0.,phase='STOPPED')
  if t<tau:return dict(t=t,x_m=v*t,v_mps=v,phase='DELAY')
  q=t-tau;return dict(t=t,x_m=v*tau+v*q-.5*a*q*q,v_mps=max(0.,v-a*q),phase='BRAKING')
 times=[i*h for i in range(int(T/h)+1)]
 if times[-1]!=T:times.append(T)
 rows=[state(t) for t in times]
 if L==0:classification='INITIAL_CONTACT';contact=0.
 elif L>distance:classification='NO_CONTACT_IN_MODEL';contact=None
 elif L==distance:classification='TOUCH_AT_STOP';contact=stop
 else:
  classification='CONTACT_BEFORE_STOP'
  contact=L/v if L<=delay_d else tau+(v-math.sqrt(max(0.,v*v-2*a*(L-delay_d))))/a
 def event(kind,t):
  within=t<=T;on_sample=t in times
  bracket=([t,t] if on_sample else [max(x for x in times if x<t),min(x for x in times if x>t)]) if within else None
  return dict(kind=kind,time_s=t,within_window=within,on_sample=on_sample,bracketing_samples_s=bracket,state=state(t),source='analytical event, not sample scan')
 events=[]
 if not instant and v>0 and tau>0:events.append(event('DELAY_END',tau))
 events.append(event('STOP',stop))
 if contact is not None:events.append(event('CONTACT',contact))
 return dict(rows=rows,events=events,delay_distance_m=delay_d,braking_distance_m=brake_d,stop_distance_m=distance,stop_time_s=stop,contact_classification=classification,first_contact_time_s=contact,event_status='NO_CONTACT_EVENT' if contact is None else ('EVENT_IN_WINDOW' if contact<=T else 'FUTURE_EVENT_OUTSIDE_WINDOW'),horizon_motion='STOPPED_BY_HORIZON' if T>=stop else 'NOT_STOPPED_BY_HORIZON',final_state=rows[-1],effective_tau_s=tau,instant_velocity_jump_mps=v if instant else None,obstacle_m=L,horizon_s=T,units=dict(x='m',v='m/s',a='m/s^2',t='s'))
