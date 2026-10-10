#!/usr/bin/env python3
import argparse, datetime, hashlib, json, pathlib, platform, sqlite3, struct, sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parent
CASES=[('passive','PASSIVE',True,False,[20]),('full','FULL',True,False,[20]),('truncate','TRUNCATE',True,False,[20]),('begin-only','PASSIVE',False,False,[20]),('rollback','PASSIVE',True,True,[20]),('two-commits','PASSIVE',True,False,[20,30])]
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def record():
    run=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); run.mkdir(parents=True)
    result={'startedUtc':utc(),'environment':{'python':platform.python_version(),'platform':platform.system(),'sqlite':sqlite3.sqlite_version,'connectTimeoutSeconds':0.05},'cases':[],'sourceHashes':{n:sha((ROOT/n).read_bytes()) for n in ['runner.py','checker.py','index.html','preview.py','route.py','test_negative.py','README.md','COVERAGE.md','skills/wal-snapshot-checkpoint/SKILL.md']}}
    for name,mode,established,rollback,values in CASES:
        folder=run/name; folder.mkdir(); db=folder/'closed.sqlite'; w=sqlite3.connect(str(db),isolation_level=None,timeout=.05); r=sqlite3.connect(str(db),isolation_level=None,timeout=.05)
        c={'id':name,'mode':mode,'trace':[]}
        def state(label):
            p=pathlib.Path(str(db)+'-wal'); b=p.read_bytes() if p.exists() else b''
            ps=struct.unpack('>I',b[8:12])[0] if len(b)>=32 else None
            frames=[]
            if ps:
                for off in range(32,len(b),24+ps):
                    h=b[off:off+24]; frames.append({'page':struct.unpack('>I',h[:4])[0],'commitDbPages':struct.unpack('>I',h[4:8])[0]})
            if b: (folder/(label+'.wal')).write_bytes(b)
            return {'exists':p.exists(),'bytes':len(b),'sha256':sha(b),'pageSize':ps,'physicalFrames':frames,'capturedUtc':utc()}
        def sql(role,label,q):
            conn=w if role=='writer' else r; before=conn.in_transaction
            rows=[list(row) for row in conn.execute(q).fetchall()]
            e={'label':label,'connection':role,'sql':q,'rows':rows,'beforeTransaction':before,'afterTransaction':conn.in_transaction,'utc':utc(),'wal':state(label)}; c['trace'].append(e); return rows
        sql('writer','page-size','PRAGMA page_size=4096'); sql('writer','journal','PRAGMA journal_mode=WAL')
        for role in ['writer','reader']:
            sql(role,role+'-auto','PRAGMA wal_autocheckpoint=0'); sql(role,role+'-timeout','PRAGMA busy_timeout=50'); sql(role,role+'-sync','PRAGMA synchronous=FULL')
        sql('writer','create','CREATE TABLE item(id INTEGER PRIMARY KEY, value INTEGER NOT NULL)'); sql('writer','seed','INSERT INTO item VALUES(1,10)'); sql('writer','baseline','PRAGMA wal_checkpoint(TRUNCATE)')
        sql('reader','reader-begin','BEGIN')
        if established: sql('reader','old','SELECT value FROM item WHERE id=1')
        for i,v in enumerate(values):
            sql('writer','writer-begin-'+str(i),'BEGIN IMMEDIATE'); sql('writer','update-'+str(i),'UPDATE item SET value='+str(v)+' WHERE id=1'); sql('writer','writer-end-'+str(i),'ROLLBACK' if rollback else 'COMMIT')
        sql('reader','held','SELECT value FROM item WHERE id=1'); sql('writer','checkpoint-held','PRAGMA wal_checkpoint('+mode+')')
        sql('reader','reader-end','COMMIT'); sql('reader','fresh','SELECT value FROM item WHERE id=1'); sql('writer','checkpoint-ended','PRAGMA wal_checkpoint('+mode+')'); sql('writer','cleanup-truncate','PRAGMA wal_checkpoint(TRUNCATE)')
        c['compileOptions']=sql('writer','compile','PRAGMA compile_options'); c['sourceId']=sql('writer','source-id','SELECT sqlite_source_id()')
        r.close(); w.close(); c['closedDbSha256']=sha(db.read_bytes()); c['closedUtc']=utc(); result['cases'].append(c)
    result['endedUtc']=utc(); write(run/'result.json',result)
    (run/'stdout.ndjson').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in result['cases']))
    write(run/'command.json',{'argv':['python3','runner.py','--record'],'exitCode':0,'stdout':'stdout.ndjson','startedUtc':result['startedUtc'],'endedUtc':result['endedUtc']})
    write(run/'artifacts.json',{str(p.relative_to(run)):{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(run.rglob('*')) if p.is_file()})
    (ROOT/'CURRENT').write_text(str(run.relative_to(ROOT))+'\n'); sys.stdout.write((run/'stdout.ndjson').read_text())
if __name__=='__main__':
    a=argparse.ArgumentParser(); a.add_argument('--record',action='store_true'); args=a.parse_args()
    if args.record: record()
    else:
        import checker
        checker.check(ROOT/(ROOT/'CURRENT').read_text().strip()); print('PASS read-only evidence')
