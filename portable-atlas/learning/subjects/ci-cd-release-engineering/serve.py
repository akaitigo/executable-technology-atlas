"""Dedicated loopback UI. Explicit POST appends observations; no external CI."""
import sys
sys.dont_write_bytecode = True
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from urllib.parse import unquote, urlsplit
from runner import ROOT, CASES, canonical, observe, publish


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, mime="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path == "/favicon.ico": return self.reply(204,b"")
        if path.startswith("/api/"): return self.reply(405,canonical({"error":"POST required"}))
        target=(ROOT/unquote(path).lstrip("/")).resolve() if path != "/" else ROOT/"index.html"
        if not target.is_relative_to(ROOT) or not target.is_file():
            return self.reply(404,canonical({"error":"module file not found"}))
        self.reply(200,target.read_bytes(),mimetypes.guess_type(target.name)[0] or "application/octet-stream")

    def do_POST(self):
        if self.path != "/api/run": return self.reply(404,canonical({"error":"unknown endpoint"}))
        try:
            origin=self.headers.get("Origin")
            expected=f"http://127.0.0.1:{self.server.server_port}"
            if origin and origin != expected: raise ValueError("own loopback Origin required")
            if self.headers.get("Content-Type","").split(";")[0] != "application/json": raise ValueError("JSON required")
            size=int(self.headers.get("Content-Length","0"))
            if not 1 <= size <= 4096: raise ValueError("bounded request required")
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict) or set(data) != {"case","rollback"}: raise ValueError("case/rollback only")
            payload=observe(data["case"],data["rollback"],["POST /api/run", "explicit UI calculation"])
            payload["comparisons"]=[observe(c,data["rollback"],["POST /api/run", "comparison"]) for c in CASES]
        except (ValueError, TypeError) as exc:
            return self.reply(400,canonical({"error":str(exc)}))
        try: folder=publish(payload,"ui")
        except OSError as exc:
            return self.reply(500,canonical({"error":str(exc),"old_records_preserved":True}))
        self.reply(200,canonical({"payload":payload,"raw":str((folder/"result.json").relative_to(ROOT)),
                                 "metadata":str((folder/"metadata.json").relative_to(ROOT))}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--port",type=int,default=0); args=parser.parse_args()
    server=ThreadingHTTPServer(("127.0.0.1",args.port),Handler)
    print(f"CI/CD有限教材: http://127.0.0.1:{server.server_port}/",flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
