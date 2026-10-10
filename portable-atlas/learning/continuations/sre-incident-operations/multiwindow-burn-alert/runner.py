#!/usr/bin/env python3
import datetime,hashlib,json,pathlib,platform,shutil,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fixtures():
 def events(ids,bad=()):return [{'id':i,'tick':i,'status':'bad' if i in bad else 'good'} for i in ids]
 d={'normal':events(range(100)),'spike':events(range(100),range(96,100)),'sustained':events(range(100),list(range(18))+[90,91]),'recovered':events(range(100),range(20)),'boundaries':events([89,90,99,100],[89,90,99,100]),'short-empty':events(range(90)),'all-outside':events(range(100,200)),'empty':[],'unknown-status':events(range(100)),'duplicate-id':events(range(100)),'boolean-tick':[{'id':0,'tick':True,'status':'good'}]}
 d['unknown-status'][0]['status']='timeout';d['duplicate-id'].append(dict(d['duplicate-id'][0]));return d
def record():
 run=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 sources=['runner.py','worker.py','checker.py','expected.json','index.html','preview.py','route.py','test_negative.py','README.md','COVERAGE.md','skills/multiwindow-burn-alert/SKILL.md']
 d={'startedUtc':utc(),'environment':{'python':platform.python_version(),'platform':platform.system(),'arithmetic':'fractions.Fraction','events':'synthetic ticks; no real clock'},'sourceHashes':{n:digest(ROOT/n) for n in sources},'cases':[]}
 shutil.copyfile(ROOT/'worker.py',run/'worker.py');shutil.copyfile(ROOT/'expected.json',run/'expected.json')
 for name,events in fixtures().items():
  folder=run/name;folder.mkdir();write(folder/'input.json',events);started=utc();argv=['worker.py',name+'/input.json'];p=subprocess.run([sys.executable,'-B']+argv,cwd=str(run),capture_output=True,text=True,timeout=10)
  (folder/'stdout.json').write_text(p.stdout);(folder/'stderr.txt').write_text(p.stderr)
  d['cases'].append({'id':name,'argv':['python3','-B']+argv,'executablePathNormalized':True,'startedUtc':started,'endedUtc':utc(),'inputSha256':digest(folder/'input.json'),'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'observation':json.loads(p.stdout)})
 d['endedUtc']=utc();write(run/'result.json',d);(run/'stdout.json').write_text(json.dumps(d,ensure_ascii=False)+'\n');write(run/'command.json',{'argv':['python3','runner.py','--record'],'startedUtc':d['startedUtc'],'endedUtc':d['endedUtc'],'exitCode':0,'stdout':'stdout.json'})
 write(run/'artifacts.json',{str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in run.rglob('*') if p.is_file()});(ROOT/'CURRENT').write_text(str(run.relative_to(ROOT))+'\n');sys.stdout.write((run/'stdout.json').read_text())
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:
  import checker
  checker.check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS saved evidence read-only')
 else:print('unsupported runner arguments',file=sys.stderr);sys.exit(2)
