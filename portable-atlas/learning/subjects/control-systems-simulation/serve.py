"""loopback限定の教材サーバー。API結果はPythonで計算し、専用pathへ記録。"""
import json
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from simulator import ROOT, observe


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_):
        pass

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path != "/api/simulate":
            return super().do_GET()
        try:
            query = parse_qs(parsed.query, strict_parsing=True)
            if not set(query) <= {"gain", "dt", "limit", "steps"} or any(len(v) != 1 for v in query.values()):
                raise ValueError("未知/重複パラメータです")
            inputs = {"gain": float(query.get("gain", [2])[0]), "dt": float(query.get("dt", [.1])[0]),
                      "steps": int(query.get("steps", [40])[0]),
                      "limit": float(query["limit"][0]) if "limit" in query else None}
            result = observe(inputs, ["HTTP GET", self.path])
            run_id = uuid.uuid4().hex
            result["execution"]["raw_path"] = f"observations/ui-{run_id}.json"
            payload = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode()
            folder = ROOT/"observations"
            folder.mkdir(exist_ok=True)
            (ROOT/result["execution"]["raw_path"]).write_bytes(payload)
            status = 200
        except (ValueError, TypeError, OverflowError) as error:
            payload = json.dumps({"error": str(error)}, ensure_ascii=False).encode()
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 18771), Handler)
    print("control simulator http://127.0.0.1:18771 (CPU only)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
