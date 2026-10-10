import pathlib,subprocess,sys,json,datetime,hashlib
R=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def execute(raw):
 start=utc();p=subprocess.run([sys.executable,'-B',str(R/'model.py')],input=raw,capture_output=True,text=True,timeout=5);end=utc();c={'inputRaw':raw,'argv':['python3','-B','model.py'],'startedUtc':start,'endedUtc':end,'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 inp=json.dumps(c);astart=utc();a=subprocess.run([sys.executable,'-B',str(R/'checker.py'),'--audit'],input=inp,capture_output=True,text=True,timeout=5);aend=utc();c.update(auditExitCode=a.returncode,auditStdout=a.stdout,auditStderr=a.stderr,auditCommand={'argv':['python3','-B','checker.py','--audit'],'inputRaw':inp,'startedUtc':astart,'endedUtc':aend,'exitCode':a.returncode,'stdout':a.stdout,'stderr':a.stderr})
 c['sourceHashes']={n:hashlib.sha256((R/n).read_bytes()).hexdigest() for n in ['model.py','checker.py','execute.py']};c['responseUtc']=utc();return c
