import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from runner import ROOT,run
class UI(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        if self.path=='/api':
            value,_=run(False);data=json.dumps(value).encode();content='application/json'
        elif self.path=='/':data=(ROOT/'index.html').read_bytes();content='text/html; charset=utf-8'
        elif self.path in ('/runner.py','/check.py','/oracle.json','/README.md'):
            data=(ROOT/self.path[1:]).read_bytes();content='application/json' if self.path=='/oracle.json' else 'text/plain; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),UI)
    print('preview http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
