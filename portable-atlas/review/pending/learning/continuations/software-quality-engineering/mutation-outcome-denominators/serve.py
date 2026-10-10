# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from model import evaluate
R=Path(__file__).resolve().parent
REFERENCES={'/reference/requirements-README.md':R.parents[2]/'subjects/requirements-engineering/README.md','/reference/qe-README.md':R.parents[2]/'quality-engineering-atlas/README.md','/reference/risk-README.md':R.parent/'risk-weighted-test-priority/README.md','/reference/quality-README.md':R.parents[2]/'subjects/software-quality-engineering/README.md'}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path=='/evaluate':
   try:config=parse_qs(u.query)['input'][0];r=evaluate(json.loads(config));r['request_json']=config
   except (KeyError,ValueError):r=evaluate(None);r['reason']='JSON input'
   b=json.dumps(r,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  elif u.path in REFERENCES:
   try:b=REFERENCES[u.path].read_bytes()
   except FileNotFoundError:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
  else:super().do_GET()
 def log_message(self,*a):pass
if __name__=='__main__':
 s=ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:'+str(s.server_port)+'/index.html','port':s.server_port}),flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
