# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,os,datetime
from http.server import HTTPServer,BaseHTTPRequestHandler
from domain import parse,receive
mode=sys.argv[1];records=[]
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
class Handler(BaseHTTPRequestHandler):
 def do_POST(self):
  start=utc();raw=self.rfile.read(int(self.headers['Content-Length']));n=None;payload=None
  try:payload=parse(raw);n=receive(payload,mode)
  except (ValueError,UnicodeError):pass
  status=200 if n is not None else 400;body=json.dumps(dict(fixture_id=payload.get('fixture_id') if type(payload) is dict else None,status='ACCEPTED' if n is not None else 'REFUSED_CONTRACT',accepted_delay_ms=n),separators=(',',':')).encode('utf-8')
  self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);records.append(dict(fixture_id=payload.get('fixture_id') if type(payload) is dict else None,request_hex=raw.hex(),response_hex=body.hex(),http_status=status,accepted_delay_ms=n,started_utc=start,ended_utc=utc()))
 def log_message(self,*a):pass
s=HTTPServer(('127.0.0.1',0),Handler);s.timeout=5
print(json.dumps(dict(pid=os.getpid(),port=s.server_port,receiver=mode)),flush=True)
try:
 for _ in range(2):s.handle_request()
finally:s.server_close()
print(json.dumps(dict(pid=os.getpid(),records=records,closed=True)),flush=True)
