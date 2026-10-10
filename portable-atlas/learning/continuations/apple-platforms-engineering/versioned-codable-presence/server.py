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
            try:
                results=self.server.swift.run([case]);v=results.get(case,results);v['owned_compile_tmp_cleaned']=False;v['execution_scope']='preview session own temporary compiler output, cleaned at shutdown'
            except Exception as error:v=dict(case=case,utc=runner.utc(),result=dict(status='EXECUTION_FAILURE',phase='request/process',error=type(error).__name__,message=str(error),partial={}))
            data=json.dumps(v).encode();mime='application/json'
        else:
            name=url.path.lstrip('/') or 'index.html'
            if name not in ['index.html','README.md','main.swift','oracle.py','check.py','fixtures.json','hand-oracle.json','sources.json']:self.send_error(404);return
            data=(ROOT/name).read_bytes();mime='text/html; charset=utf-8' if name.endswith('.html') else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),UI);server.swift=runner.SwiftSession();print('http://127.0.0.1:'+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();print('owned_swift_tmp_cleaned='+str(server.swift.close()),flush=True)
