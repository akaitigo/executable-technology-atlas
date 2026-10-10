"""Owned loopback service. RAM receipts; GET/POST/export never write."""
import argparse,html,json,time,uuid,datetime,threading
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from runner import ROOT,SOURCES,digest,run
MEM={};LOCK=threading.Lock();DELAY=0
VIEW={'readme':'README.md','calculate':'calculate.py','checker':'checker.py','hand':'hand-oracle.json','coverage':'COVERAGE.md','skill':'skills/atlas-merkle-membership-trusted-root/SKILL.md','parent-readme':'../../../subjects/decentralized-systems-blockchain/README.md'}
STATIC={'/index.html':'index.html','/app.js':'app.js','/styles.css':'styles.css','/observation-data.js':'observation-data.js'}
def encoded(data):return json.dumps(data,ensure_ascii=False).encode()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def send(self,status,data,typ='application/json; charset=utf-8'):
  self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
 def viewer(self,text):
  self.send(200,('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:24px;background:#f5f7fa;color:#152f38;font:14px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>固定allowlist text viewer</h1><pre>'+html.escape(text)+'</pre></html>').encode(),'text/html; charset=utf-8')
 def do_GET(self):
  path=self.path.split('?')[0]
  if path in ['/',*STATIC]:
   name=STATIC.get(path,'index.html');typ='text/javascript' if name.endswith('.js') else 'text/css' if name.endswith('.css') else 'text/html';return self.send(200,(ROOT/name).read_bytes(),typ+'; charset=utf-8')
  if path=='/api/health':return self.send(200,encoded({'mode':'memory-only','request_count':len(MEM),'delay_ms':DELAY,'source_digests':{n:digest(ROOT/n) for n in SOURCES}}))
  if path=='/api/export':
   with LOCK:data={'mode':'memory-only','requests':list(MEM.values())}
   return self.send(200,encoded(data))
  if path.startswith('/receipts/') and path.endswith('.json'):
   item=MEM.get(path[10:-5]);return self.send(200 if item else 404,encoded(item or {'status':'expired-or-unknown'}))
  if path.startswith('/view/receipt/'):
   item=MEM.get(path[len('/view/receipt/'):]);return self.viewer(json.dumps(item,ensure_ascii=False,indent=2)) if item else self.send(404,encoded({'status':'expired-or-unknown'}))
  if path=='/view/fixed-raw':
   text=(ROOT/'observation-data.js').read_text().split('=',1)[1].strip().removesuffix(';');return self.viewer(json.dumps(json.loads(text),ensure_ascii=False,indent=2))
  if path.startswith('/view/') and path[6:] in VIEW:return self.viewer((ROOT/VIEW[path[6:]]).read_text())
  return self.send(404,encoded({'status':'not-allowlisted'}))
 def do_POST(self):
  if self.path!='/measure':return self.send(404,encoded({'status':'not-allowlisted'}))
  try:
   length=int(self.headers.get('Content-Length','0'))
   if not 0<length<=20000:raise ValueError()
   req=json.loads(self.rfile.read(length));assert set(req)=={'input_json','revision'} and isinstance(req['input_json'],str) and type(req['revision']) is int
  except Exception:return self.send(400,encoded({'status':'request-shape'}))
  data={'request_id':uuid.uuid4().hex,'request_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':req['revision'],'input_json':req['input_json'],'run':run(req['input_json']),'source_digests':{n:digest(ROOT/n) for n in SOURCES},'mode':'memory-only'}
  data['raw_href']='view/receipt/'+data['request_id'];data['raw_json_href']='receipts/'+data['request_id']+'.json'
  with LOCK:
   MEM[data['request_id']]=data
   if len(MEM)>512:MEM.pop(next(iter(MEM)))
  time.sleep(DELAY/1000);self.send(200,encoded(data))
def main():
 global DELAY
 p=argparse.ArgumentParser();p.add_argument('--delay-ms',type=int,default=0);args=p.parse_args();DELAY=args.delay_ms
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:'+str(server.server_port)+'/index.html','mode':'memory-only','delay_ms':DELAY}),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close();print(json.dumps({'closed':True,'discarded':len(MEM),'files_written':0}),flush=True)
if __name__=='__main__':main()
