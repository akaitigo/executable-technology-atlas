import functools,http.server,json
from urllib.parse import urlparse,parse_qs
from pathlib import Path
from producer import run
ROOT=Path(__file__).resolve().parent
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
 def do_GET(self):
  request=urlparse(self.path)
  if request.path!='/reference':return super().do_GET()
  name=parse_qs(request.query).get('file',[''])[0]
  allowed={'../../../subjects/requirements-engineering/README.md','../../../subjects/software-engineering-foundations/README.md'}
  if name not in allowed:self.send_error(404);return
  payload=(ROOT/name).read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
 def do_POST(self):
  if self.path!='/api':self.send_error(404);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<4096:raise ValueError('request length')
   args=json.loads(self.rfile.read(n));out=run(args.get('case'),args.get('start') or None)
  except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=str(e),reachable=[],missing_reverse=[],missing_forward=[],trace=[],input=None)
  payload=json.dumps(out,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
if __name__=='__main__':
 with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT))) as s:
  print(json.dumps({'url':'http://127.0.0.1:%d/index.html'%s.server_port}),flush=True)
  try:s.serve_forever()
  except KeyboardInterrupt:pass
