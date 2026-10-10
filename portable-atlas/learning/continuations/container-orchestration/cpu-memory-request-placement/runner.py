import pathlib,json,hashlib,subprocess,datetime,platform,sys,shutil
R=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def record():
 t=datetime.datetime.now(datetime.timezone.utc);run=R/'observations'/t.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 files=[p for p in R.rglob('*') if p.is_file() and not any(n in p.relative_to(R).parts for n in ('observations','media','revisions')) and p.name not in ('CURRENT','QA.json','qa-artifacts.json')]
 d={'startedUtc':t.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'model':'fixed first-fit integer request units; not Kubernetes scheduler or usage/limits'},'sourceHashes':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in files},'cases':[]}
 for n in ('model.py','checker.py'):shutil.copyfile(R/n,run/n)
 for name,x in json.loads((R/'requests.json').read_text()).items():
  folder=run/name;folder.mkdir();inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode();(folder/'input.txt').write_bytes(inp)
  start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run([sys.executable,'-B','../model.py'],cwd=folder,input=inp,capture_output=True,timeout=5);(folder/'stdout.txt').write_bytes(p.stdout);(folder/'stderr.txt').write_bytes(p.stderr)
  try:o=json.loads(p.stdout)
  except ValueError:o=None
  c={'id':name,'argv':['python3','-B','../model.py'],'startedUtc':start,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputSha256':sha(inp),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'observation':o,'outcome':'OBSERVED' if p.returncode==0 else 'REFUSED' if p.returncode==2 else 'EXECUTION_FAILURE'}
  ai=json.dumps({'request':x,'observation':o})+'\n';astart=datetime.datetime.now(datetime.timezone.utc).isoformat();ap=subprocess.run([sys.executable,'-B','../checker.py','--audit'],cwd=folder,input=ai.encode(),capture_output=True,timeout=5)
  ac={'argv':['python3','-B','../checker.py','--audit'],'stdin':ai,'startedUtc':astart,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':ap.returncode,'stdout':ap.stdout.decode(),'stderr':ap.stderr.decode()};(folder/'audit-input.txt').write_text(ai);(folder/'audit-stdout.txt').write_bytes(ap.stdout);(folder/'audit-stderr.txt').write_bytes(ap.stderr);(folder/'audit-command.json').write_text(json.dumps(ac,indent=2)+'\n');c['audit']=json.loads(ap.stdout)
  (folder/'command.json').write_text(json.dumps(c,indent=2)+'\n');d['cases'].append(c)
 raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw);(run/'artifacts.json').write_text(json.dumps({'files':{p.relative_to(run).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()}},indent=2)+'\n');(R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n');print(raw,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; no mutation')
 else:print('unsupported argument',file=sys.stderr);sys.exit(2)
