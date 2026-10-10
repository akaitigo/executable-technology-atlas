"""Synthetic QA request failure on second same-case call; production inputs unchanged."""
import pathlib,sys,http.server
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from server import UI
calls=0
class QA(UI):
    def do_GET(self):
        global calls
        if self.path=='/api?case=epsilon-0.1':
            calls+=1
            if calls==2:self.send_error(503,'QA_SECOND_REQUEST_FAULT');return
        super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),QA);print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close()
