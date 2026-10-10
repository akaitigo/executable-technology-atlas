import sys
sys.dont_write_bytecode=True
import checker,policy,json,pathlib,tempfile,shutil,hashlib
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
before=fp();checker.check();assert before==fp();out=[{'test':'read-only SHA256+mtime_ns','passed':True}]
d=json.loads((R/(R/'CURRENT').read_text().strip()/'result.json').read_text())
for caseId,remove in [('root-static','Adapter.__init__'),('root-dynamic','import_module')]:
 o=next(c for c in d['cases'] if c['id']==caseId)['observation']
 partial=[t for t in o['trace'] if t['calleeFunction']!=remove]
 assert any(t['calleeFunction']=='Adapter.add' for t in partial)
 assert policy.judge(o['edges'],partial)['verdict']=='INDETERMINATE'
 out.append({'test':'partial-missing-'+remove,'passed':True,'kind':'mutated evidence unit check; not new runtime observation','sameBusinessEdgeRetained':True})
for kind in ['same-business-forbidden','core-label-conforming','dynamic-target','missing-constructor-as-conforming','dynamic-extracted-by-import-AST','wrong-business-output','traceless-as-conforming','failure-reuses-answer']:
 with tempfile.TemporaryDirectory(prefix='dependency-negative-') as tmp:
  root=pathlib.Path(tmp)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
  c=next(c for c in d['cases'] if c['id']=='root-static');o=c['observation']
  if kind=='same-business-forbidden':o['judgment']['verdict']='RESPONSIBILITY_VIOLATION'
  elif kind=='core-label-conforming':
   c=next(c for c in d['cases'] if c['id']=='core-static');c['observation']['judgment']['verdict']='CONFORMING'
  elif kind=='dynamic-target':
   c=next(c for c in d['cases'] if c['id']=='root-dynamic')
   for t in c['observation']['trace']:
    if t['calleeFunction']=='import_module':t['requested']='os'
  elif kind=='missing-constructor-as-conforming':o['trace']=[t for t in o['trace'] if t['calleeFunction']!='Adapter.__init__']
  elif kind=='dynamic-extracted-by-import-AST':
   c=next(c for c in d['cases'] if c['id']=='root-dynamic');c['observation']['edges'].append({'from':'root','to':'adapter','syntax':'Import','line':4})
  elif kind=='wrong-business-output':o['output']=6
  elif kind=='traceless-as-conforming':
   c=next(c for c in d['cases'] if c['id']=='trace-off-root-static');c['observation']['judgment']['verdict']='CONFORMING'
  elif kind=='failure-reuses-answer':
   c=next(c for c in d['cases'] if c['id']=='execution-failure');c['outcome']='OBSERVED';c['observation']=o
  c['stdout']=json.dumps(c['observation'])+'\n';(run/c['id']/'stdout.txt').write_text(c['stdout'])
  raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejected':True})
  else:raise AssertionError(kind+' was accepted')
assert before==fp();print(json.dumps(out,indent=2))
