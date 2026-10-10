import json
from pathlib import Path
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,parse_qs
from model import experiment
from oracle import counter_expected,latency_expected
ROOT=Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u=urlsplit(self.path)
        if u.path=='/api':
            try:
                q=parse_qs(u.query,strict_parsing=True)
                if set(q)!={'schedule','mode','hold','arrival','deadline'} or any(len(v)!=1 for v in q.values()):raise ValueError('input')
                args={'schedule':q['schedule'][0],'mode':q['mode'][0],**{k:int(q[k][0]) for k in ['hold','arrival','deadline']}}
                x=experiment(**args);x['independentOracle']={'counter':counter_expected(x['selected']['counter']['requestedOrder'],args['mode']),'latency':latency_expected(args['mode'],args['hold'],args['arrival'],args['deadline'])}
                data=json.dumps(x).encode();status=200;mime='application/json'
            except (ValueError,KeyError):data=b'{"error":"input"}';status=400;mime='application/json'
        elif u.path in ['/','/index.html']:data=(ROOT/'index.html').read_bytes();status=200;mime='text/html; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
    def log_message(self,*args):pass
if __name__=='__main__':
    s=HTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:%d'%s.server_port,'title':'ISR・main loop有限スケジュール実験室'}),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
