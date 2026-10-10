import pathlib,json,hashlib,sqlite3,tempfile,shutil,struct
R=pathlib.Path(__file__).resolve().parent
REQUESTS={'compare': {'mode': 'compare'}, 'backup-only': {'mode': 'backup-only'}, 'main-only': {'mode': 'main-only'}, 'refused-mode': {'mode': 'unknown'}, 'refused-external-path': {'mode': 'compare', 'path': '/not-task-owned/db.sqlite'}, 'wal-unavailable': {'mode': 'wal-unavailable'}, 'sql-error': {'mode': 'sql-error'}, 'execution-failure': {'rawInput': '{"mode":'}}
EXPECTED={'compare': {'sourceRows': [1, 2], 'checkpointMainRows': [1], 'sourceMainRows': [1], 'backupRows': [1, 2], 'copyRows': [1], 'backupMissing': [], 'copyMissing': [2], 'fileCopySucceeded': True}, 'backup-only': {'sourceRows': [1, 2], 'checkpointMainRows': [1], 'sourceMainRows': [1], 'backupRows': [1, 2], 'copyRows': None, 'backupMissing': [], 'copyMissing': None, 'fileCopySucceeded': None}, 'main-only': {'sourceRows': [1, 2], 'checkpointMainRows': [1], 'sourceMainRows': [1], 'backupRows': None, 'copyRows': [1], 'backupMissing': None, 'copyMissing': [2], 'fileCopySucceeded': True}}
def sha(b):return hashlib.sha256(b).hexdigest()
def sql_rows(path,immutable=True):
 db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro'+('&immutable=1' if immutable else ''),uri=True)
 try:
  db.execute('PRAGMA query_only=ON');assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';return [r[0] for r in db.execute('SELECT id FROM records ORDER BY id')]
 finally:db.close()
def pair_rows(folder):
 # WAL reader can update shm even with query_only. Copy captured bytes to owned temp; retained artifacts stay byte/mtime unchanged.
 with tempfile.TemporaryDirectory(prefix='wal-readonly-oracle-') as td:
  root=pathlib.Path(td)
  for n in ('source.sqlite','source.sqlite-wal','source.sqlite-shm'):shutil.copyfile(folder/n,root/n)
  return sql_rows(root/'source.sqlite',False)
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());assert (run/'stdout.json').read_bytes()==(run/'result.json').read_bytes();assert json.loads((root/'requests.json').read_text())==REQUESTS
 oracle=json.loads((root/'oracle.json').read_text());assert oracle['requests']==REQUESTS and oracle['literalRows']==EXPECTED and oracle['failureRows']=={'sql-error':[1],'wal-unavailable':None}
 for n,h in d['sourceHashes'].items():assert sha((root/n).read_bytes())==h,n
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():
  b=(run/n).read_bytes();assert sha(b)==v['sha256'] and len(b)==v['bytes'],n
 assert [c['id'] for c in d['cases']]==list(REQUESTS)
 for c in d['cases']:
  n=c['id'];x=REQUESTS[n];f=run/n;inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode();assert (f/'input.txt').read_bytes()==inp and sha(inp)==c['inputSha256'];assert (f/'stdout.txt').read_text()==c['stdout'] and (f/'stderr.txt').read_text()==c['stderr'] and json.loads((f/'command.json').read_text())==c;assert c['argv']==['python3','-B','../worker.py']
  if n=='execution-failure':assert c['exitCode']==3 and c['stdout']=='' and c['stderr'].startswith('JSONDecodeError:') and c['observation'] is None and c['outcome']=='EXECUTION_FAILURE';continue
  o=c['observation'];assert json.loads(c['stdout'])==o
  if n.startswith('refused-'):
   assert c['exitCode']==2 and c['outcome']=='REFUSED' and o['observed'] is False and o['summary'] is None and o['sql']==[] and o['files']=={} and o['tempCreated'] is False;continue
  assert o['tempCreated'] and o['tempCleaned'] and o['events'][-1]['event']=='owned-temp-cleaned' and o['events'][-1]['removed']
  af=f/'artifacts'
  for path,v in o['files'].items():b=(af/path).read_bytes();assert sha(b)==v['sha256'] and len(b)==v['bytes']
  assert [t['sql'] for t in o['trace']]==[s['sql'] for s in o['sql'] if s['error'] is None]
  if n in ('wal-unavailable','sql-error'):
   assert c['exitCode']==4 and c['outcome']=='EXECUTION_FAILURE' and o['observed'] is False and o['summary'] is None and o['failure'] is not None
   if n=='wal-unavailable':assert o['journalMode']=='memory' and o['failure']['type']=='WALUnavailable' and o['failure']['phase']=='activateWAL' and len(o['sql'])==1 and o['sql'][0]['result']==[['memory']] and o['files']=={}
   else:assert o['failure']['type']=='OperationalError' and o['failure']['phase']=='row2Write' and o['failure']['message']=='no such table: missing_table' and sql_rows(af/'failed-source.sqlite')==[1] and o['failedSourceRows']==[1]
   continue
  assert c['exitCode']==0 and c['stderr']=='' and c['outcome']=='OBSERVED' and o['observed'] and o['summary']==EXPECTED[n]
  assert o['journalMode']=='wal' and o['checkpoint']==[0,0,0]
  writer=[s for s in o['sql'] if s['role']=='writer'];assert [s['sql'] for s in writer]==['PRAGMA journal_mode=WAL','PRAGMA wal_autocheckpoint=0','PRAGMA page_size','CREATE TABLE records(id INTEGER PRIMARY KEY)','BEGIN IMMEDIATE','INSERT INTO records VALUES (1)','COMMIT','PRAGMA wal_checkpoint(TRUNCATE)','BEGIN IMMEDIATE','INSERT INTO records VALUES (2)','COMMIT']
  assert writer[0]['result']==[['wal']] and writer[1]['result']==[[0]]
  assert sql_rows(af/'checkpoint-main.sqlite')==[1] and sql_rows(af/'source.sqlite')==[1] and pair_rows(af)==[1,2]
  wal=(af/'source.sqlite-wal').read_bytes();magic,version,pageSize=struct.unpack('>III',wal[:12]);assert magic in (0x377f0682,0x377f0683) and version==3007000 and pageSize==o['pageSize'];assert len(wal)==32+24+pageSize
  snap=next(e for e in o['events'] if e['event']=='snapshot-captured');stable=next(e for e in o['events'] if e['event']=='source-files-still-stable');assert snap['writerOpen'] and stable['writerOpen'] and stable['before']==stable['after'];assert snap['mainAfterRow1Sha256']==snap['mainAfterRow2Sha256']==sha((af/'source.sqlite').read_bytes());assert snap['walSha256']==sha(wal)
  if n in ('compare','backup-only'):
   assert sql_rows(af/'backup.sqlite')==[1,2];api=next(e for e in o['events'] if e['event']=='backup-api-completed');assert api['progress'][-1]['status']==101 and api['progress'][-1]['remaining']==0 and api['progress'][-1]['total']>0
  else:assert not (af/'backup.sqlite').exists()
  if n in ('compare','main-only'):
   assert sql_rows(af/'main-only.sqlite')==[1] and (af/'main-only.sqlite').read_bytes()==(af/'source.sqlite').read_bytes();copy=next(e for e in o['events'] if e['event']=='main-only-copy-completed');assert copy['sourceSha256']==copy['copySha256']
  else:assert not (af/'main-only.sqlite').exists()
 return len(d['cases'])
if __name__=='__main__':print('PASS '+str(check())+' conditions; literal row table + independent read-only SQL/WAL; worker not imported')
