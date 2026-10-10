import argparse,copy,hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent;M0=1700000000000000000;M1=M0+10000000000
G={'object.bin':{'action':'compile','deps':['source.txt','suffix.txt']},'bundle.bin':{'action':'package','deps':['header.txt','object.bin']}}
BASE={'mode':'content','toolchain':'toy-1','files':{'source.txt':'hello','suffix.txt':'!\n','header.txt':'bundle\n'},'mtime':{'source.txt':M0,'suffix.txt':M0,'header.txt':M0},'graph':G}
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def cases():
    b=copy.deepcopy(BASE);weak=b|{'mode':'mtime-only'};world=b|{'files':b['files']|{'source.txt':'world'}};touch=b|{'mtime':b['mtime']|{'source.txt':M1}};missing=b|{'files':{'source.txt':'hello','header.txt':'bundle\n'}};cycle=copy.deepcopy(b);cycle['graph']['object.bin']['deps']=['bundle.bin','suffix.txt'];action=copy.deepcopy(b);action['graph']['object.bin']['action']='unknown'
    return {'cold':[b],'content-rerun':[b,b],'source-same-mtime-content':[b,world],'source-same-mtime-weak':[weak,world|{'mode':'mtime-only'}],'dependency-same-mtime':[b,b|{'files':b['files']|{'suffix.txt':'?\n'}}],'toolchain-change':[b,b|{'toolchain':'toy-2'}],'touch-only-content':[b,touch],'touch-only-weak':[weak,touch|{'mode':'mtime-only'}],'clean-rebuild':[b,b|{'isolated':True}],'empty-source':[b|{'files':b['files']|{'source.txt':''}}],'missing-dependency':[missing],'cycle':[cycle],'unsupported-action':[action]}
def record():
    ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'observations'/ident;folder.mkdir(parents=True);started=now();runs=[]
    for key,steps in cases().items():
        case=folder/key;case.mkdir();write(case/'input.json',steps);attempts=[]
        for i,step in enumerate(steps,1):
            work=case/(f'work-{i}' if step.get('isolated') else 'work');inputs=work/'inputs';inputs.mkdir(parents=True,exist_ok=True)
            for name,value in step['files'].items():
                p=inputs/name;p.write_bytes(value.encode());os.utime(p,ns=(step['mtime'][name],step['mtime'][name]))
            snapshot=case/f'attempt-{i}';snapshot.mkdir();write(snapshot/'physical-inputs.json',{p.name:{'hex':p.read_bytes().hex(),'digest':sha(p.read_bytes()),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for p in inputs.iterdir()})
            request={k:step[k] for k in ('mode','toolchain','graph')};stdin=json.dumps(request);began=now();p=subprocess.run([sys.executable,'builder.py',str(work.relative_to(ROOT)),str((snapshot/'result.json').relative_to(ROOT))],cwd=ROOT,input=stdin,text=True,capture_output=True)
            command={'argv':['python3','builder.py',str(work.relative_to(ROOT)),str((snapshot/'result.json').relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdin':stdin,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode}
            for s in ('stdin','stdout','stderr'):command[s+'_digest']=sha(command[s].encode())
            write(snapshot/'command.json',command);write(snapshot/'trace.json',[json.loads(line) for line in p.stdout.splitlines()])
            if (work/'outputs').exists():
                for source in (work/'outputs').iterdir():(snapshot/source.name).write_bytes(source.read_bytes())
            attempts.append({'attempt':i,'exit_code':p.returncode})
        runs.append({'id':key,'attempts':attempts})
    names=['builder.py','runner.py','checker.py','test_negative.py','index.html','preview.py','README.md','sources.json','coverage.json','skills/atlas-build-toolchain-package-engineering/SKILL.md','skills/atlas-build-toolchain-package-engineering/route.py']
    write(folder/'observation.json',{'execution_id':ident,'started_at':started,'completed_at':now(),'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'source_bindings':{n:sha((ROOT/n).read_bytes()) for n in names},'runs':runs,'tiny_local_toolchain':True,'external_package_install':False,'build_publish':False,'production_reproducibility_guarantee':False,'mtime_scope':'only module-owned fixture inputs/outputs','external_services':0})
    began=now();p=subprocess.run([sys.executable,'checker.py','--oracle',str(folder.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr)
    write(folder/'oracle.json',json.loads(p.stdout));write(folder/'oracle-command.json',{'argv':['python3','checker.py','--oracle',str(folder.relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'stdout_digest':sha(p.stdout.encode()),'stderr_digest':sha(p.stderr.encode())})
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():{'digest':sha(p.read_bytes()),'size':p.stat().st_size} for p in folder.rglob('*') if p.is_file()});write(ROOT/'current.json',{'directory':str(folder.relative_to(ROOT))});print(json.dumps({'directory':str(folder.relative_to(ROOT)),'cases':len(runs),'attempts':sum(len(r['attempts']) for r in runs)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    if args.record:record()
    else:raise SystemExit(subprocess.call([sys.executable,str(ROOT/'checker.py')]))
