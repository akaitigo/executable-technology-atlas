import sys
sys.dont_write_bytecode=True
import json
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from model import ROOT,experiment
from oracle import expected
class H(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urlsplit(self.path)
        if u.path in ('/','/index.html') and not u.query:
            data=(ROOT/'index.html').read_bytes();code=200;kind='text/html; charset=utf-8'
        elif u.path=='/api':
            try:
                q=parse_qs(u.query,keep_blank_values=True,strict_parsing=True)
                if set(q)!={'case','selection','launch'} or any(len(v)!=1 for v in q.values()):raise ValueError('exactly one of each query key required')
                args=[q[k][0] for k in ('case','selection','launch')];d=experiment(*args);d['expected']=expected(*args);data=json.dumps(d,ensure_ascii=False).encode();code=200
            except (ValueError,KeyError) as e:data=json.dumps({'status':'rejected','error':str(e)}).encode();code=400
            kind='application/json; charset=utf-8'
        else:data=b'not found';code=404;kind='text/plain'
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
s=HTTPServer(('127.0.0.1',0),H);print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close()
