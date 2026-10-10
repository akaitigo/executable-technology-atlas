"""Own temporary loopback preview only. Ctrl-C closes the listener."""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from runner import ROOT, run
from oracle import impact

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/api':
            case = parse_qs(url.query).get('case', ['config'])[0]
            if case not in ['config', 'price', 'invoice', 'report', 'audit', 'nochange', 'cycle', 'unknown', 'stale']:
                self.send_error(400, 'unsupported case')
                return
            result = run(case)
            if 'rejected' not in result:
                nodes, ps = impact(result['input']['graph'], result['input']['changed'])
                result['oracle'] = {'affected': nodes, 'paths': ps, 'matches': nodes == result['affected']}
            body = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

if __name__ == '__main__':
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        print(f'http://127.0.0.1:{server.server_port}/index.html', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('owned listener closed', flush=True)
