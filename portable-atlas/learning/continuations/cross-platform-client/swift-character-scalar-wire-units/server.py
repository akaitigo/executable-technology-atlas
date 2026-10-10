import argparse,datetime,json,sys,time,uuid
from http.server import HTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
sys.dont_write_bytecode=True
from runtime import Runtime,ROOT
from runner import SOURCES,digest
parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true',required=True);args=parser.parse_args()
id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-preview');folder=ROOT/'observations'/id;folder.mkdir(parents=True,exist_ok=False);(folder/'requests').mkdir()
def write(n,x):
 with (folder/n).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
failure=0
with Runtime() as rt:
 source_digests={n:digest(ROOT/n) for n in SOURCES};write('server-start.json',{'compile':rt.compile,'identity':rt.identity,'source_digests':source_digests,'delay_ms':600,'bind':'127.0.0.1:0'})
 class Handler(SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
  def do_POST(self):
   if self.path!='/measure':self.send_error(404);return
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=4096:self.send_error(413);return
   request=json.loads(self.rfile.read(size));text=request.get('input_json');revision=request.get('revision')
   if type(text) is not str or len(text.encode('utf8'))>1024:self.send_error(400);return
   run=rt.run(text);rid=uuid.uuid4().hex;raw={'request_id':rid,'revision':revision,'input_json':text,'run':run,'compile':rt.compile,'identity':rt.identity,'source_digests':source_digests,'engine':'Swift CLI'};write('requests/'+rid+'.json',raw)
   response={**raw,'raw_href':str((folder/'requests'/(rid+'.json')).relative_to(ROOT))}
   time.sleep(.6) # Explicit preview latency for stale-response QA; result remains real Swift.
   body=json.dumps(response,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 try:
  server=HTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:'+str(server.server_port)+'/index.html','preview_id':id}),flush=True)
  try:server.serve_forever()
  except KeyboardInterrupt:pass
  finally:server.server_close()
 except PermissionError as error:write('bind-failure.json',{'class':type(error).__name__,'errno':error.errno});print('PermissionError errno1 socket.bind',file=sys.stderr);failure=1
 finally:write('server-stop.json',{'server_closed':True,'runtime_cleanup_pending':True})
write('owned-tmp-cleanup.json',{'owned_tmp_cleaned':rt.cleaned})
sys.exit(failure)
