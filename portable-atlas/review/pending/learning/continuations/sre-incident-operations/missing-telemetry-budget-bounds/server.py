import json,argparse
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from execute import execute
P=Path(__file__).resolve().parent;FIX=json.loads((P/'fixture.json').read_text());receipts={}
REFERENCES={'../multiwindow-burn-alert/README.md':P.parent/'multiwindow-burn-alert/README.md','../../observability-engineering/collector-missing-late-quantiles/README.md':P.parents[1]/'observability-engineering/collector-missing-late-quantiles/README.md','../../../subjects/sre-incident-operations/README.md':P.parents[2]/'subjects/sre-incident-operations/README.md'}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(P),**kw)
 def log_message(self,*a):pass
 def send(self,value,code=200):
  b=json.dumps(value).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path);q=parse_qs(u.query)
  if u.path=='/api/receipt':self.send(receipts.get(q.get('request',[''])[0],dict(status='missing')));return
  if u.path=='/reference':
   n=q.get('file',[''])[0]
   if n not in REFERENCES:self.send(dict(status='unsupported'),404);return
   b=REFERENCES[n].read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  super().do_GET()
 def do_POST(self):
  if self.path=='/api/unavailable':self.send(dict(status='INJECTED_HTTP_503'),503);return
  if self.path!='/api/run':self.send(dict(status='unsupported'),404);return
  try:
   q=json.loads(self.rfile.read(int(self.headers['Content-Length'])));c=next(c for c in FIX if c['id']==q['case']);text=q['input_json'] or json.dumps(c['input']);raw=execute(text,c.get('inject_failure',False));receipts[raw['request_id']]=raw
   if len(receipts)>128:receipts.pop(next(iter(receipts)))
   self.send(raw)
  except Exception as e:self.send(dict(status='SERVER_ERROR',reason=type(e).__name__),500)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--port',type=int,default=0);args=a.parse_args();s=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);print('http://127.0.0.1:'+str(s.server_port)+'/index.html',flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:s.server_close()
