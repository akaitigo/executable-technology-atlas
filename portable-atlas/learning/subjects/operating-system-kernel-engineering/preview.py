import functools,http.server,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class Handler(http.server.SimpleHTTPRequestHandler):
 def guess_type(self,path):
  if Path(path).suffix in ('.md','.py','.txt'):return 'text/plain; charset=utf-8'
  return super().guess_type(path)
 def log_message(self,*args):pass
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
if __name__=='__main__':
 with http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT))) as s:
  print(json.dumps({'url':'http://127.0.0.1:%d/index.html'%s.server_port}),flush=True)
  try:s.serve_forever()
  except KeyboardInterrupt:pass
