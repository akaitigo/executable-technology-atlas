from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs
import json,sys,subprocess,datetime,hashlib,time
R=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(R),**k)
 def guess_type(self,path):return 'text/plain; charset=utf-8' if path.endswith('.md') else super().guess_type(path)
 def translate_path(self,path):
  fixed={'/subjects/container-orchestration/README.md':R.parents[2]/'subjects/container-orchestration/README.md','/performance-capacity-engineering/two-server-bounded-queue/README.md':R.parents[1]/'performance-capacity-engineering/two-server-bounded-queue/README.md','/finops-cost-engineering/unit-cost-denominator/README.md':R.parents[1]/'finops-cost-engineering/unit-cost-denominator/README.md'}
  clean=unquote(urlsplit(path).path)
  if clean in fixed:return str(fixed[clean])
  p=Path(super().translate_path(path)).resolve();return str(p) if p==R or R in p.parents else str(R/'not-found')
 def do_POST(self):
  if urlsplit(self.path).path!='/api/run':self.send_error(404);return
  size=int(self.headers.get('Content-Length','0'))
  if not 1<=size<=30000:self.send_error(413);return
  inp=self.rfile.read(size);start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run([sys.executable,'-B','model.py'],cwd=R,input=inp,capture_output=True,timeout=5);modelEnd=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:o=json.loads(p.stdout)
  except ValueError:o=None
  try:x=json.loads(inp)
  except ValueError:x={'rawInput':inp.decode()}
  ai=json.dumps({'request':x,'observation':o})+'\n';astart=datetime.datetime.now(datetime.timezone.utc).isoformat();ap=subprocess.run([sys.executable,'-B','checker.py','--audit'],cwd=R,input=ai.encode(),capture_output=True,timeout=5);auditEnd=datetime.datetime.now(datetime.timezone.utc).isoformat()
  try:a=json.loads(ap.stdout)
  except ValueError:a=None
  query=parse_qs(urlsplit(self.path).query);delay=2000 if query.get('qaDelay')==['2000'] else 0
  if delay:time.sleep(2) # transport-only QA response hold; not placement-model time
  out={'argv':['python3','-B','model.py'],'stdin':inp.decode(),'startedUtc':start,'endedUtc':modelEnd,'responseUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'observation':o,'outcome':'OBSERVED' if p.returncode==0 else 'REFUSED' if p.returncode==2 else 'EXECUTION_FAILURE','audit':a,'auditCommand':{'argv':['python3','-B','checker.py','--audit'],'stdin':ai,'startedUtc':astart,'endedUtc':auditEnd,'exitCode':ap.returncode,'stdout':ap.stdout.decode(),'stderr':ap.stderr.decode()},'qaResponseDelayMs':delay,'sourceHashes':{n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ('model.py','checker.py')}}
  data=json.dumps(out).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
if __name__=='__main__':
 s=ThreadingHTTPServer(('127.0.0.1',0),Handler);print('http://127.0.0.1:'+str(s.server_port)+'/',flush=True)
 try:s.serve_forever()
 except KeyboardInterrupt:pass
 finally:s.server_close()
