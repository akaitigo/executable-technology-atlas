from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT=Path(__file__).resolve().parent
RAM=[];LOCK=threading.Lock()
ALLOWED={"index.html","app.js","style.css","README.md","COVERAGE.md","Skill.md",
         "contract.json","hand-table.json","expected.json","matrix-hand.json",
         "calculate.py","oracle.py","checker.py","runner.py","server.py","route.py"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,value,mime="application/json",status=200):
        if not isinstance(value,bytes):value=json.dumps(value,ensure_ascii=False).encode()
        self.send_response(status);self.send_header("Content-Type",mime)
        self.send_header("Content-Length",str(len(value)));self.end_headers();self.wfile.write(value)
    def do_GET(self):
        if self.path=="/api/receipts":
            with LOCK:self.send(list(RAM))
            return
        if self.path=="/api/cases":
            cases=json.loads((ROOT/"expected.json").read_text())
            self.send([{**c,"stdin":json.dumps(c["input"],ensure_ascii=False,indent=2)} for c in cases]);return
        name="index.html" if self.path=="/" else self.path.lstrip("/")
        if name not in ALLOWED:self.send({"error":"not found"},status=404);return
        if name not in {"index.html","app.js","style.css"}:
            page='<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+name+'</title><main><h1>'+name+'</h1><a href="/">教材に戻る</a><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+html.escape((ROOT/name).read_text())+'</pre></main></html>'
            self.send(page.encode(),"text/html; charset=utf-8");return
        mime={"index.html":"text/html","app.js":"text/javascript","style.css":"text/css"}[name]
        self.send((ROOT/name).read_bytes(),mime+"; charset=utf-8")
    def do_POST(self):
        if self.path!="/api/calculate":self.send({"error":"not found"},status=404);return
        n=int(self.headers.get("Content-Length","0"))
        if n>8192:self.send({"error":"too large"},status=413);return
        stdin=self.rfile.read(n).decode()
        sha=hashlib.sha256((ROOT/"calculate.py").read_bytes()).hexdigest()
        p=subprocess.run([sys.executable,"-B",str(ROOT/"calculate.py")],input=stdin,
                         text=True,capture_output=True,timeout=5)
        receipt={"stdin":stdin,"stdout":p.stdout,"stderr":p.stderr,"exit_code":p.returncode,
                 "argv":["python3","-B","calculate.py"],"source_sha256":sha,
                 "utc":datetime.now(timezone.utc).isoformat()}
        with LOCK:
            if len(RAM)>=512:self.send({"error":"receipt limit"},status=429);return
            receipt["request_id"]=len(RAM)+1;RAM.append(receipt)
        self.send({"result":json.loads(p.stdout),"receipt":receipt})


if __name__=="__main__":
    s=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    print(json.dumps({"port":s.server_address[1],"scope":"own loopback"}),flush=True);s.serve_forever()
