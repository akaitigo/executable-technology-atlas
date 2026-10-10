from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(R),**k)
 def guess_type(self,path):return 'text/plain; charset=utf-8' if path.endswith('.md') else super().guess_type(path)
 def translate_path(self,path):
  allowed={'/subjects/software-architecture/README.md':R.parents[2]/'subjects/software-architecture/README.md',
   '/cloud-architecture/replica-lag-failover-read/README.md':R.parents[1]/'cloud-architecture/replica-lag-failover-read/README.md'}
  clean=unquote(urlsplit(path).path)
  if clean in allowed:return str(allowed[clean])
  p=Path(super().translate_path(path)).resolve()
  return str(p) if p==R or R in p.parents else str(R/'not-found')
if __name__=='__main__':
 s=ThreadingHTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(s.server_port)+'/',flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
