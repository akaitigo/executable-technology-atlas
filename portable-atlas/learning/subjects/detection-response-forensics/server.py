import json
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from model import experiment
from oracle import expected
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlsplit(self.path)
        if url.path=='/api':
            try:
                q=parse_qs(url.query,strict_parsing=True)
                if set(q)!={'case','mode','window','threshold'} or any(len(v)!=1 for v in q.values()): raise ValueError('input')
                x=experiment(q['case'][0],q['mode'][0],int(q['window'][0]),int(q['threshold'][0]))
                x['independentOracle']=expected(x['rawInput'],q['mode'][0],int(q['window'][0]),int(q['threshold'][0]))
                data=json.dumps(x).encode();status=200;mime='application/json'
            except (ValueError,KeyError): data=b'{"error":"input"}';status=400;mime='application/json'
        elif url.path in ('/','/index.html'):
            data=(ROOT/'index.html').read_bytes();status=200;mime='text/html; charset=utf-8'
        else: self.send_error(404);return
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def log_message(self,*args):pass
if __name__=='__main__':
    s=HTTPServer(('127.0.0.1',0),Handler)
    print(json.dumps({'url':'http://127.0.0.1:%d'%s.server_port,'title':'架空ログ検知・証拠の実験室'}),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
