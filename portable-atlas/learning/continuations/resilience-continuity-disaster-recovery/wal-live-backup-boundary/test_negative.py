import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,tempfile,shutil,sqlite3,copy
import checker
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():[hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns] for p in R.rglob('*') if p.is_file()}
a=fp();checker.check();results=[]
for kind in ['backup-loses-row2','copy-invents-row2','wal-missing','source-stability-false','copy-success-as-complete','failure-normal-answer','checkpoint-order','wal-header-metadata']:
 with tempfile.TemporaryDirectory() as td:
  root=pathlib.Path(td)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());name='wal-unavailable' if kind=='failure-normal-answer' else 'compare';c=next(c for c in d['cases'] if c['id']==name);o=c['observation'];af=run/name/'artifacts'
  if kind in ('backup-loses-row2','copy-invents-row2'):
   path=af/('backup.sqlite' if kind=='backup-loses-row2' else 'main-only.sqlite');db=sqlite3.connect(path);db.execute('DELETE FROM records WHERE id=2' if kind=='backup-loses-row2' else 'INSERT INTO records VALUES (2)');db.commit();db.close()
   field='backupRows' if kind=='backup-loses-row2' else 'copyRows';o['summary'][field]=[1] if kind=='backup-loses-row2' else [1,2];o['summary']['backupMissing' if kind=='backup-loses-row2' else 'copyMissing']=[2] if kind=='backup-loses-row2' else []
  elif kind=='wal-missing':(af/'source.sqlite-wal').unlink();o['files'].pop('source.sqlite-wal')
  elif kind=='source-stability-false':next(e for e in o['events'] if e['event']=='source-files-still-stable')['after']['main']='0'*64
  elif kind=='copy-success-as-complete':o['summary']['copyMissing']=[]
  elif kind=='failure-normal-answer':o['summary']=copy.deepcopy(checker.EXPECTED['compare'])
  elif kind=='checkpoint-order':
   i=next(i for i,s in enumerate(o['sql']) if s['sql']=='PRAGMA wal_checkpoint(TRUNCATE)');v=o['sql'].pop(i);j=next(i for i,s in enumerate(o['sql']) if s['sql']=='INSERT INTO records VALUES (2)');o['sql'].insert(j+2,v)
   o['trace']=[{'role':s['role'],'sql':s['sql']} for s in o['sql'] if s['error'] is None]
  else:o['pageSize']*=2
  for n,v in list(o['files'].items()):
   p=af/n;b=p.read_bytes();v.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
  c['stdout']=json.dumps(o)+'\n';(run/name/'stdout.txt').write_text(c['stdout']);(run/name/'command.json').write_text(json.dumps(c,indent=2)+'\n');raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except (AssertionError,FileNotFoundError,sqlite3.Error):results.append({'test':kind,'passed':True,'rawDerivedArtifactHashesCoherent':True,'independentLiteralOrReadOnlySQLRejected':True})
  else:raise AssertionError(kind+' escaped')
assert a==fp();print(json.dumps({'readonlySHA256MtimeNs':True,'negativeTests':results},indent=2))
