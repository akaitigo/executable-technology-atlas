"""Owned temporary loopback preview, dynamic port; Ctrl-C closes server."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
from pathlib import Path
with ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(Path(__file__).resolve().parent))) as server:
    print(f'http://127.0.0.1:{server.server_port}/index.html',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
