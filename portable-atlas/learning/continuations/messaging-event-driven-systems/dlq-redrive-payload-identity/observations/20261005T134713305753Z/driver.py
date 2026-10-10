import pathlib,json,sqlite3,subprocess,sys,datetime
R=pathlib.Path(__file__).resolve().parent
SCHEMA=[
'CREATE TABLE inbox(id TEXT PRIMARY KEY,payload TEXT NOT NULL)',
'CREATE TABLE effects(effect_no INTEGER PRIMARY KEY AUTOINCREMENT,message_id TEXT,delta INTEGER,payload TEXT,tick INTEGER,generation INTEGER)',
'CREATE TABLE account(singleton INTEGER PRIMARY KEY,balance INTEGER)',
'INSERT INTO account VALUES (1,0)',
'CREATE TABLE attempts(attempt_id INTEGER PRIMARY KEY,tick INTEGER,generation INTEGER,ordinal INTEGER,message_id TEXT,payload TEXT,outcome TEXT,exit_code INTEGER,source_dlq INTEGER)',
'CREATE TABLE dlq(dlq_id INTEGER PRIMARY KEY,generation INTEGER,tick INTEGER,message_id TEXT,payload TEXT,reason TEXT,attempt_ids TEXT,source_dlq INTEGER)',
'CREATE TABLE redrive(redrive_id INTEGER PRIMARY KEY,source_dlq INTEGER,generation INTEGER,start_tick INTEGER,payload TEXT,attempt_ids TEXT,terminal_dlq INTEGER,terminal_outcome TEXT)']
QUERIES={'inbox':'SELECT id,payload FROM inbox ORDER BY id','effects':'SELECT effect_no,message_id,delta,payload,tick,generation FROM effects ORDER BY effect_no','account':'SELECT singleton,balance FROM account','attempts':'SELECT attempt_id,tick,generation,ordinal,message_id,payload,outcome,exit_code,source_dlq FROM attempts ORDER BY attempt_id','dlq':'SELECT dlq_id,generation,tick,message_id,payload,reason,attempt_ids,source_dlq FROM dlq ORDER BY dlq_id','redrive':'SELECT redrive_id,source_dlq,generation,start_tick,payload,attempt_ids,terminal_dlq,terminal_outcome FROM redrive ORDER BY redrive_id'}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def snapshot(db):return {name:[list(row) for row in db.execute(sql)] for name,sql in QUERIES.items()}
def execute(x,dbName):
 if not isinstance(x,dict) or set(x)!=set(['seed','mode','redrive']) or type(x['seed']) is not bool:reason='invalid request'
 elif x['mode'] not in ('strict','id-only'):reason='invalid mode'
 elif x['redrive'] is not None and (not isinstance(x['redrive'],dict) or set(x['redrive'])!=set(['id','delta']) or x['redrive']['id']!='m1'):reason='same-ID redrive required'
 else:reason=None
 if reason:return {'observed':False,'reason':reason,'summary':None,'final':None,'commands':[]},2
 db=sqlite3.connect(dbName,isolation_level=None);driverSQL=[];db.set_trace_callback(driverSQL.append)
 for s in SCHEMA:db.execute(s)
 commands=[]
 def attempt(message,tick,generation,ordinal,source):
  aid=len(commands)+1;inp=(canonical(message)+'\n').encode();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
  argv=['python3','-B','../consumer.py',dbName,x['mode'],str(tick),str(generation)]
  p=subprocess.run([sys.executable,'-B',str(R/'consumer.py'),dbName,x['mode'],str(tick),str(generation)],input=inp,capture_output=True,timeout=5)
  observation=json.loads(p.stdout)
  if p.returncode not in (0,65,66):raise RuntimeError('unexpected consumer exit')
  commands.append({'attemptId':aid,'tick':tick,'generation':generation,'ordinal':ordinal,'sourceDLQ':source,'argv':argv,'stdin':inp.decode(),'startedUtc':started,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'observation':observation})
  db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?)',(aid,tick,generation,ordinal,message['id'],canonical(message),observation['status'],p.returncode,source))
  return aid,observation['status']
 def deadletter(message,tick,generation,ids,reason,source):
  did=db.execute('SELECT COALESCE(MAX(dlq_id),0)+1 FROM dlq').fetchone()[0]
  db.execute('INSERT INTO dlq VALUES (?,?,?,?,?,?,?,?)',(did,generation,tick,message['id'],canonical(message),reason,json.dumps(ids,separators=(',',':')),source))
  return did
 if x['seed']:attempt({'id':'m1','delta':7},-1,-1,1,None)
 original={'id':'m1','delta':'poison'};initialIds=[]
 for ordinal,tick in enumerate([0,1,3],1):
  aid,status=attempt(original,tick,0,ordinal,None);initialIds.append(aid)
 source=deadletter(original,3,0,initialIds,'poison-exhausted',None)
 before=snapshot(db);originalDLQ=list(before['dlq'][0]);terminal='NONE';terminalDLQ=None
 if x['redrive'] is not None:
  db.execute('INSERT INTO redrive VALUES (1,?,1,4,?,?,NULL,?)',(source,canonical(x['redrive']),'[]','STARTED'))
  ids=[]
  for ordinal,tick in enumerate([4,5,7],1):
   aid,status=attempt(x['redrive'],tick,1,ordinal,source);ids.append(aid)
   if status=='POISON':continue
   terminal=status;break
  if status=='POISON':terminal='POISON_EXHAUSTED'
  if terminal in ('POISON_EXHAUSTED','CONFLICT'):
   terminalDLQ=deadletter(x['redrive'],tick,1,ids,'poison-exhausted' if terminal=='POISON_EXHAUSTED' else 'identity-conflict',source)
  db.execute('UPDATE redrive SET attempt_ids=?,terminal_dlq=?,terminal_outcome=? WHERE redrive_id=1',(json.dumps(ids,separators=(',',':')),terminalDLQ,terminal))
 final=snapshot(db);db.close()
 summary={'effectCount':len(final['effects']),'baselineEffects':len(before['effects']),'addedEffects':len(final['effects'])-len(before['effects']),'balance':final['account'][0][1],'terminalRedrive':terminal,'initialAttemptTicks':[c['tick'] for c in commands if c['generation']==0],'redriveAttemptTicks':[c['tick'] for c in commands if c['generation']==1],'originalDLQPreserved':originalDLQ==final['dlq'][0]}
 return {'observed':True,'reason':None,'commands':commands,'beforeRedrive':before,'final':final,'summary':summary,'driverSQL':driverSQL},0
if __name__=='__main__':
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:
  print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 try:out,code=execute(x,sys.argv[1])
 except Exception as e:
  print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(4)
 print(json.dumps(out));sys.exit(code)
