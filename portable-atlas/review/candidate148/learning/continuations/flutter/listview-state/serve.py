#!/usr/bin/env python3
"""教材と固定証拠だけをloopbackで配信。SDK/cache/任意ファイルは配信しない。"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
ALLOWED = {'index.html', 'app.js', 'style.css', 'README.md', 'COVERAGE.md', 'SKILL.md',
           'REPRODUCE.md', 'probe/observations/attempt-01/actual.json',
           'probe/observations/attempt-01/inputs/probe/lib/listview_probe.dart'}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = urlsplit(self.path).path.removeprefix('/') or 'index.html'
        if name == 'favicon.ico':
            self.send_response(204); self.end_headers(); return
        if name not in ALLOWED:
            self.send_error(404, 'Not found'); return
        data = (ROOT / name).read_bytes()
        mime = mimetypes.guess_type(name)[0] or 'text/plain'
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers(); self.wfile.write(data)

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18751)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
