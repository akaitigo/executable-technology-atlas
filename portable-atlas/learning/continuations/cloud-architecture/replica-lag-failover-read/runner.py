import pathlib,json,hashlib,subprocess,datetime,platform,sys,shutil
R=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def record():
 started=datetime.datetime.now(datetime.timezone.utc);run=R/'observations'/started.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 fixtures=json.loads((R/'fixtures.json').read_text())
 names=['worker.py','runner.py','checker.py','test_negative.py','oracle.json','fixtures.json','index.html','preview.py','route.py','README.md','COVERAGE.md','skills/replica-lag-failover-read/SKILL.md']
 d={'startedUtc':started.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'storage':'two local in-memory model dictionaries; not durable stores'},'sourceHashes':{n:sha((R/n).read_bytes()) for n in names},'cases':[]}
 for name,x in fixtures.items():
  folder=run/name;folder.mkdir();inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode();(folder/'input.txt').write_bytes(inp)
  begin=datetime.datetime.now(datetime.timezone.utc).isoformat();z=subprocess.run([sys.executable,'-B',str(R/'worker.py')],input=inp,capture_output=True,timeout=10)
  (folder/'stdout.txt').write_bytes(z.stdout);(folder/'stderr.txt').write_bytes(z.stderr)
  try:observation=json.loads(z.stdout)
  except (ValueError,UnicodeDecodeError):observation=None
  d['cases'].append({'id':name,'argv':['python3','-B','worker.py'],'stdin':name+'/input.txt','inputSha256':sha(inp),'startedUtc':begin,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':z.returncode,'stdout':z.stdout.decode(),'stderr':z.stderr.decode(),'observation':observation,'outcome':'normal' if z.returncode==0 and observation else 'refusal' if z.returncode==2 and observation else 'execution-failure'})
 for n in ['worker.py','oracle.json','fixtures.json']:shutil.copyfile(R/n,run/n)
 raw=json.dumps(d,ensure_ascii=False,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
 files={p.relative_to(run).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
 (R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n');print(raw,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; checker.py is read-only')
 else:print('unsupported argument',file=sys.stderr);sys.exit(2)
