import json,sqlite3,sys
dbName,mode,tick,generation=sys.argv[1:]
message=json.load(sys.stdin);payload=json.dumps(message,sort_keys=True,separators=(',',':'))
db=sqlite3.connect(dbName,isolation_level=None);sql=[];db.set_trace_callback(sql.append)
status=None;stored=None;added=0
try:
 db.execute('BEGIN IMMEDIATE')
 if not isinstance(message,dict) or set(message)!=set(['id','delta']) or message['id']!='m1' or type(message['delta']) is not int or not 1<=message['delta']<=100:
  status='POISON';db.execute('ROLLBACK')
 else:
  row=db.execute('SELECT payload FROM inbox WHERE id=?',(message['id'],)).fetchone()
  if row:
   stored=row[0]
   if mode=='id-only':status='DUPLICATE_ID_ONLY'
   elif stored==payload:status='DUPLICATE'
   else:status='CONFLICT'
   db.execute('ROLLBACK')
  else:
   db.execute('INSERT INTO inbox(id,payload) VALUES (?,?)',(message['id'],payload))
   db.execute('INSERT INTO effects(message_id,delta,payload,tick,generation) VALUES (?,?,?,?,?)',(message['id'],message['delta'],payload,int(tick),int(generation)))
   db.execute('UPDATE account SET balance=balance+? WHERE singleton=1',(message['delta'],))
   db.execute('COMMIT');status='COMMITTED';added=1;stored=payload
 balance=db.execute('SELECT balance FROM account WHERE singleton=1').fetchone()[0]
finally:db.close()
code=65 if status=='POISON' else 66 if status=='CONFLICT' else 0
print(json.dumps({'status':status,'ackModel':code==0,'payload':payload,'storedPayload':stored,'effectAdded':added,'balance':balance,'sql':sql}))
sys.exit(code)
