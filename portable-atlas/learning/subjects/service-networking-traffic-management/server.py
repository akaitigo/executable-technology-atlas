import sys
sys.dont_write_bytecode=True
import json
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from model import ROOT,experiment
from oracle import expected,bad_expected
class H(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api':
            try:
                q=parse_qs(u.query,keep_blank_values=True);names=('threshold','cooldown','retries','deadline','budget','recovery')
                if set(q)!=set(names) or any(len(v)!=1 for v in q.values()):raise ValueError('query keys')
                if any(not q[k][0].isdigit() for k in names[:-1]):raise ValueError('integer syntax')
                args=tuple(int(q[k][0]) for k in names[:-1])+(q['recovery'][0],);row=experiment(*args);row['oracle']=expected(*args);row['badOracle']=bad_expected(args[-1]);data=json.dumps(row,ensure_ascii=False).encode();status=200
            except ValueError as e:data=json.dumps({'status':'rejected','error':str(e)}).encode();status=400
            mime='application/json'
        elif u.path in ('/','/index.html') and not u.query:data=(ROOT/'index.html').read_bytes();status=200;mime='text/html; charset=utf-8'
        else:data=b'not found';status=404;mime='text/plain'
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
s=HTTPServer(('127.0.0.1',0),H);print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close()
