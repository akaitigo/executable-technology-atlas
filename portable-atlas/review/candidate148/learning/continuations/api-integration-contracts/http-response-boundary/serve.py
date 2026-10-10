"""Atlas: 保存資料だけをloopback配信する。模型や外部操作は起動しない。"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
RELATED = json.loads((ROOT / "related-sources.json").read_text())
ALLOWED = {'related.html', 'cases.json', 'README.md', 'app.js', 'COVERAGE.md', 'related.js', 'SOURCES.md', 'boundary.py', 'style.css', 'qa/reader-acceptance.json', 'verification/execution.json', 'experiment.py', 'SKILL.md', 'observations/run-01/results.json', 'observations/run-01/inputs/boundary.py', 'index.html', 'expected.json', 'CONTRACT.md', 'verification/saved-result-check.json', 'REPRODUCE.md'}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = urlsplit(self.path).path.lstrip("/") or "index.html"
        mapping = {"related/" + k + ".md": Path(v["path"]) for k, v in RELATED.items()}
        path = mapping.get(name) if name in mapping else ROOT / name if name in ALLOWED else None
        if path is None or not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        mime = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json"}.get(path.suffix, "text/plain")
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18785)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("ATLAS_PORT=" + str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
