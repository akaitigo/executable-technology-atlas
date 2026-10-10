import sys
sys.dont_write_bytecode=True
import json,urllib.request,urllib.error,argparse,datetime
from pathlib import Path
from fixtures import FIXTURES
from admission import SCHEDULES,run
from serve import FILES
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('url');a=ap.parse_args()
def request(path,body=None):
 req=urllib.request.Request(a.url+path,data=body,headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=3) as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as exc:return exc.code,json.loads(exc.read())
normal=[]
for f in FIXTURES:
 for s in SCHEDULES:
  status,row=request('/run',json.dumps(dict(fixture=f['id'],schedule=s)).encode());exact=row==run(f,s)
  assert status==200 and exact;normal.append(dict(fixture=f['id'],schedule=s,status=status,exact=exact,response=row))
bodies=[b'{}',b'[]',b'null',b'{',b'NaN',b'{}'*1025,json.dumps(dict(fixture='same',schedule='unknown')).encode(),json.dumps(dict(fixture='unknown',schedule='split-2')).encode(),json.dumps(dict(fixture='same',schedule=True)).encode(),json.dumps(dict(fixture='same',schedule='split-2',extra=1)).encode(),b'']
refusals=[]
for i,b in enumerate(bodies):
 status,row=request('/run',b);assert status==400;refusals.append(dict(case=i,status=status,response=row))
for p in ['/source?file=../README.md','/source?file=CONTRACT.md&extra=1','/source?file=unknown']:
 status,row=request(p);assert status==400;refusals.append(dict(case=p,status=status,response=row))
sources=[]
for n in FILES:
 status,row=request('/source?file='+urllib.parse.quote(n));assert status==200 and row['text']==(R/n).read_text();sources.append(dict(file=n,status=status,exact=True))
status,t=request('/threads');assert status==200 and t==json.loads((R/'observations/attempt-01/threads.json').read_text())
(R/'observations/http.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),normal=normal,refusals=refusals,sources=sources,stored_threads_exact=True),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(normal=len(normal),refusals=len(refusals),sources=len(sources),stored_threads_exact=True)))
