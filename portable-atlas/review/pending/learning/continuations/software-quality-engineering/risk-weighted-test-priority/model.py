# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import datetime,platform
from fractions import Fraction
WEIGHTS={'A':8,'B':7,'C':6}
TESTS=[dict(id='T1',cost=3,covers=['A','B']),dict(id='T2',cost=2,covers=['A','C']),dict(id='T3',cost=2,covers=['B']),dict(id='T4',cost=1,covers=['C'])]
PROBES={'A':[2,5,2],'B':[2,5,5],'C':[2,2,2]}
def summarize(ids,budget,critical):
 selected=sorted(ids);tests=[t for t in TESTS if t['id'] in selected];covered=sorted({m for t in tests for m in t['covers']});cost=sum(t['cost'] for t in tests)
 return dict(selected=selected,cost=cost,covered=covered,score=sum(WEIGHTS[m] for m in covered),valid=cost<=budget and (not critical or 'A' in covered))
def execute(plan,variant):
 rows=[]
 for t in TESTS:
  run=plan is not None and plan['valid'] and t['id'] in plan['selected'];checks=[]
  if run:
   for m in t['covers']:
    lo,hi,x=PROBES[m];expected=x in list(range(lo,hi))
    actual={'normal':lo<=x<hi,'lower':lo<x<hi,'upper':lo<hi and lo<=x<=hi,'empty':(lo==hi and x==lo) or lo<=x<hi}[variant]
    checks.append(dict(mode=m,input=[lo,hi,x],expected=expected,actual=actual,outcome='DETECTED' if actual!=expected else 'NO_DIFFERENCE_DETECTED'))
  rows.append(dict(test_id=t['id'],status=('DETECTED' if any(c['outcome']=='DETECTED' for c in checks) else 'NO_DIFFERENCE_DETECTED') if run else 'NOT_RUN',checks=checks))
 return rows

def evaluate(config):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=dict(mode='FINITE_SELECTION_AND_REAL_PYTHON_PROBES',started_utc=start,python=platform.python_version(),inputs=config)
 if not isinstance(config,dict) or set(config)!={'budget','critical_required','variant'} or type(config.get('budget')) is not int or config['budget'] not in range(6) or type(config.get('critical_required')) is not bool or type(config.get('variant')) is not str or config['variant'] not in ('normal','lower','upper','empty'):
  out.update(status='REFUSED_INPUT',reason='exact keys budget/critical_required/variant; integer budget0..5, exact bool critical_required, finite variant',greedy=None,optimal=None,subsets=[],greedy_trace=[])
 else:
  b,critical,v=config['budget'],config['critical_required'],config['variant'];ids=[];trace=[]
  while True:
   current=summarize(ids,b,critical);candidates=[]
   for t in TESTS:
    gain=sum(WEIGHTS[m] for m in t['covers'] if m not in current['covered']);eligible=t['id'] not in ids and t['cost']+current['cost']<=b and gain>0
    candidates.append(dict(test_id=t['id'],cost=t['cost'],marginal_gain=gain,ratio=str(Fraction(gain,t['cost'])),eligible=eligible,reason='ALREADY_SELECTED' if t['id'] in ids else ('OVER_BUDGET' if t['cost']+current['cost']>b else ('ZERO_GAIN' if gain==0 else 'ELIGIBLE'))))
   eligible=[t for t in candidates if t['eligible']];chosen=sorted(eligible,key=lambda t:(-Fraction(t['ratio']),t['test_id']))[0]['test_id'] if eligible else None
   trace.append(dict(round=len(ids),selected_before=ids[:],candidates=candidates,chosen=chosen))
   if chosen is None:break
   ids.append(chosen)
  greedy=summarize(ids,b,critical);subsets=[]
  for mask in range(16):
   plan=summarize([t['id'] for i,t in enumerate(TESTS) if mask&(1<<i)],b,critical);subsets.append(dict(mask=mask,critical_covered='A' in plan['covered'],within_budget=plan['cost']<=b,**plan))
  feasible=[s for s in subsets if s['valid']];best=sorted(feasible,key=lambda s:(-s['score'],s['cost'],s['selected']))[0] if feasible else None
  optimal={k:best[k] for k in ['selected','cost','covered','score','valid']} if best else None
  out.update(status='MODEL_COMPLETE' if optimal else 'INFEASIBLE',design=dict(weights=WEIGHTS,tests=TESTS,probes=PROBES),greedy=greedy,optimal=optimal,greedy_trace=trace,subsets=subsets,score_gap=optimal['score']-greedy['score'] if optimal and greedy['valid'] else None,greedy_execution=execute(greedy,v),optimal_execution=execute(optimal,v),score_is_probability=False,score_is_product_quality=False)
 out['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();return out
if __name__=='__main__':
 import json
 print(json.dumps(evaluate(dict(budget=3,critical_required=True,variant='upper')),indent=2))
