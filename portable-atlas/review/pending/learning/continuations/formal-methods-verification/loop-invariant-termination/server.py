"""Own loopback server. Child execution receipts kept only in bounded RAM."""
from datetime import datetime, timezone
import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent
RECEIPTS=[]
LOCK=threading.Lock()
DELAY_MS=0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, content, mime="application/json", status=200):
        if not isinstance(content,bytes):
            content=json.dumps(content,ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type",mime)
        self.send_header("Content-Length",str(len(content))); self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/receipts":
            with LOCK: self.send(list(RECEIPTS))
            return
        if path=="/api/cases":
            cases=json.loads((ROOT/"expected.json").read_text())
            self.send([{**case,"stdin":json.dumps(case["input"],ensure_ascii=False,indent=2)}
                       for case in cases]); return
        name="index.html" if path=="/" else path.lstrip("/")
        allowed={"index.html","app.js","style.css","README.md","COVERAGE.md","Skill.md",
                 "contract.json","oracle-contract.md","oracle-contract-v2.md","hand-table.json","expected.json",
                 "calculate.py","checker.py","runner.py","server.py","route.py"}
        if name not in allowed:
            self.send({"error":"not found"},status=404); return
        mime="text/html; charset=utf-8" if name.endswith(".html") else (
             "text/javascript; charset=utf-8" if name.endswith(".js") else
             "text/css; charset=utf-8" if name.endswith(".css") else "text/plain; charset=utf-8")
        if name not in {"index.html","app.js","style.css"}:
            source=html.escape((ROOT/name).read_text())
            page='<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+html.escape(name)+'</title><main><h1>'+html.escape(name)+'</h1><a href="/">教材に戻る</a><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+source+'</pre></main></html>'
            self.send(page.encode(),"text/html; charset=utf-8")
            return
        self.send((ROOT/name).read_bytes(),mime)

    def do_POST(self):
        if self.path!="/api/calculate":
            self.send({"error":"not found"},status=404); return
        length=int(self.headers.get("Content-Length","0"))
        if length>8192:
            self.send({"error":"too large"},status=413); return
        stdin=self.rfile.read(length).decode("utf-8")
        time.sleep(DELAY_MS/1000)
        sha=hashlib.sha256((ROOT/"calculate.py").read_bytes()).hexdigest()
        p=subprocess.run([sys.executable,"-B",str(ROOT/"calculate.py")],input=stdin,
                         text=True,capture_output=True,timeout=4)
        receipt={"stdin":stdin,"stdout":p.stdout,"stderr":p.stderr,
                 "exit_code":p.returncode,"argv":["python3","-B","calculate.py"],
                 "source_sha256":sha,"utc":datetime.now(timezone.utc).isoformat()}
        with LOCK:
            if len(RECEIPTS)>=512:
                self.send({"error":"RAM receipt limit"},status=429); return
            receipt["request_id"]=len(RECEIPTS)+1; RECEIPTS.append(receipt)
        self.send({"result":json.loads(p.stdout),"receipt":receipt})


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--delay-ms",type=int,default=0,choices=range(1001))
    DELAY_MS=parser.parse_args().delay_ms
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    print(json.dumps({"port":server.server_address[1],"scope":"own loopback only"}),flush=True)
    server.serve_forever()
