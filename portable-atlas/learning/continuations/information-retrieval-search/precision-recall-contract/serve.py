# SPDX-License-Identifier: Apache-2.0
"""Owned temporary module-only loopback preview; actual dynamic URL; Ctrl-C closes."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);args=p.parse_args()
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        related={'/subjects/information-retrieval-search/README.md','/subjects/generative-ai-rag/README.md'}
        if self.path in related:
            data=(ROOT.parents[2]/self.path.lstrip('/')).read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT)))
print(f'http://127.0.0.1:{server.server_port}/index.html',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
