import base64,copy,hashlib,json,sqlite3,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,collect,digest,snapshot
def verify(rows):
 for row in rows:
  run=row['run'];r=run['result'];core=r['summary'] if r['status']=='observed' else r;assert core==row['expected'],row['id'];assert run['exit']==(2 if r['status']=='input_refusal' else 0) and not run['stderr'];assert json.loads(run['stdout'])==r
  if r['status']!='observed':continue
  assert r['temporary_cleanup'] and r['handles_closed'];db=base64.b64decode(r['closed_db_base64']);assert hashlib.sha256(db).hexdigest()==r['closed_db_sha256'] and db[:16]==b'SQLite format 3\x00';assert bytes.fromhex(r['db_header_hex'])[:16]==db[:16]
  # Independently read only the owned exported closed DB via the Python wrapper.
  with tempfile.TemporaryDirectory(prefix='atlas-wal-check-') as name:
   path=Path(name)/'closed.sqlite';path.write_bytes(db)
   conn=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)
   try:conn.execute('PRAGMA query_only=ON');assert conn.execute('SELECT value FROM evidence WHERE id=1').fetchall()==[(core['final_row'],)]
   finally:conn.close()
  trace=r['trace'];errors=[t for t in trace if t['return_code']];assert [t['extended_code'] for t in errors]==([core['upgrade_code']] if core['recovery_done'] else [])
  for t in errors:assert t['connection']=='reader' and t['primary_code']==5 and t['state']==core['attempt_state']
  statements=[(t['connection'],t['sql']) for t in trace]
  begin_index=statements.index(('reader','BEGIN'));select_index=next(i for i,t in enumerate(trace) if t['connection']=='reader' and t['sql'].startswith('SELECT'))
  writer_end=('writer','ROLLBACK' if core['input']['schedule']=='rollback' else 'COMMIT')
  if core['input']['schedule']=='fresh':assert begin_index<statements.index(writer_end)<select_index
  elif core['input']['schedule']!='busy':assert begin_index<select_index<statements.index(writer_end)
  if core['recovery_done']:assert statements.count(('reader','BEGIN'))==2 and ('reader','ROLLBACK') in statements
def main():
 before=snapshot();rows=collect()['rows'];verify(rows);caught=[]
 for name,idx,key,value in [('lost-snapshot',0,'first_row',20),('busy-not-snapshot',0,'upgrade_code',5),('failed-tx-closed',0,'attempt_state',{'autocommit':1,'txn_state':0}),('retry-stale-value',0,'final_row',11),('invented-timeout-name',3,'upgrade_name','SQLITE_BUSY_TIMEOUT')]:
  m=copy.deepcopy(rows);m[idx]['run']['result']['summary'][key]=value
  try:verify(m)
  except AssertionError:caught.append(name)
  else:raise AssertionError('mutant survived '+name)
 js=ROOT/'observation-data.js'
 if js.exists():
  raw=json.loads(js.read_text().split('=',1)[1].rstrip(';\n'));verify(raw['rows']);assert raw['source_digests']=={n:digest(ROOT/n) for n in SOURCES};d=ROOT/'observations'/raw['run_id'];assert json.loads((d/'raw.json').read_text())==raw;idx=json.loads((d/'artifact-index.json').read_text());assert 'artifact-index.json' not in idx['files'];assert all(digest(d/n)==h for n,h in idx['files'].items())
  for row in raw['rows']:
   if row['run']['result']['status']=='observed':assert (d/(row['id']+'.closed.sqlite')).read_bytes()==base64.b64decode(row['run']['result']['closed_db_base64'])
 assert before==snapshot();print(json.dumps({'literal_schedules':13,'closed_DB_reads':8,'mutants_rejected':caught,'unit_read_only':True,'owned_tmp_cleaned':True}));return 0
if __name__=='__main__':sys.exit(main())
