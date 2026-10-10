# SPDX-License-Identifier: Apache-2.0
"""Owned temporary module-only loopback HTTP preview. Ctrl-C closes."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=0);args=p.parse_args()
server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parent)))
print(f'http://127.0.0.1:{server.server_port}/index.html',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
