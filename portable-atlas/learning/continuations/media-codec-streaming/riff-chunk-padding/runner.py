#!/usr/bin/env python3
import datetime,hashlib,json,pathlib,platform,shutil,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fixtures():
 pcm=struct.pack('<hhh',1000,-1000,32767);fmt=struct.pack('<HHIIHH',1,1,8000,16000,2,16)
 def chunk(name,b):return name+struct.pack('<I',len(b))+b+(b'\0' if len(b)%2 else b'')
 def riff(b):return b'RIFF'+struct.pack('<I',len(b)+4)+b'WAVE'+b
 common=chunk(b'fmt ',fmt);odd=riff(common+chunk(b'JUNK',b'XYZ')+chunk(b'data',pcm))
 d={'base':riff(common+chunk(b'data',pcm)),'odd-junk':odd,'even-junk':riff(common+chunk(b'JUNK',b'WXYZ')+chunk(b'data',pcm)),'riff-oversize':odd[:4]+struct.pack('<I',1000)+odd[8:],'chunk-oversize':odd[:52]+struct.pack('<I',10)+odd[56:],'short-data':odd[:4]+struct.pack('<I',52)+odd[8:-2],'missing-pad':riff(common+b'JUNK'+struct.pack('<I',3)+b'XYZ'+chunk(b'data',pcm))}
 return d
def record():
 run=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 sources=['runner.py','worker.py','checker.py','oracle.json','index.html','preview.py','route.py','test_negative.py','README.md','COVERAGE.md','skills/riff-chunk-padding/SKILL.md']
 d={'startedUtc':utc(),'environment':{'python':platform.python_version(),'platform':platform.system(),'library':'stdlib wave','readframesCap':16,'fixtureReadCapBytes':1025},'sourceHashes':{n:digest(ROOT/n) for n in sources},'cases':[]}
 shutil.copyfile(ROOT/'worker.py',run/'worker.py');shutil.copyfile(ROOT/'oracle.json',run/'oracle.json')
 for name,b in fixtures().items():
  folder=run/name;folder.mkdir();p=folder/'input.wav';p.write_bytes(b);started=utc();argv=['worker.py',name+'/input.wav'];proc=subprocess.run([sys.executable,'-B']+argv,cwd=str(run),capture_output=True,text=True,timeout=10)
  (folder/'stdout.json').write_text(proc.stdout);(folder/'stderr.txt').write_text(proc.stderr)
  d['cases'].append({'id':name,'argv':['python3','-B']+argv,'executablePathNormalized':True,'startedUtc':started,'endedUtc':utc(),'inputSha256':digest(p),'exitCode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'observation':json.loads(proc.stdout)})
 d['endedUtc']=utc();write(run/'result.json',d);(run/'stdout.json').write_text(json.dumps(d,ensure_ascii=False)+'\n');write(run/'command.json',{'argv':['python3','runner.py','--record'],'startedUtc':d['startedUtc'],'endedUtc':d['endedUtc'],'exitCode':0,'stdout':'stdout.json'});write(run/'artifacts.json',{str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in run.rglob('*') if p.is_file()});(ROOT/'CURRENT').write_text(str(run.relative_to(ROOT))+'\n');sys.stdout.write((run/'stdout.json').read_text())
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:
  import checker
  checker.check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS saved evidence read-only')
 else:print('unsupported runner arguments',file=sys.stderr);sys.exit(2)
