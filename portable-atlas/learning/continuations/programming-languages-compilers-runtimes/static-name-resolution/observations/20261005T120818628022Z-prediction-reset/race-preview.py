"""QA-only held response; same production HTML/Handler, explicit stdin release."""
import sys,pathlib,threading,http.server
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]))
from server import Handler
release=threading.Event();held=False
class QA(Handler):
    def do_GET(self):
        global held
        if self.path=='/api?case=shadow' and not held:
            held=True;print('old_request_held',flush=True)
            if not release.wait(30):self.send_error(504,'QA release timeout');return
            super().do_GET();print('old_response_written',flush=True)
        else:super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),QA)
threading.Thread(target=server.serve_forever,daemon=True).start();print('http://127.0.0.1:'+str(server.server_port),flush=True)
try:
    for line in sys.stdin:
        if line.strip()=='release':release.set()
except KeyboardInterrupt:pass
finally:release.set();server.shutdown();server.server_close()
