"""QA-only deterministic before-probe failure or held probe. Production HTML unchanged."""
import hashlib,pathlib,sys,threading,http.server
ROOT=pathlib.Path(__file__).resolve().parents[2];QA=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));import server
mode=sys.argv[1];assert mode in ('fault','held');release=threading.Event();once=False
normal_binding=server.binding
normal_worker=(ROOT/'worker.js').read_bytes()
held_worker=normal_worker+b"\nconst actualHandler=self.onmessage;let held=false;self.onmessage=async event=>{if(!held&&event.data.kind==='probe'){held=true;await fetch('/qa-release')}actualHandler(event)};\n"
worker=(QA/'fault-worker.js').read_bytes() if mode=='fault' else held_worker
experiment=(ROOT/'experiment.js').read_bytes() if mode=='fault' else (ROOT/'experiment.js').read_bytes().replace(b'5000',b'30000')
worker_name='fault-worker.js' if mode=='fault' else 'held-worker.js';(QA/worker_name).write_bytes(worker) if mode=='held' else None
(QA/'held-experiment.js').write_bytes(experiment) if mode=='held' else None
def binding():
    values=normal_binding();values['worker.js']=hashlib.sha256(worker).hexdigest();values['experiment.js']=hashlib.sha256(experiment).hexdigest();values[str((QA/'qa-preview.py').relative_to(ROOT))]=hashlib.sha256((QA/'qa-preview.py').read_bytes()).hexdigest();values[str((QA/worker_name).relative_to(ROOT))]=hashlib.sha256(worker).hexdigest();return values
server.binding=binding
class Handler(server.UI):
    def do_GET(self):
        if self.path=='/worker.js':self.reply(worker,'text/javascript');return
        if self.path=='/experiment.js':self.reply(experiment,'text/javascript');return
        if self.path=='/qa-release':
            print('old_probe_held',flush=True)
            if not release.wait(30):self.send_error(504,'QA held timeout');return
            self.reply({'released':True});print('old_probe_released',flush=True);return
        super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=s.serve_forever,daemon=True).start();print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:
    for line in sys.stdin:
        if line.strip()=='release':release.set()
except KeyboardInterrupt:pass
finally:release.set();s.shutdown();s.server_close()
