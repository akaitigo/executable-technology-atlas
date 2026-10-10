"""Owned loopback server; dynamic port, bounded JSON API, stdlib only."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from model import experiment
ROOT = Path(__file__).resolve().parent
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/api':
            try:
                q = parse_qs(url.query, strict_parsing=True)
                if set(q) != {'phase','version','now','fault'} or any(len(v) != 1 for v in q.values()): raise ValueError('input')
                result = experiment(q['phase'][0], q['version'][0], int(q['now'][0]), q['fault'][0])
                data = json.dumps(result).encode(); status = 200; mime = 'application/json'
            except (ValueError, KeyError):
                data = b'{"error":"input"}'; status = 400; mime = 'application/json'
        elif url.path in ('/', '/index.html'):
            data = (ROOT / 'index.html').read_bytes(); status = 200; mime = 'text/html; charset=utf-8'
        else:
            self.send_error(404); return
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers(); self.wfile.write(data)
    def log_message(self, fmt, *args): pass
if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 0), Handler)
    print(json.dumps({'url': 'http://127.0.0.1:%d' % server.server_port, 'title': 'HMAC鍵ローテーション実験室'}), flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
