import argparse, json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from runner import ROOT, CASES, run
class UI(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        parsed=urlparse(self.path)
        if parsed.path=='/api':
            case=parse_qs(parsed.query).get('case',[''])[0]
            if case not in CASES: self.send_error(400); return
            data=json.dumps(run(case),ensure_ascii=False).encode(); content='application/json'
        elif parsed.path=='/': data=(ROOT/'index.html').read_bytes(); content='text/html; charset=utf-8'
        elif parsed.path in ('/runner.py','/check.py','/README.md','/oracle.json'):
            data=(ROOT/parsed.path[1:]).read_bytes(); content='application/json' if parsed.path=='/oracle.json' else 'text/plain; charset=utf-8'
        else: self.send_error(404); return
        self.send_response(200); self.send_header('Content-Type',content); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--record',action='store_true'); args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',63185),UI)
    try:
        if args.record:
            from check import record,verify
            record(); verify()
        print('preview http://127.0.0.1:63185',flush=True); server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
