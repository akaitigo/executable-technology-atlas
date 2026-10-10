import pathlib,json,hashlib,subprocess,datetime,platform,sys,sqlite3,shutil
R=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def record():
 start=datetime.datetime.now(datetime.timezone.utc);run=R/'observations'/start.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 source=[p for p in R.rglob('*') if p.is_file() and not any(n in p.relative_to(R).parts for n in ('observations','media','revisions')) and p.name not in ('CURRENT','QA.json','qa-artifacts.json')]
 d={'startedUtc':start.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'sqlite':sqlite3.sqlite_version,'ticks':'virtual ordered integers; no sleeps; seed at -1'},'sourceHashes':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in source},'cases':[]}
 for n in ['driver.py','consumer.py','oracle.json','requests.json']:shutil.copyfile(R/n,run/n)
 for name,x in json.loads((R/'requests.json').read_text()).items():
  folder=run/name;folder.mkdir();inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode();(folder/'input.txt').write_bytes(inp)
  started=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run([sys.executable,'-B','../driver.py','state.sqlite'],cwd=folder,input=inp,capture_output=True,timeout=30)
  (folder/'stdout.txt').write_bytes(p.stdout);(folder/'stderr.txt').write_bytes(p.stderr)
  try:o=json.loads(p.stdout)
  except (ValueError,UnicodeDecodeError):o=None
  d['cases'].append({'id':name,'argv':['python3','-B','../driver.py','state.sqlite'],'inputSha256':sha(inp),'startedUtc':started,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'observation':o,'outcome':'OBSERVED' if p.returncode==0 and o else 'REFUSED' if p.returncode==2 and o else 'EXECUTION_FAILURE','db':name+'/state.sqlite' if (folder/'state.sqlite').exists() else None})
 raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
 files={p.relative_to(run).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()};(run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
 (R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n');print(raw,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; checker.py is read-only')
 else:print('unsupported argument',file=sys.stderr);sys.exit(2)
