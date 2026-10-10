"""QA-only: synthetic constructor injection on second run, startup fault, held probe."""
import pathlib,sys,hashlib,threading,http.server
ROOT=pathlib.Path(__file__).resolve().parents[2];QA=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT));import server
mode=sys.argv[1];assert mode in ('constructor','fault','held');release=threading.Event();original_binding=server.binding
html=(ROOT/'index.html').read_bytes();worker=(ROOT/'worker.js').read_bytes();experiment=(ROOT/'experiment.js').read_bytes()
if mode=='constructor':
    injection=b"<script>const OriginalWorker=window.Worker;let qaWorkerCalls=0;window.Worker=new Proxy(OriginalWorker,{construct(target,args){if(++qaWorkerCalls===2)throw new DOMException('QA_WORKER_CONSTRUCTOR_FAULT','SecurityError');return Reflect.construct(target,args)}});</script>"
    html=html.replace(b'<script type="module">',injection+b'<script type="module">')
if mode=='fault':worker=(QA/'fault-worker.js').read_bytes()
if mode=='held':
    worker+=b"\nconst actualHandler=self.onmessage;let held=false;self.onmessage=async event=>{if(!held&&event.data.kind==='probe'){held=true;await fetch('/qa-release')}actualHandler(event);if(event.data.kind==='probe'&&event.data.id.endsWith(':after'))fetch('/qa-after-probe')};\n"
    experiment=experiment.replace(b'5000',b'30000')
for name,data in [('served-'+mode+'.html',html),('served-'+mode+'-worker.js',worker),('served-'+mode+'-experiment.js',experiment)]:(QA/name).write_bytes(data)
def binding():
    b=original_binding();b.update({'index.html':hashlib.sha256(html).hexdigest(),'worker.js':hashlib.sha256(worker).hexdigest(),'experiment.js':hashlib.sha256(experiment).hexdigest()});b[str((QA/'qa-preview.py').relative_to(ROOT))]=hashlib.sha256((QA/'qa-preview.py').read_bytes()).hexdigest();return b
server.binding=binding
class Handler(server.UI):
    def do_GET(self):
        if self.path=='/':self.reply(html,'text/html; charset=utf-8');return
        if self.path=='/worker.js':self.reply(worker,'text/javascript');return
        if self.path=='/experiment.js':self.reply(experiment,'text/javascript');return
        if self.path=='/qa-release':
            print('old_probe_held',flush=True)
            if not release.wait(30):self.send_error(504);return
            self.reply({'released':True});print('old_probe_released',flush=True);return
        if self.path=='/qa-after-probe':self.reply({'observed':True});print('old_worker_after_probe_completed',flush=True);return
        super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=s.serve_forever,daemon=True).start();print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:
    for line in sys.stdin:
        if line.strip()=='release':release.set()
except KeyboardInterrupt:pass
finally:release.set();s.shutdown();s.server_close()
