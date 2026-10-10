# SPDX-License-Identifier: Apache-2.0
"""Module-only loopback preview. Ctrl-C closes the owned server."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--port',type=int,default=0)
args = parser.parse_args()
server = ThreadingHTTPServer(('127.0.0.1',args.port), partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parent)))
print(f'http://127.0.0.1:{server.server_port}/index.html',flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
