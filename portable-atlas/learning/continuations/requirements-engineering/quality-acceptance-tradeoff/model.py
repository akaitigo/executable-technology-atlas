import json,sys
EXPECTED={'S1':2,'S2':4,'S3':6}
class Refused(Exception):pass
def exact(x,k,reason):
 if not isinstance(x,dict) or set(x)!=set(k):raise Refused(reason)
def integer(x,lo,hi,reason):
 if type(x)!=int or not lo<=x<=hi:raise Refused(reason)
def validate(x):
 exact(x,['purpose','old','new','candidates'],'FIELDS')
 if x['purpose']!='synthetic-three-receipts':raise Refused('PURPOSE')
 for k in ['old','new']:
  exact(x[k],['min_accuracy_bp','deadline_ms'],'THRESHOLD');integer(x[k]['min_accuracy_bp'],0,10000,'THRESHOLD');integer(x[k]['deadline_ms'],1,1000,'THRESHOLD')
 if not isinstance(x['candidates'],list) or len(x['candidates'])>6:raise Refused('CANDIDATES')
 seen=set()
 for c in x['candidates']:
  exact(c,['id','samples'],'CANDIDATE')
  if not isinstance(c['id'],str) or c['id'] not in list('ABCDEF') or c['id'] in seen:raise Refused('CANDIDATE')
  seen.add(c['id'])
  if not isinstance(c['samples'],list) or len(c['samples'])>3:raise Refused('SAMPLE')
  samples=set()
  for s in c['samples']:
   exact(s,['sample','output','elapsed_ms'],'SAMPLE')
   if not isinstance(s['sample'],str) or s['sample'] not in EXPECTED or s['sample'] in samples:raise Refused('SAMPLE')
   samples.add(s['sample'])
   if s['output'] is not None:integer(s['output'],0,9,'OUTPUT')
   if s['elapsed_ms'] is not None:integer(s['elapsed_ms'],0,1000,'TIME')
def decide(m,t):
 q='UNKNOWN' if m['observed_outputs']<3 else 'PASS' if m['correct_count']*10000>=t['min_accuracy_bp']*3 else 'FAIL'
 time='UNKNOWN' if m['observed_times']<3 else 'PASS' if m['worst_ms']<=t['deadline_ms'] else 'FAIL'
 a='FAIL' if 'FAIL' in [q,time] else 'INSUFFICIENT' if 'UNKNOWN' in [q,time] else 'PASS'
 return dict(R_CORRECT=q,R_TIMELY=time,acceptance=a)
def process(x):
 validate(x);rows=[]
 for c in sorted(x['candidates'],key=lambda c:c['id']):
  samples={s['sample']:s for s in c['samples']};trace=[];observed_outputs=observed_times=correct=0;times=[]
  for id,expected in EXPECTED.items():
   s=samples.get(id);output=s['output'] if s else None;elapsed=s['elapsed_ms'] if s else None
   if output is not None:observed_outputs+=1;correct+=int(output==expected)
   if elapsed is not None:observed_times+=1;times.append(elapsed)
   trace.append(dict(sample=id,expected=expected,output=output,elapsed_ms=elapsed,correct=(output==expected) if output is not None else None,present=s is not None))
  m=dict(observed_outputs=observed_outputs,observed_times=observed_times,correct_count=correct,accuracy_bp=correct*10000//3 if observed_outputs==3 else None,worst_ms=max(times) if observed_times==3 else None,eligible=observed_outputs==3 and observed_times==3)
  rows.append(dict(id=c['id'],metrics=m,old=decide(m,x['old']),new=decide(m,x['new']),samples=trace))
 dominance=[]
 for a in rows:
  for b in rows:
   am,bm=a['metrics'],b['metrics']
   if a['id']!=b['id'] and am['eligible'] and bm['eligible'] and am['correct_count']>=bm['correct_count'] and am['worst_ms']<=bm['worst_ms'] and (am['correct_count']>bm['correct_count'] or am['worst_ms']<bm['worst_ms']):dominance.append([a['id'],b['id']])
 dominated={b for a,b in dominance};pareto=[r['id'] for r in rows if r['metrics']['eligible'] and r['id'] not in dominated]
 return dict(status='OBSERVED',purpose=x['purpose'],thresholds={k:x[k] for k in ['old','new']},rows=rows,accepted={k:[r['id'] for r in rows if r[k]['acceptance']=='PASS'] for k in ['old','new']},changed=[r['id'] for r in rows if r['old']['acceptance']!=r['new']['acceptance']],pareto=pareto,dominance=dominance,excluded=[r['id'] for r in rows if not r['metrics']['eligible']],requirement_ids=['R-CORRECT','R-TIMELY'],needs=['N-RIGHT','N-FAST'],measurementSource='synthetic-fixture',testsExecuted=False,approval='UNCONFIRMED',validation='UNCONFIRMED')
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read())
  if '--fail' in sys.argv:raise RuntimeError('injected evaluator error')
  out=process(x);code=0
 except (json.JSONDecodeError,Refused) as e:out=dict(status='INPUT_REFUSED',reason=str(e) if isinstance(e,Refused) else 'JSON');code=2
 except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=type(e).__name__);code=1
 print(json.dumps(out));sys.exit(code)
