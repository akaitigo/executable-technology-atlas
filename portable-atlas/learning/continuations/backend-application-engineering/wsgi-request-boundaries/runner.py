"""Actual stdlib HTTP client -> owned wsgiref server -> owned SQLite, sequential groups."""
import json,sqlite3,threading,tempfile,shutil,http.client,io,datetime,hashlib,uuid,argparse,sys,platform
from pathlib import Path
from wsgiref.simple_server import make_server,WSGIRequestHandler
from adapter import App
ROOT=Path(__file__).resolve().parent
class Handler(WSGIRequestHandler):
 def get_stderr(self):return self.server.lesson_errors
 def log_message(self,format,*args):self.server.lesson_access.append(format%args)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_snapshot(path):
 c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
 try:return dict(orders=[list(r) for r in c.execute('SELECT id,units FROM orders ORDER BY id')],outbox=[list(r) for r in c.execute('SELECT order_id,event FROM outbox ORDER BY order_id')],integrity=c.execute('PRAGMA integrity_check').fetchone()[0])
 finally:c.close()
def execute_group(group,destination,raw):
 row=dict(id=group['id'],cases=[],cleanup={});raw['groups'].append(row);server=None;thread=None;tmp=None
 try:
  tmp=tempfile.TemporaryDirectory(prefix='.owned-wsgi-',dir=ROOT);db=Path(tmp.name)/'live.sqlite';setup=sqlite3.connect(db);setup.executescript('CREATE TABLE orders(id INTEGER PRIMARY KEY,units INTEGER NOT NULL);CREATE TABLE outbox(order_id INTEGER PRIMARY KEY,event TEXT NOT NULL);');setup.close();row['setup_connection']='separate from request acquisitions, closed'
  app=App(db);server=make_server('127.0.0.1',0,app,handler_class=Handler);server.lesson_errors=io.StringIO();server.lesson_access=[];row['host']='127.0.0.1';row['port']=server.server_port;thread=threading.Thread(target=server.serve_forever,kwargs=dict(poll_interval=0.02),daemon=True);thread.start()
  for case in group['cases']:
   c=dict(id=case['id'],request=case,http_command='http.client.HTTPConnection dynamic loopback; putrequest/putheader/endheaders/getresponse');row['cases'].append(c);client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3);errors_before=len(server.lesson_errors.getvalue());access_before=len(server.lesson_access)
   try:
    body=case['body'].encode();client.putrequest(case['method'],case['path']);
    for k,v in case['headers'].items():client.putheader(k,v)
    client.endheaders(body);response=client.getresponse();received=response.read();c['response']=dict(status=response.status,reason=response.reason,headers=list(response.getheaders()),body_hex=received.hex(),body=json.loads(received));c['app']=app.requests[-1];c['error_stream_delta']=server.lesson_errors.getvalue()[errors_before:];c['access_log']=server.lesson_access[access_before:]
   finally:client.close();c['http_client_closed']=client.sock is None
   snapshot=destination/(case['id']+'.sqlite');shutil.copyfile(db,snapshot);c['db_snapshot']=str(snapshot.relative_to(ROOT));c['db_sha256']=sha(snapshot);c['independent_observer']=read_snapshot(snapshot)
 except Exception as e:row['execution_failure']=dict(type=type(e).__name__,message=str(e))
 finally:
  if server is not None:
   if thread is not None and thread.is_alive():server.shutdown();thread.join(timeout=2)
   server.server_close();row['cleanup']['server_closed']=server.socket.fileno()==-1;row['cleanup']['server_thread_stopped']=thread is None or not thread.is_alive()
  else:row['cleanup']['server_not_created']=True
  if tmp is not None:
   path=Path(tmp.name);tmp.cleanup();row['cleanup']['live_temp_removed']=not path.exists()
 return row
def run(destination):
 destination.mkdir(parents=True,exist_ok=False);f=json.loads((ROOT/'fixture.json').read_text());r=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B runner.py --record',environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,system=platform.system(),release=platform.release()),fixture=f,source_sha256={n:sha(ROOT/n) for n in ['fixture.json','oracle.json','EXPECTATIONS.md','adapter.py','runner.py']},groups=[])
 for g in f['groups']:execute_group(g,destination,r)
 r['execution_failures']=sum('execution_failure' in g for g in r['groups']);r['exit_code']=1 if r['execution_failures'] else 0;return r
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');args=a.parse_args()
 if args.record:
  name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8];dest=ROOT/'evidence'/name
  r=run(dest);path=dest/'raw.json';path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
  if r['exit_code']==0:(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=str(path.relative_to(ROOT)),sha256=sha(path)),indent=2)+'\n')
  print(str(path.relative_to(ROOT)));sys.exit(r['exit_code'])
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/p['raw']).read_text())
