# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from runner import run
R=Path(__file__).resolve().parent
ORIGINAL=R.parents[2]/'subjects/service-networking-traffic-management/README.md'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def do_GET(self):
  u=urlsplit(self.path)
  if u.path=='/run':
   try:
    x=json.loads(parse_qs(u.query)['input'][0]);assert type(x) is list and len(x)==7;r=run(*x)
   except (ValueError,KeyError,AssertionError,TypeError):r=dict(status='REFUSED_INPUT',error='seven JSON fields required')
   blob=json.dumps(r,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(blob)));self.end_headers();self.wfile.write(blob)
  elif u.path=='/subjects/service-networking-traffic-management/README.md':
   b=ORIGINAL.read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:super().do_GET()
 def translate_path(self,path):
  p=(R/unquote(urlsplit(path).path).lstrip('/')).resolve()
  return str(p) if p==R or R in p.parents else str(R/'__outside_refused__')
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:%s/index.html'%server.server_port,flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
