# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,time,datetime,os,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
lock=threading.Lock();log=Path(sys.argv[1]);assert not log.exists()
def emit(event,request_id,**extra):
 row=dict(event=event,request_id=request_id,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),monotonic_ns=time.monotonic_ns(),**extra)
 with lock:
  with log.open('a') as f:f.write(json.dumps(row)+'\n')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  u=urlsplit(self.path);id=parse_qs(u.query).get('id',[''])[0];plans={'/fast':('qe-fast-01',100),'/slow':('qe-timeout-01',2200)}
  if u.path not in plans or plans[u.path][0]!=id:self.send_error(400);return
  delay=plans[u.path][1];emit('ARRIVED',id,delay_ms=delay);time.sleep(delay/1000);body=json.dumps(dict(request_id=id,delay_ms=delay)).encode();emit('GENERATED_200_SEND_ATTEMPT',id,status=200,client_receipt_proven=False)
  try:self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);emit('WRITE_RETURNED',id,delivery_to_client_unknown=True)
  except (BrokenPipeError,ConnectionResetError) as e:emit('SEND_ERROR',id,error_class=type(e).__name__,error_message=str(e),client_receipt_proven=False)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps(dict(port=server.server_port,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())),flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
