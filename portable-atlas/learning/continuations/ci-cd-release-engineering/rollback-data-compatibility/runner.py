#!/usr/bin/env python3
import datetime,hashlib,json,pathlib,platform,shutil,sqlite3,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parent
CREATE='CREATE TABLE person(id INTEGER PRIMARY KEY, name TEXT NOT NULL)'
SEED="INSERT INTO person VALUES(1,'Ada')"
MIGRATIONS={'v1':[],'additive':["ALTER TABLE person ADD COLUMN display_name TEXT NOT NULL DEFAULT ''","UPDATE person SET display_name=name || '-v2'"],'rename':['ALTER TABLE person RENAME COLUMN name TO display_name',"UPDATE person SET display_name=display_name || '-v2'"]}
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def observe(db):
    c=sqlite3.connect(db.resolve().as_uri()+'?mode=ro&immutable=1',uri=True);c.execute('PRAGMA query_only=ON')
    out={'schemaSql':c.execute("SELECT sql FROM sqlite_schema WHERE name='person'").fetchone()[0],'columns':[list(x) for x in c.execute('PRAGMA table_info(person)')],'rows':[list(x) for x in c.execute('SELECT * FROM person ORDER BY id')],'dbSha256':sha(db.read_bytes())};c.close();return out

def record():
    run=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');run.mkdir(parents=True);(run/'store').mkdir()
    sources=['runner.py','checker.py','app_v1.py','app_v2.py','health.py','compatibility.json','index.html','preview.py','route.py','test_negative.py','README.md','COVERAGE.md','skills/rollback-data-compatibility/SKILL.md']
    d={'startedUtc':utc(),'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.system(),'subprocessExecutable':pathlib.Path(sys.executable).name,'executablePathNormalized':True},'sourceHashes':{n:sha((ROOT/n).read_bytes()) for n in sources},'matrix':[],'releases':[],'artifacts':{}}
    shutil.copyfile(ROOT/'compatibility.json',run/'inputs.json');shutil.copyfile(ROOT/'health.py',run/'health.py')
    for version in ['v1','v2']:
        b=(ROOT/('app_'+version+'.py')).read_bytes();digest=sha(b);name='store/'+digest+'.py';(run/name).write_bytes(b);d['artifacts'][version]={'path':name,'sha256':digest,'bytes':len(b)}
    def command(label,argv):
        started=utc();p=subprocess.run([sys.executable,'-B']+argv,cwd=str(run),capture_output=True,text=True,timeout=10)
        return {'label':label,'argv':['python3','-B']+argv,'executablePathNormalized':True,'startedUtc':started,'endedUtc':utc(),'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'parsed':json.loads(p.stdout)}
    def sqls(db,queries):
        c=sqlite3.connect(str(db),isolation_level=None,timeout=.1);trace=[]
        for q in queries:
            start=utc();rows=[list(x) for x in c.execute(q)];trace.append({'sql':q,'rows':rows,'exitCode':0,'startedUtc':start,'endedUtc':utc()})
        c.close();return trace
    for schema in ['v1','additive','rename']:
        folder=run/('matrix-'+schema);folder.mkdir();db=folder/'data.sqlite';trace=sqls(db,[CREATE,SEED]+MIGRATIONS[schema]);snapshot=observe(db)
        reads={v:command(v,[d['artifacts'][v]['path'],str(db.relative_to(run))]) for v in ['v1','v2']}
        d['matrix'].append({'schema':schema,'sqlTrace':trace,'snapshot':snapshot,'reads':reads})
    for schema in ['additive','rename']:
        folder=run/('release-'+schema);folder.mkdir();db=folder/'data.sqlite';seed=sqls(db,[CREATE,SEED]);shutil.copyfile(db,folder/'before.sqlite');before=observe(db);v1=d['artifacts']['v1']['sha256'];v2=d['artifacts']['v2']['sha256']
        pointer=folder/'active.json';write(pointer,{'sha256':v1});shutil.copyfile(pointer,folder/'pointer-before.json')
        trace=[{'event':'before','active':json.loads(pointer.read_text()),'database':before}]
        migration=sqls(db,MIGRATIONS[schema]);shutil.copyfile(db,folder/'migrated.sqlite');migrated=observe(db);trace.append({'event':'migration','sqlTrace':migration,'database':migrated})
        write(pointer,{'sha256':v2});shutil.copyfile(pointer,folder/'pointer-promoted.json');trace.append({'event':'promotion','active':json.loads(pointer.read_text())})
        read2=command('v2-read',[d['artifacts']['v2']['path'],str(db.relative_to(run))]);trace.append({'event':'v2-read','command':read2})
        health=command('synthetic-health-failure',['health.py']);trace.append({'event':'synthetic-health-failure','command':health})
        assert sha((run/d['artifacts']['v1']['path']).read_bytes())==v1
        write(pointer,{'sha256':v1});shutil.copyfile(pointer,folder/'pointer-restored.json');trace.append({'event':'artifact-rollback','active':json.loads(pointer.read_text()),'databaseSha256':sha(db.read_bytes()),'savedBytesVerified':True})
        active=json.loads(pointer.read_text())['sha256'];read1=command('v1-read',['store/'+active+'.py',str(db.relative_to(run))]);trace.append({'event':'v1-read','command':read1})
        shutil.copyfile(db,folder/'after.sqlite');after=observe(db);trace.append({'event':'after','active':json.loads(pointer.read_text()),'database':after})
        d['releases'].append({'schema':schema,'seedTrace':seed,'trace':trace,'artifactRestored':True,'databaseRestored':False,'v1ReadExit':read1['exitCode'],'v1ReadSucceeded':read1['exitCode']==0})
    c=sqlite3.connect(':memory:');d['compileOptions']=[x[0] for x in c.execute('PRAGMA compile_options')];d['sourceId']=c.execute('SELECT sqlite_source_id()').fetchone()[0];c.close();d['endedUtc']=utc()
    write(run/'result.json',d);(run/'stdout.json').write_text(json.dumps(d,ensure_ascii=False)+'\n');write(run/'command.json',{'argv':['python3','runner.py','--record'],'startedUtc':d['startedUtc'],'endedUtc':d['endedUtc'],'exitCode':0,'stdout':'stdout.json'})
    write(run/'artifacts.json',{str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in run.rglob('*') if p.is_file()})
    (ROOT/'CURRENT').write_text(str(run.relative_to(ROOT))+'\n');sys.stdout.write((run/'stdout.json').read_text())
if __name__=='__main__':
    if sys.argv[1:]==['--record']:record()
    elif not sys.argv[1:]:
        import checker
        checker.check(ROOT/(ROOT/'CURRENT').read_text().strip());print('PASS read-only evidence')
    else:print('unsupported runner arguments',file=sys.stderr);sys.exit(2)
