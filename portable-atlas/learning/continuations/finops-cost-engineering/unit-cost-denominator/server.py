import datetime,http.server,json,pathlib,urllib.parse
import runner
ROOT=pathlib.Path(__file__).resolve().parent
class UI(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        url=urllib.parse.urlparse(self.path)
        if url.path=='/api':
            case=urllib.parse.parse_qs(url.query).get('case',[''])[0]
            if case not in json.loads((ROOT/'fixtures.json').read_text()):self.send_error(404);return
            try:v=runner.run(case)
            except Exception as error:v=dict(case=case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),result=dict(status='EXECUTION_FAILURE',phase='calculate',error=type(error).__name__,message=str(error),partial={}))
            data=json.dumps(v).encode();mime='application/json'
        else:
            name=url.path.lstrip('/') or 'index.html'
            if name not in ['index.html','README.md','calculate.py','oracle.py','check.py','fixtures.json','hand-oracle.json','sources.json']:self.send_error(404);return
            data=(ROOT/name).read_bytes();mime='text/html; charset=utf-8' if name.endswith('.html') else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),UI);print('http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
