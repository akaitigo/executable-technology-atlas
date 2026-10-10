import http.server,json,pathlib,urllib.parse
import runner
ROOT=pathlib.Path(__file__).resolve().parent
class UI(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path=='/api':
            q=urllib.parse.parse_qs(u.query)
            try:v=runner.run(q['case'][0])
            except (KeyError,ValueError):self.send_error(400);return
            except Exception as error:v=dict(case=q.get('case',[''])[0],utc=runner.utc(),result=dict(status='EXECUTION_FAILURE',phase='owned file setup/read/resolve',error=type(error).__name__,errno=getattr(error,'errno',None)))
            data=json.dumps(v).encode();mime='application/json'
        else:
            name=u.path.lstrip('/') or 'index.html'
            if name not in ['index.html','README.md','calculate.py','oracle.py','check.py','fixtures.json','hand-oracle.json','sources.json']:self.send_error(404);return
            data=(ROOT/name).read_bytes();mime='text/html; charset=utf-8' if name.endswith('.html') else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    s=http.server.ThreadingHTTPServer(('127.0.0.1',0),UI);print('http://127.0.0.1:'+str(s.server_port),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close();print('owned_server_closed=True',flush=True)
