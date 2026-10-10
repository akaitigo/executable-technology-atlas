import argparse,hashlib,json,platform,sqlite3,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE=[[3,'A',2,5],[2,'A',1,20],[1,'A',1,10],[5,'B',2,None],[4,'B',1,7]]
SCHEMA='CREATE TABLE samples(id INTEGER NOT NULL UNIQUE, part TEXT, sort_key INTEGER, amount INTEGER)'
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def cases():
    rows={'peers':BASE,'null-sort':[[3,'A',1,5],[2,'A',None,20],[1,'A',None,10]],'null-amounts':[[1,'A',1,None],[2,'A',1,None],[3,'A',2,None]],'negative-amounts':[[1,'A',1,10],[2,'A',1,-10],[3,'A',2,4]],'no-peers':[[1,'A',1,10],[2,'A',2,20],[3,'A',3,5]],'singleton':[[9,'Z',None,None]],'empty-partition':BASE,'null-partition':[[3,'A',1,9],[2,None,1,7],[1,None,1,5]],'negative-sort':[[3,'A',0,5],[2,'A',-1,20],[1,'A',-1,10]],'range-tie-breaker':BASE,'invalid-start-end':BASE,'invalid-negative':BASE}
    return {k:{'rows':v,'filter':'missing' if k=='empty-partition' else None,'modes':[k] if k.startswith('invalid') else ['range-default','rows-explicit','range-explicit']+(['range-with-id'] if k=='range-tie-breaker' else [])} for k,v in rows.items()}
def record():
    ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'observations'/ident;folder.mkdir(parents=True);started=now();runs=[]
    for key,request in cases().items():
        case=folder/key;case.mkdir();write(case/'input.json',request);db=case/'fixture.sqlite3';connection=sqlite3.connect(db)
        try:connection.execute(SCHEMA);connection.executemany('INSERT INTO samples VALUES (?,?,?,?)',request['rows']);connection.commit()
        finally:connection.close()
        write(case/'database-created.json',{'schema':SCHEMA,'insert_sql':'INSERT INTO samples VALUES (?,?,?,?)','rows_in_insertion_order':request['rows'],'db_digest':sha(db.read_bytes()),'completed_at':now()})
        stdin=json.dumps({'modes':request['modes'],'filter':request['filter']});began=now();p=subprocess.run([sys.executable,'observe.py',str(db.relative_to(ROOT)),str((case/'result.json').relative_to(ROOT))],cwd=ROOT,input=stdin,text=True,capture_output=True)
        command={'argv':['python3','observe.py',str(db.relative_to(ROOT)),str((case/'result.json').relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdin':stdin,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode}
        for s in ('stdin','stdout','stderr'):command[s+'_digest']=sha(command[s].encode())
        write(case/'command.json',command);write(case/'trace.json',[json.loads(line) for line in p.stdout.splitlines()]);runs.append({'id':key,'exit_code':p.returncode,'queries':len(request['modes'])})
    names=['observe.py','runner.py','checker.py','test_negative.py','queries.json','index.html','preview.py','README.md','sources.json','coverage.json','skills/atlas-sql-window-frames-peers/SKILL.md','skills/atlas-sql-window-frames-peers/route.py']
    write(folder/'observation.json',{'execution_id':ident,'started_at':started,'completed_at':now(),'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'source_bindings':{n:sha((ROOT/n).read_bytes()) for n in names},'runs':runs,'continuation_of':'relational-database-sql LEARNING_PATH experiment 2','original_subject_changed':False,'external_DB':False,'external_services':0})
    began=now();p=subprocess.run([sys.executable,'checker.py','--oracle',str(folder.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr)
    write(folder/'oracle.json',json.loads(p.stdout));write(folder/'oracle-command.json',{'argv':['python3','checker.py','--oracle',str(folder.relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'stdout_digest':sha(p.stdout.encode()),'stderr_digest':sha(p.stderr.encode())})
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():{'digest':sha(p.read_bytes()),'size':p.stat().st_size} for p in folder.rglob('*') if p.is_file()});write(ROOT/'current.json',{'directory':str(folder.relative_to(ROOT))});print(json.dumps({'directory':str(folder.relative_to(ROOT)),'cases':len(runs),'queries':sum(r['queries'] for r in runs)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    if args.record:record()
    else:raise SystemExit(subprocess.call([sys.executable,str(ROOT/'checker.py')]))
