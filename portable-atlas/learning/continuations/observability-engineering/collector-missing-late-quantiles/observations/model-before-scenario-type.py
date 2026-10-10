# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
from fractions import Fraction
import datetime,platform
LATENCIES=[100,200,400,800,1800,2200]
SCHEDULES={'full':([2400]*6,[None]*6),'late':([2400]*4+[4000,5000],[None]*6),'missing-high':([2400]*4+[None]*2,[None]*4+[4500]*2),'missing-low':([None]*2+[2400]*4,[4500]*2+[None]*4),'empty':([None]*6,[4500]*6)}
def stats(values):
 if not values:return None
 s=sorted(values);n=len(s)
 return dict(n=n,mean_ms=str(Fraction(sum(s),n)),p50_ms=s[(n+1)//2-1],p95_ms=s[(95*n+99)//100-1])
def evaluate(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=dict(mode='SYNTHETIC_MEMORY_ONLY',started_utc=start,python=platform.python_version(),inputs=config)
 if not isinstance(config,dict) or set(config)!={'scenario','cutoff_ms','threshold_ms'} or config.get('scenario') not in SCHEDULES or type(config.get('cutoff_ms')) is not int or config['cutoff_ms'] not in (1000,2400,4000,4500,5000) or type(config.get('threshold_ms')) is not int or config['threshold_ms'] not in (400,800):
  out.update(status='REFUSED_INPUT',reason='exact scenario/cutoff_ms/threshold_ms; finite scenario, integer cutoff1000/2400/4000/4500/5000, integer threshold400/800',collector=None,teaching_oracle=None)
 else:
  arrivals,loss=SCHEDULES[config['scenario']];cut=config['cutoff_ms'];threshold=config['threshold_ms'];trace=[];seen=[]
  for i in range(6):
   a,l=arrivals[i],loss[i];observed=a is not None and a<=cut;missing=not observed and l is not None and l<=cut
   trace.append(dict(request_id='r'+str(i+1),issued_ms=0,state='SEEN' if observed else ('CONFIRMED_MISSING' if missing else 'PENDING'),arrival_ms=a if observed else None,loss_notice_ms=l if missing else None,latency_ms=LATENCIES[i] if observed else None))
   if observed:seen.append(LATENCIES[i])
  n=len(seen);missing=sum(e['state']=='CONFIRMED_MISSING' for e in trace);pending=6-n-missing;good=sum(v<=threshold for v in seen);ss=stats(seen);ts=stats(LATENCIES)
  collector=dict(trace=trace,seen_ids=[e['request_id'] for e in trace if e['state']=='SEEN'],counts=dict(issued=6,seen=n,pending=pending,confirmed_missing=missing,unobserved=6-n),seen_stats=ss,known_good=good,seen_good_ratio=str(Fraction(good,n)) if n else None,registered_good_lower=str(Fraction(good,6)),registered_good_upper=str(Fraction(good+6-n,6)),full_population_stats=None,imputed_values=[])
  truth_good=sum(v<=threshold for v in LATENCIES);truth=dict(label='OMNISCIENT_TEACHING_FIXTURE_NOT_COLLECTOR',ledger=[dict(request_id='r'+str(i+1),issued_ms=0,latency_ms=v,scheduled_arrival_ms=arrivals[i],scheduled_final_loss_notice_ms=loss[i]) for i,v in enumerate(LATENCIES)],stats=ts,good=truth_good,good_ratio=str(Fraction(truth_good,6)))
  bias=None if ss is None else dict(mean_ms=str(Fraction(ss['mean_ms'])-Fraction(ts['mean_ms'])),p50_ms=ss['p50_ms']-ts['p50_ms'],p95_ms=ss['p95_ms']-ts['p95_ms'])
  out.update(status='MODEL_COMPLETE',collector=collector,teaching_oracle=truth,teaching_bias_seen_minus_ledger=bias)
 out['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return out
if __name__=='__main__':
 import json
 print(json.dumps(evaluate(dict(scenario='missing-high',cutoff_ms=4500,threshold_ms=800)),indent=2))
