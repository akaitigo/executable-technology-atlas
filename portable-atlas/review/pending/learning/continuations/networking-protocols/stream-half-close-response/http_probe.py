import sys
sys.dont_write_bytecode=True
import argparse,json,urllib.request,urllib.error,urllib.parse,datetime
from pathlib import Path
from serve import FILES
R=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('url');a=ap.parse_args()
def request(path,b=None):
 req=urllib.request.Request(a.url+path,data=b,headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=3) as r:return r.status,json.loads(r.read())
 except urllib.error.HTTPError as exc:return exc.code,json.loads(exc.read())
raw=json.loads((R/'observations/attempt-01/raw.json').read_text());normal=[]
for row in raw['rows']:
 b=json.dumps({n:row[n] for n in ('fixture','mode','width')}).encode();status,v=request('/run',b);assert status==200 and v==row
 normal.append(dict(fixture=row['fixture'],mode=row['mode'],width=row['width'],status=status,exact=True,response=v))
refusals=[]
bodies=[b'{}',b'[]',b'null',b'{',b'NaN',b'{}'*1025,b'',b'{"fixture":"ping","mode":"normal","width":true}',b'{"fixture":"ping","mode":"normal","width":2}',b'{"fixture":"missing","mode":"normal","width":1}',b'{"fixture":"ping","mode":"unknown","width":1}',b'{"fixture":"ping","mode":"normal","width":1,"extra":1}']
for i,b in enumerate(bodies):
 status,v=request('/run',b);assert status==400;refusals.append(dict(case=i,status=status,response=v))
for path in ['/source?file=../README.md','/source?file=unknown','/source?file=CONTRACT.md&extra=1']:
 status,v=request(path);assert status==400;refusals.append(dict(case=path,status=status,response=v))
sources=[]
for n in FILES:
 status,v=request('/source?file='+urllib.parse.quote(n));assert status==200 and v['text']==(R/n).read_text();sources.append(dict(file=n,status=status,exact=True))
status,p=request('/probes');assert status==200 and p==raw['probes']
(R/'observations/http.json').write_text(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),normal=normal,refusals=refusals,sources=sources,probes_exact=True),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(rows=len(normal),refusals=len(refusals),sources=len(sources),probes_exact=True)))
