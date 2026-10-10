#!/usr/bin/env python3
import copy,datetime,hashlib,json,pathlib,platform,shutil,sqlite3,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parent
BASE=[{'eventId':'e1','op':'upsert','key':'a','price':110,'sourceVersion':2},{'eventId':'e2','op':'delete','key':'b','sourceVersion':2},{'eventId':'e3','op':'upsert','key':'d','price':400,'sourceVersion':1}]
EXTRA={'eventId':'e4','op':'upsert','key':'a','price':120,'sourceVersion':3}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def record():
 run=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True)
 sources=['runner.py','worker.py','checker.py','expectations.json','index.html','preview.py','route.py','test_negative.py','README.md','COVERAGE.md','skills/incremental-corrected-batch/SKILL.md']
 d={'startedUtc':utc(),'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.system(),'connectTimeoutSeconds':.1},'sourceHashes':{n:digest(ROOT/n) for n in sources},'cases':[]}
 shutil.copyfile(ROOT/'worker.py',run/'worker.py');shutil.copyfile(ROOT/'expectations.json',run/'expectations.json');write(run/'initial.json',[['a',100],['b',200],['c',300]])
 collision=copy.deepcopy(BASE[0]);collision['price']=999
 cases=[('replace','replace',[BASE]),('append','append',[BASE]),('keyed','keyed',[BASE,BASE]),('unknown-delete','keyed',[[BASE[0],{'eventId':'e5','op':'delete','key':'z','sourceVersion':1}]]),('duplicate-id','keyed',[[BASE[0],BASE[0]]]),('id-collision','keyed',[BASE,[collision]]),('same-key-order','keyed',[BASE+[EXTRA]]),('same-key-reverse','keyed',[[EXTRA]+BASE])]
 for name,strategy,batches in cases:
  folder=run/name;folder.mkdir();db=folder/'data.sqlite';c=sqlite3.connect(str(db));c.execute('CREATE TABLE items(key TEXT NOT NULL,price INTEGER NOT NULL)');c.execute('CREATE TABLE applied(event_id TEXT PRIMARY KEY,payload_sha TEXT NOT NULL)')
  if strategy=='keyed':c.execute('CREATE UNIQUE INDEX items_key ON items(key)')
  c.executemany('INSERT INTO items VALUES(?,?)',[('a',100),('b',200),('c',300)]);c.commit();c.close();shutil.copyfile(db,folder/'before.sqlite')
  rec={'id':name,'strategy':strategy,'initial':[['a',100],['b',200],['c',300]],'beforeDbSha256':digest(db),'attempts':[]}
  for i,events in enumerate(batches):
   inp=folder/('batch-'+str(i)+'.json');write(inp,events);start=utc();before=digest(db);argv=['worker.py','--db',str(db.relative_to(run)),'--input',str(inp.relative_to(run)),'--strategy',strategy]
   p=subprocess.run([sys.executable,'-B']+argv,cwd=str(run),capture_output=True,text=True,timeout=10);end=utc();(folder/('stdout-'+str(i)+'.json')).write_text(p.stdout);(folder/('stderr-'+str(i)+'.txt')).write_text(p.stderr);shutil.copyfile(db,folder/('after-'+str(i)+'.sqlite'))
   rec['attempts'].append({'index':i,'argv':['python3','-B']+argv,'executablePathNormalized':True,'startedUtc':start,'endedUtc':end,'exitCode':p.returncode,'inputSha256':digest(inp),'beforeDbSha256':before,'afterDbSha256':digest(db),'stdout':p.stdout,'stderr':p.stderr,'observation':json.loads(p.stdout)})
  d['cases'].append(rec)
 c=sqlite3.connect(':memory:');d['compileOptions']=[x[0] for x in c.execute('PRAGMA compile_options')];d['sqliteSourceId']=c.execute('SELECT sqlite_source_id()').fetchone()[0];c.close();d['endedUtc']=utc()
 write(run/'result.json',d);(run/'stdout.json').write_text(json.dumps(d,ensure_ascii=False)+'\n');write(run/'command.json',{'argv':['python3','runner.py','--record'],'startedUtc':d['startedUtc'],'endedUtc':d['endedUtc'],'exitCode':0,'stdout':'stdout.json'})
 write(run/'artifacts.json',{str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in run.rglob('*') if p.is_file()});(ROOT/'CURRENT').write_text(str(run.relative_to(ROOT))+'\n');sys.stdout.write((run/'stdout.json').read_text())
if __name__=='__main__':
 if sys.argv[1:]==['--record']:record()
 elif not sys.argv[1:]:
  import checker
  checker.check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS saved evidence read-only')
 else:print('unsupported runner arguments',file=sys.stderr);sys.exit(2)
