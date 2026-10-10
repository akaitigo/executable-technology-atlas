import sys
sys.dont_write_bytecode=True
import checker,json,pathlib,tempfile,shutil,hashlib
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
before=fp();checker.check();assert before==fp()
results=[{'test':'read-only SHA256+mtime_ns','passed':True}]
def mutate(cases,kind):
 c=next(c for c in cases if c['id']=='bounded-backpressure');o=c['result']
 if kind=='hide-producer-wait':o['metrics']['offeredToFinishMean']=o['metrics']['admittedToFinishMean']
 elif kind=='queue-includes-active':o['states'][0]['queue']=['A','B','C']
 elif kind=='change-FIFO':o['states'][0]['producerWaiting']=['E','D']
 elif kind=='wrong-finish':o['jobs'][4]['finish']=4
 elif kind=='wrong-denominator':o['metrics']['latencyDenominator']=3
 elif kind=='false-refusal-success':
  c=next(c for c in cases if c['id']=='invalid-service');c['exitCode']=0;c['result']['accepted']=True
 c['stdout']=json.dumps(c['result'],ensure_ascii=False)+'\n'
for kind in ['hide-producer-wait','queue-includes-active','change-FIFO','wrong-finish','wrong-denominator','false-refusal-success']:
 with tempfile.TemporaryDirectory(prefix='twoqueue-negative-') as tmp:
  root=pathlib.Path(tmp)/'module';shutil.copytree(R,root)
  run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());mutate(d['cases'],kind)
  for c in d['cases']:(run/c['id']/'stdout.json').write_text(c['stdout'])
  raw=json.dumps(d,ensure_ascii=False,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'}
  (run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:results.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejected':True})
  else:raise AssertionError(kind+' was accepted')
assert before==fp()
print(json.dumps(results,indent=2))
