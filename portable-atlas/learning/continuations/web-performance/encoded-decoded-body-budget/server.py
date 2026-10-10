import http.server,functools,json,hashlib
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from producer import prepare,resolve,decide,empty,Refused,PLAIN,GZIP,utc
ROOT=Path(__file__).resolve().parent
RECEIPTS={}
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
 def payload(self,status,body,encoding=None,id=None,ctype='application/octet-stream'):
  self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
  if encoding:self.send_header('Content-Encoding',encoding)
  if id:
   self.send_header('X-Request-ID',id);self.send_header('X-Body-SHA256',hashlib.sha256(body).hexdigest())
  self.end_headers();written=self.wfile.write(body)
  if id:
   RECEIPTS[id]=dict(request_id=id,http_status=status,body_hex=body.hex(),body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),bytes_written=written,content_encoding=encoding,utc=utc())
   if len(RECEIPTS)>256:RECEIPTS.pop(next(iter(RECEIPTS)))
 def do_GET(self):
  p=urlparse(self.path)
  if p.path=='/api/receipt':
   id=parse_qs(p.query).get('request',[''])[0];receipt=RECEIPTS.get(id)
   self.payload(200 if receipt else 404,json.dumps(receipt).encode(),ctype='application/json');return
  if p.path.startswith('/body/'):
   id=parse_qs(p.query).get('request',[''])[0]
   if len(id)!=32 or any(c not in '0123456789abcdef' for c in id):self.send_error(400);return
   kind=p.path[6:]
   if kind=='plain':self.payload(200,PLAIN,id=id)
   elif kind=='gzip':self.payload(200,GZIP,'gzip',id)
   elif kind=='error':self.payload(500,b'injected HTTP failure',id=id,ctype='text/plain')
   else:self.send_error(404)
   return
  if p.path=='/reference':
   name=parse_qs(p.query).get('file',[''])[0]
   if name not in {'../../../subjects/web-performance/README.md'}:self.send_error(404);return
   self.payload(200,(ROOT/name).read_bytes(),ctype='text/plain; charset=utf-8');return
  super().do_GET()
 def do_POST(self):
  start=utc()
  try:
   n=int(self.headers.get('Content-Length','0'))
   if not 0<n<32768:raise ValueError('request length')
   args=json.loads(self.rfile.read(n))
   if self.path=='/api/prepare':result=prepare(args.get('case'),args.get('input_json'))
   elif self.path=='/api/decide':
    c=resolve(args.get('case'),args.get('input_json'));result=decide(c,args.get('measurement'))
   else:self.send_error(404);return
  except Refused as e:result=empty(args.get('case'),'INPUT_REFUSED',str(e))
  except Exception as e:result=empty(None,'EXECUTION_FAILURE',type(e).__name__+': '+str(e))
  self.payload(200,json.dumps(dict(result=result,attempt=dict(started_utc=start,ended_utc=utc(),http_status=200,executor='actual Python finite validator/budget; Browser provides ResourceTiming')),ensure_ascii=False).encode(),ctype='application/json; charset=utf-8')
if __name__=='__main__':
 with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT))) as s:
  print(json.dumps(dict(url='http://127.0.0.1:%d/index.html'%s.server_port,port=s.server_port)),flush=True)
  try:s.serve_forever()
  except KeyboardInterrupt:pass
