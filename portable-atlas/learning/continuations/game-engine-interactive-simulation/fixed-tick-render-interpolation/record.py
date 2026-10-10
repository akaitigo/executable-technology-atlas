import json,sys,subprocess,hashlib,uuid,datetime
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent
cases=json.loads((P/'cases.json').read_text());literals=json.loads((P/'oracle.json').read_text())
custom=json.loads((P/'custom-oracle.json').read_text());attempts=[]
for c in cases+custom:
    cmd=['node','runner.mjs',c['id'] if c in cases else 'normal-5']
    if c in custom:cmd.append(json.dumps(c['input']))
    start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(cmd,cwd=P,text=True,capture_output=True)
    raw=json.loads(r.stdout);check(raw['result'],c['input'],literals[c['id']] if c in cases else c['rows'])
    assert r.returncode==(2 if raw['result']['status']=='REFUSED' else 0)
    attempts.append(dict(id=c['id'],command=cmd,started=start,exit=r.returncode,stdout=r.stdout,stderr=r.stderr))
report=dict(status='passed',attempts=attempts,source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in P.iterdir() if f.is_file()},clock='UTC execution timestamps; synthetic input separate')
if sys.argv[1:]==['--record']:
    name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
    (P/'evidence'/name).write_text(json.dumps(report,indent=2)+'\n')
    (P/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=hashlib.sha256((P/'evidence'/name).read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(dict(status='passed',actual_children=len(attempts))))
