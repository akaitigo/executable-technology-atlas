import http.server,json,functools
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from execute import execute
P=Path(__file__).resolve().parent;CASES=json.loads((P/'fixture.json').read_text());RECEIPTS={}
REFS={'../../embedded-firmware-rtos/isr-offload-bounded-queue/README.md':P.parent/'isr-offload-bounded-queue/README.md','../../../subjects/embedded-firmware-rtos/README.md':P.parents[2]/'subjects/embedded-firmware-rtos/README.md'}
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,status,data):
  b=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path=='/api/receipt':
   id=parse_qs(u.query).get('request',[''])[0];self.send(200 if id in RECEIPTS else 404,RECEIPTS.get(id));return
  if u.path=='/reference':
   name=parse_qs(u.query).get('file',[''])[0]
   if name not in REFS:self.send_error(404);return
   b=REFS[name].read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.end_headers();self.wfile.write(b);return
  super().do_GET()
 def do_POST(self):
  if self.path=='/api/unavailable':self.send(503,dict(status='INJECTED_HTTP_503'));return
  if self.path!='/api/run':self.send_error(404);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<=30000:self.send_error(413);return
   args=json.loads(self.rfile.read(n));c=next(c for c in CASES if c['id']==args.get('case'));text=args.get('input_json')
   if type(text) is not str:self.send_error(400);return
   raw=execute(text if text.strip() else json.dumps(c['input']),c.get('inject_failure',False));RECEIPTS[raw['request_id']]=raw
   if len(RECEIPTS)>256:RECEIPTS.pop(next(iter(RECEIPTS)))
   self.send(200,raw)
  except (ValueError,TypeError,StopIteration):self.send_error(400)
if __name__=='__main__':
 with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(P))) as server:
  print(json.dumps(dict(url='http://127.0.0.1:%d/index.html'%server.server_port,pid=__import__('os').getpid())),flush=True)
  try:server.serve_forever()
  except KeyboardInterrupt:pass
