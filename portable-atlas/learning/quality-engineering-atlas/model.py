# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform,json
from fractions import Fraction
DELAYS={'slow':[100,200,400,800,1800,2200],'boundary':[100,200,400,800,1800,2000],'healthy':[100,200,400,800,1000,1200]}
def stats(values):
 if not values:return dict(n=0,mean_ms=None,p50_ms=None,p95_ms=None)
 s=sorted(values);n=len(s);return dict(n=n,mean_ms=str(Fraction(sum(s),n)),p50_ms=s[(50*n+99)//100-1],p95_ms=s[(95*n+99)//100-1])
def run(case='slow',timeout_ms=2000,window_ms=2500):
 r=dict(mode='DETERMINISTIC_MODEL',inputs=dict(case=case,timeout_ms=timeout_ms,window_ms=window_ms),python=platform.python_version(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='REFUSED_INPUT',trace=[])
 if type(case) is not str or case not in DELAYS or type(timeout_ms) is not int or timeout_ms not in (1000,2000) or type(window_ms) is not int or window_ms not in (1500,2500):r['reason']='finite case, integer timeout1000/2000 and window1500/2500 ms required'
 else:
  received=[];waits=[];success=timeout=pending=seen=0
  for i,delay in enumerate(DELAYS[case],1):
   if delay<=timeout_ms and delay<=window_ms:outcome='RECEIVED_200';success+=1;received.append(delay)
   elif timeout_ms<=window_ms:outcome='CLIENT_TIMEOUT';timeout+=1
   else:outcome='PENDING_AT_WINDOW';pending+=1
   seen+=int(delay<=window_ms);wait=min(delay,timeout_ms,window_ms);waits.append(wait)
   r['trace'].append(dict(request_id='r'+str(i),arrival_ms=0,planned_server_delay_ms=delay,server200_generated_by_window=delay<=window_ms,server_attempt_status=200 if delay<=window_ms else None,client_outcome=outcome,client_received_status=200 if outcome=='RECEIVED_200' else None,observed_wait_ms=wait,response_latency_ms=delay if outcome=='RECEIVED_200' else None,right_censored=outcome!='RECEIVED_200'))
  r.update(status='MODEL_COMPLETE',counts=dict(issued=6,client_received=success,client_timeout=timeout,pending=pending,server200_attempts=seen),metrics=dict(deadline_confirmed_ratio=str(Fraction(success,6)),deadline_upper_ratio=str(Fraction(success+pending,6)),client_received200_ratio=str(Fraction(success,success)) if success else None,server_attempt200_ratio=str(Fraction(seen,seen)) if seen else None,received_latency_stats=stats(received),all_observed_wait_stats=stats(waits),full_response_latency_stats=None),censored_ids=[x['request_id'] for x in r['trace'] if x['right_censored']])
 r['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return r
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
