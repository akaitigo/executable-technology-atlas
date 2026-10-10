import sys
sys.dont_write_bytecode=True
import checker,json,pathlib,tempfile,shutil,hashlib,sqlite3
R=pathlib.Path(__file__).resolve().parent
def fp():return {p.relative_to(R).as_posix():(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
before=fp();checker.check();assert before==fp();out=[{'test':'read-only SHA256+mtime_ns','passed':True}]
for kind in ['extra-effect','changed-inbox-payload','overwrite-original-dlq','delete-original-history','wrong-backoff-tick','conflict-acknowledged','wrong-added-effects','failure-old-answer']:
 with tempfile.TemporaryDirectory(prefix='dlq-negative-') as tmp:
  root=pathlib.Path(tmp)/'module';shutil.copytree(R,root);run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text())
  name='committed-changed' if kind=='conflict-acknowledged' else 'poison-corrected'
  c=next(c for c in d['cases'] if c['id']==name);o=c['observation']
  db=sqlite3.connect(run/c['db'])
  if kind=='extra-effect':
   db.execute("INSERT INTO effects(message_id,delta,payload,tick,generation) VALUES ('m1',7,?,4,1)",('{"delta":7,"id":"m1"}',));db.execute('UPDATE account SET balance=14')
  elif kind=='changed-inbox-payload':db.execute('UPDATE inbox SET payload=?',('{"delta":9,"id":"m1"}',))
  elif kind=='overwrite-original-dlq':db.execute('UPDATE dlq SET payload=? WHERE dlq_id=1',('{"delta":7,"id":"m1"}',))
  elif kind=='delete-original-history':db.execute('DELETE FROM dlq WHERE dlq_id=1')
  elif kind=='wrong-backoff-tick':db.execute('UPDATE attempts SET tick=2 WHERE generation=0 AND ordinal=2')
  elif kind=='conflict-acknowledged':db.execute("UPDATE attempts SET outcome='DUPLICATE_ID_ONLY',exit_code=0 WHERE generation=1");db.execute("UPDATE redrive SET terminal_outcome='DUPLICATE_ID_ONLY'")
  db.commit();db.close()
  o['final']=checker.rows(run/c['db'])
  if kind=='extra-effect':o['summary'].update(effectCount=2,addedEffects=2,balance=14)
  elif kind=='wrong-added-effects':o['summary']['addedEffects']=0
  elif kind=='failure-old-answer':
   c=next(c for c in d['cases'] if c['id']=='execution-failure');c['observation']=o;c['outcome']='OBSERVED'
  c['stdout']=json.dumps(c['observation'])+'\n';(run/c['id']/'stdout.txt').write_text(c['stdout'])
  raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
  files={p.relative_to(run).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file() and p.name!='artifacts.json'};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
  try:checker.check(root)
  except AssertionError:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'independentLiteralSQLOracleRejected':True})
  else:raise AssertionError(kind+' was accepted')
assert before==fp();print(json.dumps(out,indent=2))
