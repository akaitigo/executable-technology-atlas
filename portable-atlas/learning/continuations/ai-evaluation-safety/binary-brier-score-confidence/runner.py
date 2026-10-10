import sys,pathlib,json,datetime,platform,hashlib
sys.dont_write_bytecode=True
from execute import execute
R=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record():
 t=datetime.datetime.now(datetime.timezone.utc);run=R/'observations'/t.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True);d={'startedUtc':t.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'dependencies':'stdlib only; no sklearn runtime'},'sourceHashes':{p.relative_to(R).as_posix():sha(p) for p in R.rglob('*') if p.is_file() and not any(n in p.relative_to(R).parts for n in ('observations','media','revisions')) and p.name not in ['CURRENT','QA.json','qa-artifacts.json']},'cases':[]}
 for n,x in json.loads((R/'requests.json').read_text()).items():
  raw=x['rawInput'] if 'rawInput' in x else json.dumps(x,sort_keys=True)+'\n';c=execute(raw);c['id']=n;f=run/n;f.mkdir();
  for k,v in [('input.txt',raw),('stdout.txt',c['stdout']),('stderr.txt',c['stderr']),('audit-stdout.txt',c['auditStdout']),('audit-stderr.txt',c['auditStderr'])]:(f/k).write_text(v)
  (f/'command.json').write_text(json.dumps(c,indent=2)+'\n');(f/'audit-command.json').write_text(json.dumps(c['auditCommand'],indent=2)+'\n');d['cases'].append(c)
 s=json.dumps(d,indent=2)+'\n';(run/'result.json').write_text(s);(run/'stdout.json').write_text(s);(run/'artifacts.json').write_text(json.dumps({'files':{p.relative_to(run).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()}},indent=2)+'\n');(R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n');print(s,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; no mutation')
 else:sys.exit(2)
