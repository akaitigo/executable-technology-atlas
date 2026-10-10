import sys
sys.dont_write_bytecode=True
import json,argparse,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from fixtures import FIXTURES
from model import run,MODES
from oracle import sequential
ap=argparse.ArgumentParser();ap.add_argument('url');args=ap.parse_args()
report=dict(utc=datetime.now(timezone.utc).isoformat(),endpoint='own dynamic localhost server',normal=[],refusals=[])
def send(body):
    request=urllib.request.Request(args.url+'/run',data=body.encode(),headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as exc:return exc.code,json.load(exc)
try:
    for f in FIXTURES:
        for mode in MODES:
            code,r=send(json.dumps(dict(fixture=f['id'],mode=mode)))
            wanted=dict(fixture=f['id'],oracle=sequential(f['program'],f['initial']),**run(f['program'],f['initial'],mode))
            wanted['matches_oracle']=wanted['registers']==wanted['oracle']
            assert code==200 and r==wanted
            report['normal'].append(dict(fixture=f['id'],mode=mode,status=code,exact=True))
    bad=['{','[]','true','null','{}','{"fixture":"chain"}',
         '{"fixture":"unknown","mode":"none"}','{"fixture":"chain","mode":"unknown"}',
         '{"fixture":"chain","mode":true}','{"fixture":"chain","mode":{}}',
         '{"fixture":"chain","mode":"none","extra":1}',
         '{"fixture":"chain","mode":NaN}','{"fixture":"chain","mode":Infinity}']
    for body in bad:
        code,r=send(body);assert code==400 and 'error' in r
        report['refusals'].append(dict(body=body,status=code,response=r))
    Path('observations/http.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(normal=len(report['normal']),refusals=len(report['refusals']),status='passed')))
except urllib.error.URLError as exc:
    Path('observations/sandbox-connect-failure.json').write_text(json.dumps(dict(utc=report['utc'],error=str(exc.reason),scope='same own localhost server',phase='HTTP connect',exit_status=1),indent=2)+'\n')
    print(str(exc.reason));sys.exit(1)
