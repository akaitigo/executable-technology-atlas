"""Own module only; dynamic loopback preview, no external services."""
import sys
sys.dont_write_bytecode=True
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import runner


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlparse(self.path).path
        allowed={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}
        if path not in allowed: self.send_error(404); return
        target=runner.ROOT/allowed[path]
        self.send_response(200); self.send_header("Content-Type",{".html":"text/html; charset=utf-8",".js":"text/javascript; charset=utf-8",".css":"text/css; charset=utf-8"}[target.suffix]); self.end_headers(); self.wfile.write(target.read_bytes())

    def do_POST(self):
        if self.path!="/run": self.send_error(404); return
        size=int(self.headers.get("Content-Length","0"))
        if not 0<size<=1024: self.send_error(400); return
        try:
            request=json.loads(self.rfile.read(size))
            if set(request)!={"case","record"} or type(request["record"]) is not bool: raise ValueError("finite input required")
            report=runner.observe(request["case"],["POST","/run",request["case"]])
            if not report["oracle"]["all_match"]: raise ValueError("oracle mismatch")
            record=runner.publish(report,"ui-"+request["case"]).relative_to(runner.ROOT).as_posix() if request["record"] else None
            response={"report":report,"record_path":record}
        except (ValueError,KeyError): self.send_error(400); return
        self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.end_headers()
        self.wfile.write(runner.canonical(response))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--port",type=int,default=0); args=parser.parse_args()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"http://127.0.0.1:{server.server_port}",flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
