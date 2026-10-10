#!/usr/bin/env python3
import http.server,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def translate_path(self,path):
        p=pathlib.Path(super().translate_path(path)).resolve();return str(p if p==ROOT or ROOT in p.parents else ROOT/'__denied__')
    def log_message(self,fmt,*args):print(fmt%args,flush=True)
if __name__=='__main__':
    with http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler) as s:
        print('http://127.0.0.1:'+str(s.server_port)+'/',flush=True)
        try:s.serve_forever()
        except KeyboardInterrupt:pass
