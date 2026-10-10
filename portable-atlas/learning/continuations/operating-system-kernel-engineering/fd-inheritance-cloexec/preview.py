#!/usr/bin/env python3
"""Atlas: own loopback preview with an explicit read-only reference allowlist."""
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import argparse,html,json,hashlib
ROOT=Path(__file__).resolve().parent
REFERENCES={x['slug']:x for x in json.loads((ROOT/'reference-map.json').read_text())['entries']}

def reference_html(slug):
    entry=REFERENCES[slug];data=Path(entry['path']).read_bytes()
    if hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('参照元が変更されています。保存した対応を再確認してください。')
    lines=data.decode().splitlines()
    if entry['line_start']:lines=lines[entry['line_start']-1:entry['line_end']]
    body='\n'.join(lines)
    return ('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atlas：'+html.escape(entry['title'])+'</title><style>body{font-family:system-ui;max-width:960px;margin:30px auto;padding:15px;line-height:1.8}pre{white-space:pre-wrap;overflow-wrap:anywhere}code{overflow-wrap:anywhere}</style><h1>Atlas：'+html.escape(entry['title'])+'</h1><p>元ファイルの読取り専用表示です。実験は実行しません。</p><code>'+html.escape(entry['path'])+'</code><p><a href="../references.html">前提一覧へ戻る</a> / <a href="../index.html">FD継承の教材へ戻る</a></p><pre>'+html.escape(body)+'</pre></html>').encode()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        requested=self.path.split('?')[0]
        if requested.startswith('/reference/'):
            slug=requested.removeprefix('/reference/')
            if slug not in REFERENCES:self.send_error(404);return
            try:body=reference_html(slug)
            except (OSError,ValueError) as ex:self.send_error(409,str(ex));return
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
        super().do_GET()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=0);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print('Atlas: http://127.0.0.1:%d/ (Ctrl+C to stop)'%server.server_port,flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
