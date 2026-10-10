import pathlib,json,sqlite3,sys,tempfile,shutil,hashlib,datetime
A=pathlib.Path('artifacts')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class WALUnavailable(Exception):pass

def run(x):
 if not isinstance(x,dict) or set(x)!={'mode'}:return {'observed':False,'reason':'external paths or extra keys forbidden','failure':None,'summary':None,'sql':[],'trace':[],'events':[],'files':{},'tempCreated':False,'tempCleaned':None},2
 if x['mode'] not in ('compare','backup-only','main-only','wal-unavailable','sql-error'):return {'observed':False,'reason':'unknown mode','failure':None,'summary':None,'sql':[],'trace':[],'events':[],'files':{},'tempCreated':False,'tempCleaned':None},2
 A.mkdir();sql=[];trace=[];events=[];writer=None;phase='activateWAL';error=None;summary=None;failedRows=None;out={};tmpPath=None
 def execute(db,role,statement):
  started=utc()
  try:result=[list(r) for r in db.execute(statement).fetchall()]
  except sqlite3.Error as e:
   sql.append({'role':role,'sql':statement,'startedUtc':started,'endedUtc':utc(),'result':None,'error':{'type':type(e).__name__,'message':str(e)}});raise
  sql.append({'role':role,'sql':statement,'startedUtc':started,'endedUtc':utc(),'result':result,'error':None});return result
 def reader(path,role,immutable=True):
  db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro'+('&immutable=1' if immutable else ''),uri=True,isolation_level=None);db.set_trace_callback(lambda s:trace.append({'role':role,'sql':s}))
  try:
   execute(db,role,'PRAGMA query_only=ON');rows=execute(db,role,'SELECT id FROM records ORDER BY id');integrity=execute(db,role,'PRAGMA integrity_check');assert integrity==[['ok']];return [r[0] for r in rows]
  finally:db.close()
 with tempfile.TemporaryDirectory(prefix='wal-backup-owned-') as td:
  tmpPath=pathlib.Path(td);live=tmpPath/'live.sqlite'
  try:
   writer=sqlite3.connect(':memory:' if x['mode']=='wal-unavailable' else live,isolation_level=None);writer.set_trace_callback(lambda s:trace.append({'role':'writer','sql':s}))
   journal=execute(writer,'writer','PRAGMA journal_mode=WAL')[0][0];out['journalMode']=journal
   if journal!='wal':raise WALUnavailable('journal_mode result '+journal+'; WAL required')
   execute(writer,'writer','PRAGMA wal_autocheckpoint=0');out['pageSize']=execute(writer,'writer','PRAGMA page_size')[0][0]
   execute(writer,'writer','CREATE TABLE records(id INTEGER PRIMARY KEY)');execute(writer,'writer','BEGIN IMMEDIATE');execute(writer,'writer','INSERT INTO records VALUES (1)');execute(writer,'writer','COMMIT')
   checkpoint=execute(writer,'writer','PRAGMA wal_checkpoint(TRUNCATE)')[0];out['checkpoint']=checkpoint;assert checkpoint==[0,0,0]
   shutil.copyfile(live,A/'checkpoint-main.sqlite');checkpointRows=reader(A/'checkpoint-main.sqlite','checkpoint-main-read');beforeMain=sha(live)
   phase='row2Write';execute(writer,'writer','BEGIN IMMEDIATE')
   execute(writer,'writer','INSERT INTO missing_table VALUES (2)' if x['mode']=='sql-error' else 'INSERT INTO records VALUES (2)');execute(writer,'writer','COMMIT')
   phase='fixedSnapshot';sourceRows=reader(live,'source-new-connection',False);wal=tmpPath/'live.sqlite-wal';shm=tmpPath/'live.sqlite-shm';assert wal.exists() and wal.stat().st_size>32
   pairBefore={'main':sha(live),'wal':sha(wal)};assert beforeMain==pairBefore['main']
   for src,n in [(live,'source.sqlite'),(wal,'source.sqlite-wal'),(shm,'source.sqlite-shm')]:shutil.copyfile(src,A/n)
   events.append({'event':'snapshot-captured','utc':utc(),'writerOpen':True,'sourceRows':sourceRows,'mainAfterRow1Sha256':beforeMain,'mainAfterRow2Sha256':pairBefore['main'],'walSha256':pairBefore['wal']})
   mainRows=reader(A/'source.sqlite','captured-main-only-read');backupRows=None;copyRows=None;copySuccess=None;progress=[]
   if x['mode'] in ('compare','backup-only'):
    phase='backupAPI';destination=sqlite3.connect(A/'backup.sqlite');start=utc()
    try:writer.backup(destination,pages=-1,progress=lambda status,remaining,total:progress.append({'status':status,'remaining':remaining,'total':total,'utc':utc()}))
    finally:destination.close()
    events.append({'event':'backup-api-completed','startedUtc':start,'endedUtc':utc(),'progress':progress});backupRows=reader(A/'backup.sqlite','backup-new-connection')
   if x['mode'] in ('compare','main-only'):
    phase='mainCopy';start=utc();shutil.copyfile(live,A/'main-only.sqlite');copySuccess=True;events.append({'event':'main-only-copy-completed','startedUtc':start,'endedUtc':utc(),'sourceSha256':sha(live),'copySha256':sha(A/'main-only.sqlite')});copyRows=reader(A/'main-only.sqlite','copy-new-connection')
   pairAfter={'main':sha(live),'wal':sha(wal)};assert pairBefore==pairAfter;events.append({'event':'source-files-still-stable','utc':utc(),'before':pairBefore,'after':pairAfter,'writerOpen':True})
   summary={'sourceRows':sourceRows,'checkpointMainRows':checkpointRows,'sourceMainRows':mainRows,'backupRows':backupRows,'copyRows':copyRows,'backupMissing':[r for r in sourceRows if r not in backupRows] if backupRows is not None else None,'copyMissing':[r for r in sourceRows if r not in copyRows] if copyRows is not None else None,'fileCopySucceeded':copySuccess};phase='complete'
  except (sqlite3.Error,WALUnavailable) as e:error={'phase':phase,'type':type(e).__name__,'message':str(e)}
  finally:
   if writer is not None:writer.close();events.append({'event':'writer-closed','utc':utc()})
   if error and x['mode']=='sql-error' and live.exists():shutil.copyfile(live,A/'failed-source.sqlite');failedRows=reader(A/'failed-source.sqlite','failed-source-read')
 cleaned=not tmpPath.exists();events.append({'event':'owned-temp-cleaned','utc':utc(),'removed':cleaned});files={p.relative_to(A).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in A.rglob('*') if p.is_file()}
 out.update(observed=error is None,reason=None,failure=error,summary=summary,failedSourceRows=failedRows,sql=sql,trace=trace,events=events,files=files,tempCreated=True,tempCleaned=cleaned)
 return out,4 if error else 0
if __name__=='__main__':
 if sys.argv[1:]:print('unsupported arguments',file=sys.stderr);sys.exit(2)
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 o,code=run(x)
 if code==4:print(o['failure']['type']+': '+o['failure']['message'],file=sys.stderr)
 print(json.dumps(o));sys.exit(code)
