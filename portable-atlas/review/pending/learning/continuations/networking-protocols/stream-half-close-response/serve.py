import sys
sys.dont_write_bytecode=True
import argparse,json,os
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from fixtures import FIXTURES
R=Path(__file__).resolve().parent
FILES=['CONTRACT.md','fixtures.py','framing.py','oracle.py','observe.py','verify.py','serve.py','app.js','index.html','README.md','COVERAGE.md','skills/stream-half-close/SKILL.md']
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def log_message(self,*a):pass
 def send_json(self,status,data):
  b=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_GET(self):
  from urllib.parse import urlparse,parse_qs
  p=urlparse(self.path);q=parse_qs(p.query)
  if p.path=='/fixtures':self.send_json(200,FIXTURES)
  elif p.path=='/probes':self.send_json(200,json.loads((R/'observations/attempt-01/raw.json').read_text())['probes'])
  elif p.path=='/source':
   n=q.get('file',[''])[0]
   if set(q)!={'file'} or n not in FILES:self.send_json(400,dict(error='source allowlist'));return
   self.send_json(200,dict(file=n,text=(R/n).read_text()))
  elif p.path in ('/','/index.html','/app.js','/source.html'):super().do_GET()
  else:self.send_json(404,dict(error='unknown route'))
 def do_POST(self):
  try:
   if self.path!='/run':raise ValueError('unknown route')
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=2048:raise ValueError('body size')
   def invalid(v):raise ValueError('nonfinite JSON')
   b=json.loads(self.rfile.read(size),parse_constant=invalid)
   if type(b) is not dict or set(b)!={'fixture','mode','width'}:raise ValueError('exact selector')
   if type(b['width']) is not int or b['width'] not in (1,64):raise ValueError('width')
   if b['mode'] not in ('normal','fault'):raise ValueError('mode')
   rows=json.loads((R/'observations/attempt-01/raw.json').read_text())['rows'];row=next((r for r in rows if r['fixture']==b['fixture'] and r['mode']==b['mode'] and r['width']==b['width']),None)
   if row is None:raise ValueError('fixture')
   self.send_json(200,row)
  except (ValueError,TypeError,KeyError) as exc:self.send_json(400,dict(error=str(exc)))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);a=ap.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
 print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port),pid=os.getpid())),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
