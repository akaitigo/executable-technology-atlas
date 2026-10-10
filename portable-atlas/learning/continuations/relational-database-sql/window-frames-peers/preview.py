"""Temporary loopback; serves only this continuation and its read-only original SQL module."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parent
PREFIX='/continuations/relational-database-sql/window-frames-peers/'
REFERENCE=ROOT.parents[2]/'subjects'/'relational-database-sql'
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        path=unquote(urlsplit(path).path)
        if path.startswith(PREFIX):base=ROOT;rest=path[len(PREFIX):]
        elif path.startswith('/subjects/relational-database-sql/'):base=REFERENCE;rest=path[len('/subjects/relational-database-sql/'):]
        else:return str(ROOT/'__not_served__')
        target=(base/rest).resolve()
        try:target.relative_to(base.resolve())
        except ValueError:return str(ROOT/'__not_served__')
        return str(target)
with ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT))) as server:
    print(f'http://127.0.0.1:{server.server_port}{PREFIX}index.html',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
