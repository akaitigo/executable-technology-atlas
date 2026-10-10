import pathlib,json,hashlib,subprocess,datetime,platform,sys
R=pathlib.Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def record():
 started=datetime.datetime.now(datetime.timezone.utc)
 run=R/'observations'/started.strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 fixtures=json.loads((R/'fixtures.json').read_text())
 source=[p for p in R.rglob('*') if p.is_file() and not any(v in p.relative_to(R).parts for v in ('observations','media','revisions')) and p.name not in ('CURRENT','QA.json','qa-artifacts.json')]
 result={'startedUtc':started.isoformat(),'environment':{'python':platform.python_version(),'platform':platform.system(),'modelTime':'abstract integer ticks, not elapsed real time'},'sourceHashes':{p.relative_to(R).as_posix():sha(p.read_bytes()) for p in source},'cases':[]}
 for name,x in fixtures.items():
  d=run/name;d.mkdir();inp=(json.dumps(x,sort_keys=True)+'\n').encode();(d/'input.json').write_bytes(inp)
  begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
  z=subprocess.run([sys.executable,'-B',str(R/'worker.py')],input=inp,capture_output=True)
  (d/'stdout.json').write_bytes(z.stdout);(d/'stderr.txt').write_bytes(z.stderr)
  result['cases'].append({'id':name,'argv':['python3','-B','worker.py'],'stdin':name+'/input.json','inputSha256':sha(inp),'startedUtc':begin,'endedUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exitCode':z.returncode,'stdout':z.stdout.decode(),'stderr':z.stderr.decode(),'result':json.loads(z.stdout)})
 for name in ('worker.py','oracle.json','fixtures.json'):(run/name).write_bytes((R/name).read_bytes())
 raw=json.dumps(result,ensure_ascii=False,indent=2)+'\n';(run/'result.json').write_text(raw);(run/'stdout.json').write_text(raw)
 files={p.relative_to(run).as_posix():{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in run.rglob('*') if p.is_file()}
 (run/'artifacts.json').write_text(json.dumps({'files':files},indent=2)+'\n')
 (R/'CURRENT').write_text(run.relative_to(R).as_posix()+'\n')
 print(raw,end='')
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:print('Saved evidence '+(R/'CURRENT').read_text().strip()+'; use checker.py (read-only)')
 else:print('unsupported argument',file=sys.stderr);sys.exit(2)
