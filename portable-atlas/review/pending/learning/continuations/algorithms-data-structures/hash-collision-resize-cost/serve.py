# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from model import evaluate
R=Path(__file__).resolve().parent
REFERENCES={'/reference/LEARNING_PATH.md':R.parents[2]/'subjects/algorithms-data-structures/LEARNING_PATH.md','/reference/subject-README.md':R.parents[2]/'subjects/algorithms-data-structures/README.md'}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(R),**kw)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path=='/evaluate':
   try:
    config=parse_qs(u.query)['input'][0];c=json.loads(config);result=evaluate(c);result['request_json']=config
    if result['status']=='EXECUTED':result['peer']=evaluate(dict(c,policy='doubling' if c['policy']=='fixed' else 'fixed'))
   except (KeyError,ValueError):result=dict(status='REFUSED_INPUT',trace=[],oracle=[],differences=[])
   body=json.dumps(result,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  elif u.path in REFERENCES:
   body=REFERENCES[u.path].read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
  else:super().do_GET()
 def log_message(self,*a):pass
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port)+'/index.html',port=server.server_port)),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
