import http.server,json,pathlib,urllib.parse
from runner import run
ROOT=pathlib.Path(__file__).resolve().parent
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        request=urllib.parse.urlsplit(self.path)
        if request.path=='/api':
            try:content=json.dumps(run(urllib.parse.parse_qs(request.query).get('case',[''])[0])).encode();mime='application/json'
            except ValueError:self.send_error(400,'unsupported fixed AST');return
        else:
            name=request.path.lstrip('/') or 'index.html'
            if name not in ('index.html','README.md','language.py','check.py','fixtures.json','oracle.json'):
                self.send_error(404);return
            content=(ROOT/name).read_bytes();mime='text/html; charset=utf-8' if name=='index.html' else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(content)
    def log_message(self,*args):pass
if __name__=='__main__':
    server=http.server.HTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()
