# SPDX-License-Identifier: Apache-2.0
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  paths={'/subjects/analytics-data-platform/README.md':ROOT.parents[2]/'subjects/analytics-data-platform/README.md','/subjects/relational-database-sql/README.md':ROOT.parents[2]/'subjects/relational-database-sql/README.md'}
  if self.path in paths:
   data=paths[self.path].read_bytes();self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
print(f'http://127.0.0.1:{server.server_port}/index.html',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:server.server_close()
