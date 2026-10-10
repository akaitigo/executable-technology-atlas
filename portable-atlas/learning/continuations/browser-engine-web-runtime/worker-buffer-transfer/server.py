"""Owned loopback preview and explicit fresh record endpoint. No external writes."""
import datetime,hashlib,json,pathlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parent
BOUND=('worker.js','experiment.js','fixtures.json','oracle.json','index.html','server.py')
def binding():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in BOUND}
class UI(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,data,mime='application/json'):
        content=data if isinstance(data,bytes) else json.dumps(data).encode();self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(content)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(content)
    def do_GET(self):
        if self.path=='/binding':self.reply(binding());return
        name=self.path.lstrip('/') or 'index.html'
        if name not in (*BOUND,'check.py','README.md','sources.json'):self.send_error(404);return
        mime='text/html; charset=utf-8' if name.endswith('.html') else 'text/javascript' if name.endswith('.js') else 'application/json' if name.endswith('.json') else 'text/plain; charset=utf-8';self.reply((ROOT/name).read_bytes(),mime)
    def do_POST(self):
        if self.path not in ('/record','/record-failure'):self.send_error(404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<100000:raise ValueError('size')
            value=json.loads(self.rfile.read(size));fixtures=json.loads((ROOT/'fixtures.json').read_text())
            if value['case'] not in fixtures or value['fixture']!=fixtures[value['case']] or value['source_binding']!=binding():raise ValueError('source/fixture')
            failure=value['result']['status']=='EXECUTION_FAILURE'
            if failure!=(self.path=='/record-failure'):raise ValueError('record kind')
            parent=ROOT/'observations'/'failures' if failure else ROOT/'observations';parent.mkdir(exist_ok=True)
            path=parent/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');path.mkdir();filename='failure.json' if failure else 'raw.json';(path/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');self.reply({'saved':str(path.relative_to(ROOT)/filename)})
        except (ValueError,KeyError,TypeError):self.send_error(400,'fixed fixture/current source binding required')
if __name__=='__main__':
    s=ThreadingHTTPServer(('127.0.0.1',0),UI);print('http://127.0.0.1:'+str(s.server_port),flush=True)
    try:s.serve_forever()
    except KeyboardInterrupt:pass
    finally:s.server_close()
