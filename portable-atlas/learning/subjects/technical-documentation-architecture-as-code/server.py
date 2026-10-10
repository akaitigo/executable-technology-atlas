import sys
sys.dont_write_bytecode=True
import json
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from model import ROOT,experiment,SCENARIOS
from oracle import verify
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api':
            try:
                q=parse_qs(u.query,keep_blank_values=True)
                if set(q)!={'scenario'} or len(q['scenario'])!=1: raise ValueError('query')
                row=experiment(q['scenario'][0]);row['oracle']=verify(row)
                data=json.dumps(row,ensure_ascii=False).encode();status=200;mime='application/json'
            except (ValueError,AssertionError) as e: data=json.dumps({'error':str(e)}).encode();status=400;mime='application/json'
        elif u.path in ('/','/index.html') and not u.query:
            data=(ROOT/'index.html').read_bytes();status=200;mime='text/html; charset=utf-8'
        else: data=b'not found';status=404;mime='text/plain'
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
s=HTTPServer(('127.0.0.1',0),Handler)
print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close()
