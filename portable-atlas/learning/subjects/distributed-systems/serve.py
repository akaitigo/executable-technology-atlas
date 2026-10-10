"""2 replica教材の専用loopback server。実replication trafficは発生させない。"""
import json
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from model import ROOT, MODES, observe


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_):
        pass

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != "/api/run":
            return super().do_GET()
        try:
            query = parse_qs(parsed.query, strict_parsing=True)
            if not set(query) <= {"order", "duplicate"} or any(len(v) != 1 for v in query.values()):
                raise ValueError("未知/重複パラメータです")
            order = query.get("order", ["A2,A1,B1"])[0].split(",")
            duplicate = query.get("duplicate", ["0"])[0]
            if duplicate not in ("0", "1"):
                raise ValueError("duplicateは0/1です")
            report = {mode: observe(mode, order, duplicate == "1", ["HTTP GET", self.path]) for mode in MODES}
            report["raw_path"] = f"observations/ui-{uuid.uuid4().hex}.json"
            payload = (json.dumps(report, ensure_ascii=False, indent=2)+"\n").encode()
            (ROOT/"observations").mkdir(exist_ok=True)
            (ROOT/report["raw_path"]).write_bytes(payload)
            status = 200
        except (ValueError, TypeError) as error:
            payload, status = json.dumps({"error": str(error)}, ensure_ascii=False).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 18772), Handler)
    print("distributed simulator http://127.0.0.1:18772 (CPU only)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
