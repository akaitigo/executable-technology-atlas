import functools,http.server,json,datetime
from urllib.parse import urlparse,parse_qs
from pathlib import Path
from producer import run
ROOT=Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
 def do_GET(self):
  request=urlparse(self.path)
  if request.path!='/reference':return super().do_GET()
  name=parse_qs(request.query).get('file',[''])[0];allowed={'../../../subjects/embedded-firmware-rtos/README.md','../../performance-capacity-engineering/two-server-bounded-queue/README.md'}
  if name not in allowed:self.send_error(404);return
  payload=(ROOT/name).read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
 def do_POST(self):
  if self.path!='/api':self.send_error(404);return
  start=utc();delay=0
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<32768:raise ValueError('request length')
   args=json.loads(self.rfile.read(n));r=run(args.get('case'),args.get('events_json'))
  except Exception as e:r=dict(status='EXECUTION_FAILURE',reason=str(e),safe=None,naive=None)
  out=dict(result=r,attempt=dict(executor='same Python producer.run in HTTP handler; no child process',started_utc=start,ended_utc=utc(),delay_ms=delay,http_status=200));payload=json.dumps(out,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
if __name__=='__main__':
 with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT))) as s:
  print(json.dumps({'url':'http://127.0.0.1:%d/index.html'%s.server_port}),flush=True)
  try:s.serve_forever()
  except KeyboardInterrupt:pass
