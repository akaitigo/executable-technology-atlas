import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,tempfile,shutil,copy
import checker
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in R.rglob('*') if p.is_file()}
a=fp();checker.check();results=[]
for kind in ['epoch-key-omitted','new-epoch-stale','latest-regressed','history-discarded','duplicate-added','conflict-accepted','identity-payload-changed','failure-old-answer']:
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
  name='duplicate-conflict' if kind in ('duplicate-added','conflict-accepted','identity-payload-changed') else 'execution-failure' if kind=='failure-old-answer' else 'epoch-order'
  c=next(c for c in d['cases'] if c['id']==name);o=c['observation']
  if kind=='epoch-key-omitted':o['trace'][1]['key']=['a',1]
  elif kind=='new-epoch-stale':o['trace'][1]['decision']='STALE_REJECT';o['trace'][1]['historyAdded']=False;o['trace'][1]['latestUpdated']=False
  elif kind=='latest-regressed':o['trace'][-1]['latest']=copy.deepcopy(o['trace'][-1]['input']);o['final']['latest']=copy.deepcopy(o['trace'][-1]['input']);o['summary'].update(latestEpoch=1,latestSeq=5,latestValue=50)
  elif kind=='history-discarded':o['trace'][-1]['history'].pop();o['final']['history'].pop();o['summary']['historyCount']=2
  elif kind=='duplicate-added':o['trace'][3]['historyAdded']=True;o['trace'][3]['history'].append(copy.deepcopy(o['trace'][3]['input']))
  elif kind=='conflict-accepted':o['trace'][-1]['decision']='ACCEPT_LATEST';o['trace'][-1]['latestUpdated']=True;o['summary']['lastDecision']='ACCEPT_LATEST'
  elif kind=='identity-payload-changed':o['trace'][-1]['identities'][1]['payload']='{"value":999}';o['final']['identities'][1]['payload']='{"value":999}'
  else:o=copy.deepcopy(checker.EXPECTED['epoch-order']);c['observation']=o;c['outcome']='OBSERVED'
  c['stdout']=json.dumps(o)+'\n';(run/name/'stdout.txt').write_text(c['stdout']);(run/name/'command.json').write_text(json.dumps(c,indent=2)+'\n')
  for step in o['trace']:(run/name/('arrival-'+str(step['arrival'])+'.json')).write_text(json.dumps(step,indent=2)+'\n')
  raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'}
  (run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:results.append({'test':kind,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralRejected':True})
  else:raise AssertionError(kind+' escaped')
assert a==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':results},indent=2))
