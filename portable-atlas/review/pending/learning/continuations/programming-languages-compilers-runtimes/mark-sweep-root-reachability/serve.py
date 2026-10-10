import sys
sys.dont_write_bytecode=True
import argparse,json,os
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from fixtures import FIXTURES
from lesson import run
R=Path(__file__).resolve().parent
FILES=('CONTRACT.md','collector.py','oracle.py','lesson.py','fixtures.py','verify.py','serve.py','app.js','index.html','README.md','COVERAGE.md','skills/mark-sweep-roots/SKILL.md')
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kw):super().__init__(*args,directory=str(R),**kw)
    def log_message(self,*args):pass
    def send_json(self,status,data):
        body=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        from urllib.parse import urlparse,parse_qs
        p=urlparse(self.path)
        if p.path=='/fixtures':self.send_json(200,FIXTURES)
        elif p.path=='/source':
            q=parse_qs(p.query);name=q.get('file',[''])[0]
            if name not in FILES or set(q)!={'file'}:self.send_json(400,dict(error='source allowlist'));return
            self.send_json(200,dict(file=name,text=(R/name).read_text()))
        elif p.path in ('/','/index.html','/app.js','/source.html'):super().do_GET()
        else:self.send_json(404,dict(error='unknown route'))
    def do_POST(self):
        try:
            if self.path!='/run':raise ValueError('unknown route')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=2048:raise ValueError('body size')
            def invalid(v):raise ValueError('nonfinite JSON')
            b=json.loads(self.rfile.read(size),parse_constant=invalid)
            if type(b) is not dict or set(b)!={'fixture','mode'}:raise ValueError('exact fixture/mode required')
            f=next((v for v in FIXTURES if v['id']==b['fixture']),None)
            if f is None:raise ValueError('unknown fixture')
            self.send_json(200,run(f,b['mode']))
        except (ValueError,TypeError,KeyError) as exc:self.send_json(400,dict(error=str(exc)))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);a=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port),pid=os.getpid())),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:server.server_close()
