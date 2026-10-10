"""QA only: hold one real API response until explicit stdin release."""
import pathlib,sys,threading,http.server
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from server import UI
release=threading.Event();held=False
class QA(UI):
    def do_GET(self):
        global held
        if self.path=='/api?case=epsilon-0.1' and not held:
            held=True;print('old_request_held',flush=True)
            if not release.wait(30):self.send_error(504,'QA release timeout');return
            super().do_GET();print('old_response_written',flush=True)
        else:super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),QA);threading.Thread(target=s.serve_forever,daemon=True).start();print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:
    for line in sys.stdin:
        if line.strip()=='release':release.set()
except KeyboardInterrupt:pass
finally:release.set();s.shutdown();s.server_close()
