import pathlib,json,hashlib,subprocess,datetime,platform,sys,shutil
R=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def record():
 t=datetime.datetime.now(datetime.timezone.utc);run=R/'observations'/t.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 files=[p for p in R.rglob('*') if p.is_file() and not any(n in p.relative_to(R).parts for n in ('observations','media','revisions')) and p.name not in ('CURRENT','QA.json','qa-artifacts.json')]
 d={'startedUtc':t.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'model':'memory receiver; synthetic arrivals; assumed monotonic epoch; no broker or real reboot'},'sourceHashes':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in files},'cases':[]};shutil.copyfile(R/'receiver.py',run/'receiver.py')
 for name,x in json.loads((R/'requests.json').read_text()).items():
  folder=run/name;folder.mkdir();inp=x['rawInput'].encode() if 'rawInput' in x else (json.dumps(x,sort_keys=True)+'\n').encode();(folder/'input.txt').write_bytes(inp)
  start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run([sys.executable,'-B','../receiver.py'],cwd=folder,input=inp,capture_output=True,timeout=5);(folder/'stdout.txt').write_bytes(p.stdout);(folder/'stderr.txt').write_bytes(p.stderr)
  try:o=json.loads(p.stdout)
  except ValueError:o=None
  c={'id':name,'argv':['python3','-B','../receiver.py'],'startedUtc':start,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputSha256':sha(inp),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'observation':o,'outcome':'OBSERVED' if p.returncode==0 else 'REFUSED' if p.returncode==2 else 'EXECUTION_FAILURE'}
  (folder/'command.json').write_text(json.dumps(c,indent=2)+'\n')
  if o:
   for step in o['trace']:(folder/('arrival-'+str(step['arrival'])+'.json')).write_text(json.dumps(step,indent=2)+'\n')
  d['cases'].append(c)
 raw=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw);(run/'artifacts.json').write_text(json.dumps({'files':{p.relative_to(run).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()}},indent=2)+'\n');(R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n');print(raw,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; no mutation')
 else:print('unsupported argument',file=sys.stderr);sys.exit(2)
