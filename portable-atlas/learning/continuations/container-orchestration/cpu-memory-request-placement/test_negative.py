import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,tempfile,shutil,copy
import checker
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in R.rglob('*') if p.is_file()}
a=fp();checker.check();results=[]
for kind in ['pending-as-bound','memory-fault-hidden','overhead-removed','remaining-invented','greedy-as-optimal','enumeration-truncated','duplicate-id-success','failure-old-answer']:
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());name={'pending-as-bound':'memory-overhead','memory-fault-hidden':'ignore-memory-fault','overhead-removed':'memory-overhead','remaining-invented':'no-overhead','greedy-as-optimal':'greedy-trap','enumeration-truncated':'memory-overhead','duplicate-id-success':'refused-duplicate-id','failure-old-answer':'execution-failure'}[kind];c=next(c for c in d['cases'] if c['id']==name);o=c['observation']
  if kind=='pending-as-bound':o['placements'][1]['node']='nodeB';o['summary'].update(bound=2,pending=0,outcome='BOUND')
  elif kind=='memory-fault-hidden':c['audit']['capacityFeasible']=True;c['audit']['violations']=[]
  elif kind=='overhead-removed':o['trace'][0]['demand']['memory']=2
  elif kind=='remaining-invented':o['remaining']['nodeA']['memory']=1
  elif kind=='greedy-as-optimal':c['audit']['maxBound']=1
  elif kind=='enumeration-truncated':c['audit']['feasibleAssignments']=c['audit']['feasibleAssignments'][:1]
  else:o=copy.deepcopy(checker.EXPECTED['no-overhead']);c['observation']=o;c['outcome']='OBSERVED'
  c['stdout']=json.dumps(o)+'\n';(run/name/'stdout.txt').write_text(c['stdout']);(run/name/'command.json').write_text(json.dumps(c,indent=2)+'\n')
  au=json.loads((run/name/'audit-command.json').read_text());au['stdout']=json.dumps(c['audit'])+'\n';au['stdin']=json.dumps({'request':checker.REQUESTS[name],'observation':o})+'\n';(run/name/'audit-command.json').write_text(json.dumps(au,indent=2)+'\n');(run/name/'audit-stdout.txt').write_text(au['stdout']);(run/name/'audit-input.txt').write_text(au['stdin'])
  raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:results.append({'test':kind,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralOrEnumerationRejected':True})
  else:raise AssertionError(kind+' escaped')
assert a==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':results},indent=2))
