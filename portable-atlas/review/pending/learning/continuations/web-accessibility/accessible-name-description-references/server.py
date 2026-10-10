from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import json
P=Path(__file__).resolve().parent
ALLOWED=['README.md','EXPECTATIONS.md','SOURCES.md','COVERAGE.md','ui.js','fixture.json','oracle.json','evidence/capability.json','evidence/observations.json','evidence/verification.json','../../../subjects/web-accessibility/LEARNING_PATH.md','../../../quality-engineering-atlas/README.md']
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(P),**kw)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path=='/failure':self.send_error(503,'synthetic transport failure');return
  if u.path=='/document':
   n=parse_qs(u.query).get('file',[''])[0]
   if n not in ALLOWED:self.send_error(403);return
   f=P/n
   if not f.is_file():self.send_error(404);return
   b=f.read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
  super().do_GET()
 def log_message(self,*a):pass
if __name__=='__main__':
 s=ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps(dict(url='http://127.0.0.1:'+str(s.server_port),port=s.server_port)),flush=True);s.serve_forever()
