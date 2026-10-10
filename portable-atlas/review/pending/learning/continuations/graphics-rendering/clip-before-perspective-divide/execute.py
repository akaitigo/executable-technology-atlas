import subprocess,sys,json,datetime,uuid,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCES=['model.py','oracle.py','execute.py','runner.py','server.py','ui.js','index.html','document.html','fixture.json','oracle.json','custom-oracle.json','README.md','EXPECTATIONS.md','SOURCES.md','COVERAGE.md','route.py','skills/atlas-near-plane-clip/SKILL.md']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def execute(text,fail=False):
 argv=['model.py']+(['--fail'] if fail else []);start=utc();r=subprocess.run([sys.executable,'-B']+argv,input=text,text=True,capture_output=True,cwd=P);out=json.loads(r.stdout);audit=None
 if out['status']=='OBSERVED':
  atext=json.dumps(dict(input=json.loads(text),result=out));s=utc();a=subprocess.run([sys.executable,'-B','oracle.py'],input=atext,text=True,capture_output=True,cwd=P);audit=dict(argv=['python3','-B','oracle.py'],stdin=atext,started=s,completed=utc(),exit=a.returncode,stdout=a.stdout,stderr=a.stderr)
 return dict(request_id=uuid.uuid4().hex,argv=['python3','-B']+argv,input_json=text,started=start,completed=utc(),exit=r.returncode,stdout=r.stdout,stderr=r.stderr,result=out,audit=audit,runtime=sys.version.split()[0],source_sha256={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in SOURCES})
