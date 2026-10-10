"""Read-only runs; --record explicitly creates a new receipt."""
import argparse,json,hashlib,datetime,uuid,sys
from pathlib import Path
from producer import run,FIXTURE
ROOT=Path(__file__).resolve().parent
SOURCES=['fixture.json','oracle.json','EXPECTATIONS.md','producer.py','runner.py','server.py','index.html','ui.js']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observe():return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B runner.py --record',source_sha256={n:sha(ROOT/n) for n in SOURCES},fixture=FIXTURE,cases=[run(c['id']) for c in FIXTURE['cases']])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--case',default='cap-change');p.add_argument('--record',action='store_true');args=p.parse_args()
 if args.record:
  r=observe();name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(r,f,ensure_ascii=False,indent=2);f.write('\n')
  expected={c['id'] for c in FIXTURE['cases'] if c['variant']=='execution-failure'}
  if not any(c['status']=='EXECUTION_FAILURE' and c['case'] not in expected for c in r['cases']):(ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n')
  print(name)
 else:print(json.dumps(run(args.case),ensure_ascii=False,indent=2))
