import datetime,hashlib,http.server,json,pathlib,sys,urllib.parse
import runner
ROOT=pathlib.Path(__file__).resolve().parent
class UI(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        if self.path!='/record':self.send_error(404);return
        length=int(self.headers.get('Content-Length','0'))
        if length>100000:self.send_error(413);return
        data=self.rfile.read(length)
        if self.server.record_dir is not None:
            v=json.loads(data);v['html_sha256']=hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest();self.server.record_count+=1
            (self.server.record_dir/('browser-'+str(self.server.record_count).zfill(3)+'.json')).write_text(json.dumps(v,indent=2)+'\n')
        self.send_response(204);self.end_headers()
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path=='/api':
            q=urllib.parse.parse_qs(u.query)
            try:v=runner.run(q['case'][0],int(q['point'][0]))
            except (KeyError,ValueError):self.send_error(400);return
            data=json.dumps(v).encode();mime='application/json'
        else:
            name=u.path.lstrip('/') or 'index.html'
            if name not in ['index.html','README.md','calculate.py','oracle.py','check.py','fixtures.json','hand-oracle.json','sources.json']:self.send_error(404);return
            data=(ROOT/name).read_bytes();mime='text/html; charset=utf-8' if name.endswith('.html') else 'text/plain; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
def configure(s,record=False):
    s.record_dir=None;s.record_count=0
    if record:
        s.record_dir=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');s.record_dir.mkdir(parents=True);print('explicit_preview_record='+str(s.record_dir.relative_to(ROOT)),flush=True)
if __name__=='__main__':
    if sys.argv[1:] not in [[],['--record-preview']]:raise SystemExit(2)
    s=http.server.ThreadingHTTPServer(('127.0.0.1',0),UI);configure(s,sys.argv[1:]==['--record-preview']);print('http://127.0.0.1:'+str(s.server_port),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close();print('owned_server_closed=True',flush=True)
