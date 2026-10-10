# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
from http.server import HTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import json
from runner import run
R=Path(__file__).resolve().parent
RELATED={'/subjects/oci-container-engineering/README.md':R.parents[2]/'subjects/oci-container-engineering/README.md'}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path=='/run':
   q=parse_qs(u.query,keep_blank_values=True);data=run(q.get('case',[''])[0],q.get('payload',[''])[0],q.get('marker',[''])[0]);b=json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b);return
  if u.path in RELATED:
   b=RELATED[u.path].read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.end_headers();self.wfile.write(b);return
  super().do_GET()
if __name__=='__main__':
 s=HTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(s.server_port)+'/index.html',flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
