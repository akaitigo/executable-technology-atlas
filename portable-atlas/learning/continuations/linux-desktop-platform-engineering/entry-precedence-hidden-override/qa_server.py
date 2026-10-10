import http.server,json,sys,threading
import server
import failure_probe
MODE=sys.argv[1];count=0;held=threading.Event();released=threading.Event()
class QA(server.UI):
    def do_GET(self):
        global count
        if self.path=='/release':
            released.set();data=b'released'
            self.send_response(200);self.end_headers();self.wfile.write(data);return
        if self.path.startswith('/api?'):
            count+=1;n=count
            if MODE=='held' and n==1:
                held.set();print('old_request_held=True',flush=True);released.wait(45)
                super().do_GET();print('old_response_written=True',flush=True);return
            if MODE=='failure' and n in [2,4]:
                if n==4:self.send_error(503,'synthetic QA transport failure');print('synthetic_http_503=True',flush=True);return
                v=failure_probe.probe();data=json.dumps(v).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(data);print('actual_owned_decode_failure=True; owned_tmp_cleaned=True',flush=True);return
        super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),QA);print('http://127.0.0.1:'+str(s.server_port),flush=True)
try:s.serve_forever()
except KeyboardInterrupt:pass
finally:s.server_close();print('owned_server_closed=True',flush=True)
