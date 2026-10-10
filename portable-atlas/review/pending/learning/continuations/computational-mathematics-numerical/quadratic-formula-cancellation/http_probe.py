import sys
sys.dont_write_bytecode=True
import argparse,json,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from fixtures import FIXTURES
from solver import METHODS
from lesson import run
ap=argparse.ArgumentParser();ap.add_argument('url');a=ap.parse_args()
report=dict(utc=datetime.now(timezone.utc).isoformat(),endpoint='own dynamic localhost',normal=[],refusals=[])
def send(body):
    req=urllib.request.Request(a.url+'/run',data=body.encode(),headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req) as response:return response.status,json.load(response)
    except urllib.error.HTTPError as exc:return exc.code,json.load(exc)
try:
    for f in FIXTURES:
        for m in METHODS:
            status,data=send(json.dumps(dict(fixture=f['id'],method=m)))
            assert status==200 and data==run(f,m)
            report['normal'].append(dict(fixture=f['id'],method=m,status=status,exact=True))
    bad=['{','[]','true','null','{}','{"fixture":"severe"}',
      '{"fixture":"unknown","method":"standard"}','{"fixture":"severe","method":"unknown"}',
      '{"fixture":"severe","method":true}','{"fixture":"severe","method":{}}',
      '{"fixture":"severe","method":"standard","extra":1}',
      '{"fixture":"severe","method":NaN}','{"fixture":"severe","method":Infinity}']
    for body in bad:
        status,data=send(body);assert status==400 and 'error' in data
        report['refusals'].append(dict(body=body,status=status,response=data))
    Path('observations/http.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(normal=20,refusals=13,status='passed')))
except urllib.error.URLError as exc:
    Path('observations/sandbox-connect-failure.json').write_text(json.dumps(dict(utc=report['utc'],error=str(exc.reason),phase='same own localhost HTTP connect',exit_status=1),indent=2)+'\n')
    print(str(exc.reason));sys.exit(1)
