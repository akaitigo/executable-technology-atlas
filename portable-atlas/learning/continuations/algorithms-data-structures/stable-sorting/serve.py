"""Atlas: loopback-only static reader; sorting is never executed by this server."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlsplit

BASE=Path(__file__).resolve().parent
RELATED=json.loads((BASE/'related-sources.json').read_text())
ALLOWED={'index.html','app.js','style.css','related.html','related.js','README.md','COVERAGE.md',
         'REPRODUCE.md','SKILL.md','SOURCES.md','CONTRACT.md','rejection-cases.json',
         'fixture.json','expected.json','qa/reader-acceptance.json','qa/independent-cli-reference.json',
         'verification/saved-result-check.json','verification/execution.json','observations/run-01/results.json',
         'observations/run-01/inputs/algorithm.py'}
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name=urlsplit(self.path).path.lstrip('/') or 'index.html'
        mapping={'related/'+key+'.md':Path(value['path']) for key,value in RELATED.items()}
        p=mapping.get(name) if name in mapping else BASE/name if name in ALLOWED else None
        if p is None or not p.is_file():self.send_error(404);return
        data=p.read_bytes()
        mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json'}.get(p.suffix,'text/plain')
        self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'")
        self.end_headers();self.wfile.write(data)
    def log_message(self,*args):pass
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=18762);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('ATLAS_PORT='+str(server.server_port),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
