"""Atlas: read-only lesson files on loopback; no calculation or browser launch."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

BASE = Path(__file__).resolve().parent
MIMES = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
         '.json': 'application/json', '.md': 'text/plain', '.py': 'text/plain'}

def local_file(url):
    relative = unquote(urlsplit(url).path).lstrip('/') or 'index.html'
    target = (BASE / relative).resolve()
    if BASE not in target.parents or any(part.startswith('.') for part in Path(relative).parts):
        return None
    return target if target.is_file() else None

class Handler(BaseHTTPRequestHandler):
    def serve_file(self, head=False):
        target = local_file(self.path)
        if target is None:
            self.send_error(404)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', MIMES.get(target.suffix, 'text/plain') + '; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        if not head:
            self.wfile.write(data)

    def do_GET(self):
        self.serve_file()

    def do_HEAD(self):
        self.serve_file(head=True)

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print('ATLAS_PORT=' + str(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
