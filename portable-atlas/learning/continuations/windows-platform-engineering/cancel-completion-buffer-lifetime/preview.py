import http.server,pathlib,sys,json,time,urllib.parse
sys.dont_write_bytecode=True
from execute import execute
R=pathlib.Path(__file__).resolve().parent
REF='/subjects/windows-platform-engineering/README.md'
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def do_GET(self):
  path=urllib.parse.urlsplit(self.path).path
  if path==REF:
   b=(R.parents[2]/'subjects/windows-platform-engineering/README.md').read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  if not (R/path.lstrip('/')).resolve().is_relative_to(R):self.send_error(403);return
  return super().do_GET()
 def do_POST(self):
  u=urllib.parse.urlsplit(self.path)
  if u.path!='/execute':self.send_error(404);return
  length=int(self.headers.get('Content-Length','0'))
  if not 0<length<=30000:self.send_error(413);return
  raw=self.rfile.read(length).decode('utf8');c=execute(raw)
  if urllib.parse.parse_qs(u.query).get('qaDelay')==['2000']:time.sleep(2)
  b=json.dumps(c).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(server.server_port)+'/',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
