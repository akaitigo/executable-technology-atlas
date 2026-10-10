# Separate rational/set evaluator. No model import.
import json,sys
from fractions import Fraction
EXPECTED={'S1':2,'S2':4,'S3':6}
def check(result,x,literal=None):
 if literal and 'status' in literal:assert result==literal;return
 rows=[]
 for c in sorted(x['candidates'],key=lambda c:c['id']):
  samples={s['sample']:s for s in c['samples']};outputs={k:s['output'] for k,s in samples.items() if s['output'] is not None};times={k:s['elapsed_ms'] for k,s in samples.items() if s['elapsed_ms'] is not None};matches={k for k,v in outputs.items() if v==EXPECTED[k]};oc,tc=len(outputs),len(times);complete=oc==tc==3;worst=max(times.values()) if tc==3 else None
  metric=dict(observed_outputs=oc,observed_times=tc,correct_count=len(matches),accuracy_bp=int(Fraction(len(matches),3)*10000) if oc==3 else None,worst_ms=worst,eligible=complete)
  decisions={}
  for k in ['old','new']:
   q='UNKNOWN' if oc!=3 else 'PASS' if Fraction(len(matches),3)>=Fraction(x[k]['min_accuracy_bp'],10000) else 'FAIL';t='UNKNOWN' if tc!=3 else 'PASS' if all(v<=x[k]['deadline_ms'] for v in times.values()) else 'FAIL';a={'PASS':'PASS','UNKNOWN':'INSUFFICIENT','FAIL':'FAIL'}[max([q,t],key=lambda v:['PASS','UNKNOWN','FAIL'].index(v))];decisions[k]=dict(R_CORRECT=q,R_TIMELY=t,acceptance=a)
  trace=[dict(sample=k,expected=v,output=samples.get(k,{}).get('output'),elapsed_ms=samples.get(k,{}).get('elapsed_ms'),correct=(outputs[k]==v) if k in outputs else None,present=k in samples) for k,v in EXPECTED.items()]
  rows.append(dict(id=c['id'],metrics=metric,samples=trace,**decisions))
 points={r['id']:(r['metrics']['correct_count'],-r['metrics']['worst_ms']) for r in rows if r['metrics']['eligible']};relations=sorted([[a,b] for a,u in points.items() for b,v in points.items() if u!=v and all(ui>=vi for ui,vi in zip(u,v))]);blocked={b for a,b in relations};front=sorted(set(points)-blocked)
 expected=dict(status='OBSERVED',purpose=x['purpose'],thresholds={k:x[k] for k in ['old','new']},rows=rows,accepted={k:[r['id'] for r in rows if r[k]['acceptance']=='PASS'] for k in ['old','new']},changed=[r['id'] for r in rows if r['old']['acceptance']!=r['new']['acceptance']],pareto=front,dominance=relations,excluded=[r['id'] for r in rows if r['id'] not in points],requirement_ids=['R-CORRECT','R-TIMELY'],needs=['N-RIGHT','N-FAST'],measurementSource='synthetic-fixture',testsExecuted=False,approval='UNCONFIRMED',validation='UNCONFIRMED')
 assert result==expected
 if literal:
  for k in ['old','new']:assert {r['id']:r[k]['acceptance'] for r in rows}==literal[k],k
  assert result['pareto']==literal['pareto'] and result['dominance']==literal['dominance']
if __name__=='__main__':
 a=json.loads(sys.stdin.read());check(a['result'],a['input']);print(json.dumps(dict(status='passed',independent=True)))
