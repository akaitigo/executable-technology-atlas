# SPDX-License-Identifier: Apache-2.0
import math
from cases import FIXTURES,HAND
from area_oracle import expected
def equal(a,b):
 if b is None or type(b) in [str,bool]:assert type(a) is type(b) and a==b
 elif type(b) is dict:
  assert set(a)==set(b)
  for k in b:equal(a[k],b[k])
 elif type(b) is list:
  assert len(a)==len(b)
  for x,y in zip(a,b):equal(x,y)
 else:assert type(a) in [int,float] and math.isfinite(a) and abs(a-float(b))<=1e-10*max(1.,abs(float(b)))
def projection(r):return {k:r[k] for k in ['inputs','status','delay_distance_m','braking_distance_m','stop_distance_m','stop_time_s','contact_classification','first_contact_time_s','event_status','horizon_motion','final_state']}
def check(r):
 assert r['status']=='EXECUTED' and HAND['fixed_before_implementation'];c=r['inputs'];f=FIXTURES[c['fixture']];want=expected(f,c['mode'],c['h']);equal({k:r[k] for k in want},want)
 hand=f['hand'];name={'delayed':'delay_distance_m','zero-delay':'zero_delay_distance_m','instant':'instant_distance_m'}[c['mode']];equal(r['stop_distance_m'],hand[name])
 if c['mode']=='delayed':equal(r['stop_time_s'],hand['delay_stop_time_s'])
 for row in r['rows']:assert row['v_mps']>=0
 if r['first_contact_time_s'] is not None:
  e=next(e for e in r['events'] if e['kind']=='CONTACT');equal(e['state']['x_m'],f['obstacle_m'])
 if c['fixture']=='between-samples' and c['mode']=='delayed':
  e=next(e for e in r['events'] if e['kind']=='CONTACT');assert not e['on_sample'];equal(e['time_s'],.6339745962155614)
