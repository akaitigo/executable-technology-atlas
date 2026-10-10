import base64,hashlib,json,sys,tempfile,time
from pathlib import Path
sys.dont_write_bytecode=True
class Refusal(Exception):pass
def require(ok,code):
 if not ok:raise Refusal(code)
def nonfinite(x):raise Refusal('nonfinite_json')
def unique(pairs):
 d={}
 for k,v in pairs:require(k not in d,'duplicate_key');d[k]=v
 return d
def validate(text):
 try:x=json.loads(text,parse_constant=nonfinite,object_pairs_hook=unique)
 except json.JSONDecodeError:raise Refusal('json_syntax')
 require(type(x) is dict and set(x)=={'schedule','initial','writer','delta','busy_ms'},'shape');require(type(x['schedule']) is str and x['schedule'] in ['stale','fresh','rollback','busy'],'schedule')
 for k,a,b in [('initial',0,100),('writer',0,100),('delta',1,10),('busy_ms',0,100)]:require(type(x[k]) is int and a<=x[k]<=b,'integer_range')
 require(x['writer']!=x['initial'],'writer_must_change');return x
def observe(x):
 from native import Connection,version,source,LIBRARY
 trace=[];handles=[]
 with tempfile.TemporaryDirectory(prefix='atlas-wal-upgrade-') as name:
  folder=Path(name);path=folder/'owned.sqlite'
  try:
   a=Connection(path);handles.append(a);b=Connection(path);handles.append(b)
   def sql(who,text,allow=False):
    conn=a if who=='reader' else b;start=time.monotonic_ns();r=conn.sql(text);r.update(connection=who,elapsed_ns=time.monotonic_ns()-start);trace.append(r)
    if r['return_code'] and not allow:raise RuntimeError('unexpected SQL failure '+str(r['extended_code']))
    return r
   sql('writer','PRAGMA journal_mode=WAL');sql('writer','PRAGMA wal_autocheckpoint=0');sql('writer','PRAGMA synchronous=FULL');sql('writer','CREATE TABLE evidence(id INTEGER PRIMARY KEY, value INTEGER NOT NULL)');sql('writer','INSERT INTO evidence VALUES(1,'+str(x['initial'])+')')
   for who in ['reader','writer']:sql(who,'PRAGMA busy_timeout='+str(x['busy_ms']))
   sql('reader','BEGIN');first=None
   if x['schedule']!='fresh':first=int(sql('reader','SELECT value FROM evidence WHERE id=1')['rows'][0][0])
   sql('writer','BEGIN IMMEDIATE');sql('writer','UPDATE evidence SET value='+str(x['writer'])+' WHERE id=1')
   if x['schedule']=='rollback':sql('writer','ROLLBACK')
   elif x['schedule']!='busy':sql('writer','COMMIT')
   if first is None:first=int(sql('reader','SELECT value FROM evidence WHERE id=1')['rows'][0][0])
   attempt=sql('reader','UPDATE evidence SET value=value+'+str(x['delta'])+' WHERE id=1',True);attempt_state=attempt['state'];after=int(sql('reader','SELECT value FROM evidence WHERE id=1')['rows'][0][0]);recovery_before=None;recovery_done=bool(attempt['return_code'])
   if recovery_done:
    # Expected SQL error is retained; an unexpected code remains an observed mismatch for checker.
    sql('reader','ROLLBACK')
    if x['schedule']=='busy':sql('writer','ROLLBACK')
    sql('reader','BEGIN');recovery_before=int(sql('reader','SELECT value FROM evidence WHERE id=1')['rows'][0][0]);sql('reader','UPDATE evidence SET value=value+'+str(x['delta'])+' WHERE id=1')
   sql('reader','COMMIT');final=int(sql('reader','SELECT value FROM evidence WHERE id=1')['rows'][0][0]);final_state=a.state()
   wal=Path(str(path)+'-wal').read_bytes();header=path.read_bytes()[:100];wal_info={'bytes':len(wal),'sha256':hashlib.sha256(wal).hexdigest(),'header_hex':wal[:32].hex()}
   for c in handles:c.close()
   handles=[];closed=path.read_bytes()
   summary={'category':'stale' if attempt['extended_code']==517 else 'busy' if attempt['extended_code']==5 else 'success' if attempt['extended_code']==0 else 'other-code','first_row':first,'upgrade_code':attempt['extended_code'],'upgrade_name':attempt['code_name'],'after_attempt_row':after,'attempt_state':attempt_state,'recovery_before':recovery_before,'final_row':final,'recovery_done':recovery_done,'status':'observed','input':x,'final_state':final_state}
   result={'status':'observed','summary':summary,'trace':trace,'engine':{'sqlite_version':version().decode(),'source_id':source().decode(),'api':'public native SQLite C API via stdlib ctypes','library':LIBRARY},'db_header_hex':header.hex(),'wal':wal_info,'closed_db_sha256':hashlib.sha256(closed).hexdigest(),'closed_db_base64':base64.b64encode(closed).decode(),'handles_closed':True}
  finally:
   for c in handles:c.close()
 result['temporary_cleanup']=not folder.exists();summary['temporary_cleanup']=result['temporary_cleanup'];return result
def main():
 try:
  text=sys.stdin.read(8193);require(len(text.encode('utf8'))<=4096,'input_size');x=validate(text)
 except Refusal as e:print(json.dumps({'status':'input_refusal','code':str(e),'summary':None,'temporary_cleanup':'not-created'}));return 2
 try:r=observe(x);code=0
 except Exception as e:r={'status':'execution_error','class':type(e).__name__,'message':str(e),'summary':None};code=3
 print(json.dumps(r,ensure_ascii=False,separators=(',',':')));return code
if __name__=='__main__':sys.exit(main())
