import argparse,datetime,json,sys,time,uuid
from http.server import HTTPServer,SimpleHTTPRequestHandler
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run
parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true',required=True);parser.parse_args()
rid=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-preview');folder=ROOT/'observations'/rid;folder.mkdir(parents=True,exist_ok=False);(folder/'requests').mkdir()
def write(n,x):
 with (folder/n).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
binding={n:digest(ROOT/n) for n in SOURCES};write('server-start.json',{'bind':'127.0.0.1:0','engine':'Native SQLite WAL two connections','source_digests':binding,'delay_ms':600,'owned_tmp_created':False})
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def do_POST(self):
  if self.path!='/measure':self.send_error(404);return
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=16384:self.send_error(413);return
   x=json.loads(self.rfile.read(size));text=x['input_json'];revision=x['revision']
   if type(text) is not str or len(text.encode('utf8'))>4096 or type(revision) is not int:self.send_error(400);return
   result=run(text);req=uuid.uuid4().hex;raw={'request_id':req,'revision':revision,'input_json':text,'run':result,'source_digests':binding,'engine':'Native SQLite WAL two connections'};write('requests/'+req+'.json',raw)
   response=dict(raw,raw_href=str((folder/'requests'/(req+'.json')).relative_to(ROOT)))
   time.sleep(.6) # Explicit preview latency solely to exercise stale-response suppression.
   body=json.dumps(response,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  except (ValueError,KeyError,TypeError):self.send_error(400)
  except (BrokenPipeError,ConnectionResetError):pass
failure=0
try:
 server=HTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:'+str(server.server_port)+'/index.html','preview_id':rid}),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
except PermissionError as e:write('bind-failure.json',{'class':type(e).__name__,'errno':e.errno});print('PermissionError socket.bind',file=sys.stderr);failure=1
finally:write('server-stop.json',{'server_closed':True,'owned_tmp_created':False,'owned_tmp_remaining':False})
sys.exit(failure)
