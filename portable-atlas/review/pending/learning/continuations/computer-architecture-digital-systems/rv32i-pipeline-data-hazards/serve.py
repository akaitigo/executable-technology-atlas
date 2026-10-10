import sys
sys.dont_write_bytecode = True
import argparse, json, os
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from fixtures import FIXTURES
from model import run, MODES
from oracle import sequential
ROOT=Path(__file__).resolve().parent
FILES=('CONTRACT.md','model.py','oracle.py','fixtures.py','verify.py','serve.py','app.js','index.html','README.md','COVERAGE.md','skills/rv32i-hazard/SKILL.md')
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kw): super().__init__(*args,directory=str(ROOT),**kw)
    def log_message(self,*args): pass
    def send_json(self,code,data):
        content=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def do_GET(self):
        from urllib.parse import urlparse,parse_qs
        parsed=urlparse(self.path)
        if parsed.path=='/fixtures':
            self.send_json(200,FIXTURES)
        elif parsed.path=='/source':
            fields=parse_qs(parsed.query);name=fields.get('file',[''])[0]
            if name not in FILES or set(fields)!={'file'}: self.send_json(400,dict(error='source allowlist'));return
            self.send_json(200,dict(file=name,text=(ROOT/name).read_text()))
        elif parsed.path in ('/','/index.html','/app.js','/source.html'):
            super().do_GET()
        else: self.send_json(404,dict(error='unknown route'))
    def do_POST(self):
        try:
            if self.path!='/run': raise ValueError('unknown route')
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=2048: raise ValueError('body size')
            def invalid_constant(v): raise ValueError('nonfinite JSON')
            body=json.loads(self.rfile.read(length),parse_constant=invalid_constant)
            if type(body) is not dict or set(body)!={'fixture','mode'}: raise ValueError('exact fixture and mode fields')
            f=next((v for v in FIXTURES if v['id']==body['fixture']),None)
            if not f: raise ValueError('unknown fixture')
            r=run(f['program'],f['initial'],body['mode']);expected=sequential(f['program'],f['initial'])
            self.send_json(200,dict(fixture=f['id'],oracle=expected,matches_oracle=r['registers']==expected,**r))
        except (ValueError,TypeError,KeyError) as exc: self.send_json(400,dict(error=str(exc)))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--port',type=int,default=0);args=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(json.dumps(dict(url='http://127.0.0.1:'+str(server.server_port),pid=os.getpid())),flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: server.server_close()
