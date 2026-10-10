import sys
sys.dont_write_bytecode=True
import json
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
from model import ROOT,experiment
from oracle import expected
class H(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api':
            try:
                q=parse_qs(u.query,keep_blank_values=True)
                if set(q)!={'source','protocol','port','order'} or any(len(v)!=1 for v in q.values()):raise ValueError('query keys')
                if not q['port'][0].isdigit():raise ValueError('port syntax')
                row=experiment(q['source'][0],q['protocol'][0],int(q['port'][0]),q['order'][0]);row['oracle']=expected(row['input']['packet'],row['input']['order']);data=json.dumps(row,ensure_ascii=False).encode();status=200
            except ValueError as e:data=json.dumps({'status':'rejected','error':str(e)}).encode();status=400
            mime='application/json'
        elif u.path in ('/','/index.html') and not u.query:data=(ROOT/'index.html').read_bytes();status=200;mime='text/html; charset=utf-8'
        else:data=b'not found';status=404;mime='text/plain'
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
s=HTTPServer(('127.0.0.1',0),H);print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close()
