import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,tempfile,shutil,copy
import checker
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in R.rglob('*') if p.is_file()}
a=fp();checker.check();results=[]
for kind in ['wrong-class','read-as-search','missing-root-gate','later-stop','deny-as-allow','wrong-errno','fault-disguised','failure-old-answer']:
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
  name={'wrong-class':'search-only-read','read-as-search':'directory-read-no-search','missing-root-gate':'search-only-read','later-stop':'directory-read-no-search','deny-as-allow':'file-no-read','wrong-errno':'missing-first','fault-disguised':'leaf-only-fault','failure-old-answer':'execution-failure'}[kind]
  c=next(c for c in d['cases'] if c['id']==name);o=c['observation']
  if kind=='wrong-class':o['gates'][2]['selectedClass']='group'
  elif kind=='read-as-search':o['gates'][-1]['required']='r'
  elif kind=='missing-root-gate':o['gates'].pop(0)
  elif kind=='later-stop':o['firstStop']={'node':'/vault/report','stage':'READ'}
  elif kind=='deny-as-allow':o['result']='ALLOW';o['allowed']=True;o['firstStop']=None
  elif kind=='wrong-errno':o['result']='EACCES'
  elif kind=='fault-disguised':o=copy.deepcopy(checker.EXPECTED['directory-read-no-search']);c['observation']=o
  else:o=copy.deepcopy(checker.EXPECTED['search-only-read']);c['observation']=o;c['outcome']='OBSERVED'
  c['stdout']=json.dumps(o)+'\n';(run/name/'stdout.txt').write_text(c['stdout']);(run/name/'command.json').write_text(json.dumps(c,indent=2)+'\n')
  raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  m=json.loads((run/'artifacts.json').read_text())
  for n,v in m['files'].items():b=(run/n).read_bytes();v.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
  (run/'artifacts.json').write_text(json.dumps(m,indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:results.append({'test':kind,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralRejected':True})
  else:raise AssertionError(kind+' escaped')
assert a==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':results},indent=2))
