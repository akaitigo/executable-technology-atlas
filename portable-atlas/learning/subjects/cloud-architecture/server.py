import http.server,json,urllib.parse
import runner,oracle
MATRIX=runner.matrix();MATRIX_ORACLE=oracle.audit_matrix(MATRIX)
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(runner.ROOT),**kw)
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path!='/api':return super().do_GET()
        case=urllib.parse.parse_qs(u.query).get('case',[''])[0]
        if case not in runner.load('fixture.json')['cases']:self.send_error(400,'unsupported-case');return
        raw=runner.run(case);data=json.dumps({'raw':raw,'oracle':oracle.audit(raw),'matrix':MATRIX,'matrixOracle':MATRIX_ORACLE},ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
if __name__=='__main__':
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(server.server_port)+'/index.html',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();print('owned listener closed',flush=True)
