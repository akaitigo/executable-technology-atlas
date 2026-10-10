import sys
sys.dont_write_bytecode=True
import checker,json,pathlib,tempfile,shutil,hashlib
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
before=fp();checker.check();assert before==fp();out=[{'test':'read-only SHA256+mtime_ns','passed':True}]
for kind in ['ack-means-delivered','stale-marked-fresh','wrong-read-value','partition-auto-delivery','lost-queue-message','refusal-normal-answer','execution-failure-success']:
 with tempfile.TemporaryDirectory(prefix='replica-negative-') as tmp:
  root=pathlib.Path(tmp)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
  case=next(c for c in d['cases'] if c['id']=='failover-before-delivery');o=case['observation']
  if kind=='ack-means-delivered':o['trace'][0]['stores']['B']['revision']=1
  elif kind=='stale-marked-fresh':o['answer']['fresh']=True;o['reads'][-1]['fresh']=True;o['trace'][-1]['read']['fresh']=True
  elif kind=='wrong-read-value':o['answer']['value']='v1';o['reads'][-1]['value']='v1';o['trace'][-1]['read']['value']='v1'
  elif kind=='partition-auto-delivery':
   case=next(c for c in d['cases'] if c['id']=='partition-read');case['observation']['trace'][3]['status']='delivered'
  elif kind=='lost-queue-message':o['trace'][-1]['deliveryQueue']=[]
  elif kind=='refusal-normal-answer':
   case=next(c for c in d['cases'] if c['id']=='invalid-target');case['observation']['answer']={'revision':0,'fresh':True}
  elif kind=='execution-failure-success':
   case=next(c for c in d['cases'] if c['id']=='execution-failure');case['exitCode']=0;case['outcome']='normal';case['observation']={'accepted':True,'answer':{'revision':0,'fresh':True}}
  case['stdout']=json.dumps(case['observation'],ensure_ascii=False)+'\n';(run/case['id']/'stdout.txt').write_text(case['stdout'])
  raw=json.dumps(d,ensure_ascii=False,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejected':True})
  else:raise AssertionError(kind+' was accepted')
assert before==fp();print(json.dumps(out,indent=2))
