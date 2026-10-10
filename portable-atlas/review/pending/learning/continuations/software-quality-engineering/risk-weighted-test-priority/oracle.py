# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from fractions import Fraction
from pathlib import Path
H=json.loads((Path(__file__).parent/'hand-oracle.json').read_text())
def check(r):
 cfg=r['inputs'];h=next(c for c in H['cases'] if all(c[k]==cfg[k] for k in cfg));assert r['mode']=='FINITE_SELECTION_AND_REAL_PYTHON_PROBES'
 for k in ['status','greedy','optimal','score_gap']:assert r[k]==h[k],k
 assert not r['score_is_probability'] and not r['score_is_product_quality'];assert r['design']['tests']==H['tests'] and r['design']['weights']=={m['id']:m['weight'] for m in H['modes']} and r['design']['probes']=={m['id']:m['input'] for m in H['modes']}
 assert len(r['subsets'])==16
 for actual,literal in zip(r['subsets'],H['subsets']):
  for k,v in literal.items():assert actual[k]==v
  within=literal['cost']<=cfg['budget'];assert actual['within_budget']==within and actual['valid']==(within and (not cfg['critical_required'] or literal['critical_covered']))
 chosen=[]
 for step in r['greedy_trace']:
  assert step['round']==len(chosen) and step['selected_before']==chosen and len(step['candidates'])==4
  covered={m for t in H['tests'] if t['id'] in chosen for m in t['covers']};spent=sum(t['cost'] for t in H['tests'] if t['id'] in chosen)
  possibilities=[]
  for actual,t in zip(step['candidates'],H['tests']):
   gain=sum(m['weight'] for m in H['modes'] if m['id'] in set(t['covers'])-covered);allowed=t['id'] not in chosen and spent+t['cost']<=cfg['budget'] and gain>0
   reason='ALREADY_SELECTED' if t['id'] in chosen else ('OVER_BUDGET' if spent+t['cost']>cfg['budget'] else ('ZERO_GAIN' if gain==0 else 'ELIGIBLE'))
   assert actual==dict(test_id=t['id'],cost=t['cost'],marginal_gain=gain,ratio=str(Fraction(gain,t['cost'])),eligible=allowed,reason=reason)
   if allowed:possibilities.append((Fraction(gain,t['cost']),t['id']))
  choice=sorted(possibilities,key=lambda p:(-p[0],p[1]))[0][1] if possibilities else None;assert step['chosen']==choice
  if choice is not None:chosen.append(choice)
 assert sorted(chosen)==h['greedy']['selected'] and r['greedy_trace'][-1]['chosen'] is None
 for key,plan in [('greedy_execution',h['greedy']),('optimal_execution',h['optimal'])]:
  assert len(r[key])==4
  for actual,t in zip(r[key],H['tests']):
   run=plan is not None and plan['valid'] and t['id'] in plan['selected'];checks=[]
   if run:
    for mid in t['covers']:
     m=next(x for x in H['modes'] if x['id']==mid);expected=m['input'][2] in set(range(m['input'][0],m['input'][1]));assert expected==m['expected'];value=H['literal_actual'][cfg['variant']][mid]
     checks.append(dict(mode=mid,input=m['input'],expected=expected,actual=value,outcome='DETECTED' if expected!=value else 'NO_DIFFERENCE_DETECTED'))
   status=('DETECTED' if any(c['outcome']=='DETECTED' for c in checks) else 'NO_DIFFERENCE_DETECTED') if run else 'NOT_RUN'
   assert actual==dict(test_id=t['id'],status=status,checks=checks)
 return True
