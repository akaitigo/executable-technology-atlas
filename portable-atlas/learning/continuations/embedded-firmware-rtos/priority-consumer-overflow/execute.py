import sys,json,subprocess,datetime,hashlib,uuid
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCES=['model.py','oracle.py','execute.py','runner.py','server.py','ui.js','index.html','fixture.json','oracle.json','custom-oracle.json','EXPECTATIONS.md','README.md','SOURCES.md','route.py']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def execute(text,inject=False):
 cmd=['python3','-B','model.py']+(['--inject-failure'] if inject else []);start=utc();r=subprocess.run(cmd,cwd=P,input=text,text=True,capture_output=True);end=utc()
 try:result=json.loads(r.stdout)
 except ValueError:result=dict(status='EXECUTION_FAILURE',reason='CHILD_STDOUT',trace=[],counts=None)
 audit=None
 if result['status']=='OBSERVED':
  audit_input=json.dumps(dict(input=json.loads(text),result=result));astart=utc();a=subprocess.run(['python3','-B','oracle.py'],cwd=P,input=audit_input,text=True,capture_output=True)
  audit=dict(argv=['python3','-B','oracle.py'],stdin=audit_input,started=astart,completed=utc(),exit=a.returncode,stdout=a.stdout,stderr=a.stderr)
 return dict(request_id=uuid.uuid4().hex,argv=cmd,input_json=text,started=start,completed=end,exit=r.returncode,stdout=r.stdout,stderr=r.stderr,result=result,audit=audit,source_sha256={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in SOURCES},runtime=sys.version.split()[0])
