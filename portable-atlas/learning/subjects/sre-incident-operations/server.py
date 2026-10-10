import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from runner import ROOT,run,fixture
from oracle import audit
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kw):super().__init__(*args,directory=str(ROOT),**kw)
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=='/api':
            case=parse_qs(p.query).get('case',['unequal-volume'])[0]
            if case not in fixture()['cases']:self.send_error(400,'unsupported-case');return
            raw=run(case);body=json.dumps({'raw':raw,'oracle':audit(raw)},ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        super().do_GET()
if __name__=='__main__':
    with ThreadingHTTPServer(('127.0.0.1',0),Handler) as s:
        print(f'http://127.0.0.1:{s.server_port}/index.html',flush=True)
        try:s.serve_forever()
        except KeyboardInterrupt:print('owned listener closed',flush=True)
