"""Memory-only evaluation/receipts. Starting, GET and POST never record unit files."""
import argparse,datetime,html,json,os,re,sys,time,uuid
from http.server import HTTPServer,SimpleHTTPRequestHandler
sys.dont_write_bytecode=True
from runner import ROOT,SOURCES,digest,run
parser=argparse.ArgumentParser();parser.add_argument('--delay-ms',type=int,choices=[0,600],default=0);args=parser.parse_args();receipts={};binding={n:digest(ROOT/n) for n in SOURCES}
DOCUMENTS={'readme':('README',ROOT/'README.md'),'calculate':('実装 calculate.py',ROOT/'calculate.py'),'checker':('独立13木 checker.py',ROOT/'checker.py'),'hand':('実装前手表',ROOT/'hand-oracle.json'),'coverage':('有限COVERAGE',ROOT/'COVERAGE.md'),'skill':('有限Skill',ROOT/'skills/atlas-huffman-payload-header-cost/SKILL.md'),'parent-path':('元Coding実験4（read-only reference）',ROOT/'../../../subjects/information-theory-coding/LEARNING_PATH.md')}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def end_headers(self):self.send_header('Cache-Control','no-store');super().end_headers()
 def send_json(self,x,status=200):
  body=json.dumps(x,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def document(self,title,text):
  body=('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{font:16px/1.65 system-ui;margin:0;background:#f3f6f7;color:#182d3a}main{max-width:1050px;margin:auto;padding:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:20px;background:white;border:1px solid #d8e1e5;font-size:13px}a{color:#167388}h1{font-size:25px}</style><main><a href="/index.html">教材へ戻る</a><h1>'+html.escape(title)+'</h1><p>固定allowlistのread-only表示。原文/sourceはescaped text、実行しません。</p><pre id="document-body">'+html.escape(text)+'</pre></main></html>').encode()
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  if self.path.startswith('/view/receipt/'):
   key=self.path.removeprefix('/view/receipt/')
   if key not in receipts:return self.send_error(404)
   return self.document('この実入力のmemory原票',json.dumps(receipts[key],ensure_ascii=False,indent=2))
  if self.path=='/view/fixed-raw':
   raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.HUFFMAN_OBSERVATION=').strip().removesuffix(';'))
   if not re.fullmatch(r'\d{8}T\d{12}Z-huffman',raw['run_id']):return self.send_error(500)
   return self.document('保存固定raw',(ROOT/'observations'/raw['run_id']/'raw.json').read_text())
  if self.path.startswith('/view/'):
   key=self.path.removeprefix('/view/')
   if key not in DOCUMENTS:return self.send_error(404)
   title,path=DOCUMENTS[key];return self.document(title,path.read_text())
  if self.path=='/api/health':return self.send_json({'mode':'memory-only','source_digests':binding,'request_count':len(receipts),'delay_ms':args.delay_ms})
  if self.path=='/api/receipts':return self.send_json({'mode':'memory-only','requests':list(receipts.values())})
  if self.path.startswith('/receipts/'):
   key=self.path.removeprefix('/receipts/').removesuffix('.json')
   if key not in receipts:return self.send_error(404)
   return self.send_json(receipts[key])
  super().do_GET()
 def do_POST(self):
  if self.path!='/measure':return self.send_error(404)
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=16384:return self.send_error(413)
   x=json.loads(self.rfile.read(size));text=x['input_json'];revision=x['revision']
   if type(text) is not str or len(text.encode())>4096 or type(revision) is not int:return self.send_error(400)
  except (ValueError,KeyError,TypeError):return self.send_error(400)
  req=uuid.uuid4().hex
  try:result=run(text)
  except Exception as e:
   result={'argv':['python3','-B','calculate.py'],'stdin':text,'stdout':'','stderr':'','exit':3,'result':{'status':'execution_error','summary':None,'cells':None,'error_class':type(e).__name__}}
  raw={'request_id':req,'request_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'revision':revision,'input_json':text,'run':result,'source_digests':binding,'mode':'memory-only','raw_href':'view/receipt/'+req,'raw_json_href':'receipts/'+req+'.json'};receipts[req]=raw
  if len(receipts)>512:receipts.pop(next(iter(receipts)))
  time.sleep(args.delay_ms/1000) # QA latency only, never a measured process property.
  try:self.send_json(raw)
  except (BrokenPipeError,ConnectionResetError):pass
try:
 server=HTTPServer(('127.0.0.1',0),Handler);print(json.dumps({'url':'http://127.0.0.1:'+str(server.server_port)+'/index.html','pid':os.getpid(),'mode':'memory-only','delay_ms':args.delay_ms,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}),flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close();print(json.dumps({'server_closed':True,'memory_receipts_discarded':len(receipts),'files_recorded':0}),flush=True)
except PermissionError as e:print(json.dumps({'failure':'socket.bind','class':type(e).__name__,'errno':e.errno,'files_recorded':0}),file=sys.stderr);sys.exit(1)
