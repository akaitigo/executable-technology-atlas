import http.server,json,urllib.parse
from runner import ROOT,run
class UI(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        q=urllib.parse.urlsplit(self.path)
        if q.path=='/api':
            try:data=json.dumps(run(urllib.parse.parse_qs(q.query).get('case',[''])[0])).encode();mime='application/json'
            except ValueError:self.send_error(400);return
        else:
            n=q.path.lstrip('/') or 'index.html'
            if n not in ('index.html','README.md','pipeline.py','check.py','corpus.json','evidence.json','fixtures.json','hand-oracle.json'):self.send_error(404);return
            data=(ROOT/n).read_bytes();mime='text/html; charset=utf-8' if n=='index.html' else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    s=http.server.ThreadingHTTPServer(('127.0.0.1',0),UI);print('http://127.0.0.1:'+str(s.server_port),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
