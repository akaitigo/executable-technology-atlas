import argparse,hashlib,json,os,platform,subprocess,sys,tempfile,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent
SOURCES=('contracts.json','expected-states.json','experiment.py','runner.py','checker.py','route.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-key-generation-cas/SKILL.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record:raise SystemExit('Read-only default. No files changed; use checker.py. Explicit --record only.')
    source={n:sha(ROOT/n) for n in SOURCES};token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-cas');out=ROOT/'observations'/token;out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='atlas-generation-cas-') as scratch:
        started=datetime.now(timezone.utc).isoformat()
        try:
            r=subprocess.run([sys.executable,'experiment.py',scratch],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=10)
            command={'argv':['python3','experiment.py','<owned-temporary-directory>'],'started':started,'ended':datetime.now(timezone.utc).isoformat(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
        except subprocess.TimeoutExpired as e:
            dec=lambda v:v.decode() if isinstance(v,bytes) else v or ''
            command={'argv':['python3','experiment.py','<owned-temporary-directory>'],'exit':None,'stdout':dec(e.stdout),'stderr':dec(e.stderr),'failure':'timeout; child killed and waited'}
        write(out/'command.json',command)
        for db in Path(scratch).glob('*.sqlite'):shutil.copyfile(db,out/db.name)
        if command['exit']!=0:raise SystemExit('Failure and partial databases retained; pointer not updated')
        raw={'run_id':token,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':source,**json.loads(command['stdout'])}
        write(out/'raw.json',raw)
        for n in ('contracts.json','expected-states.json'):(out/n).write_bytes((ROOT/n).read_bytes())
        write(out/'artifact-index.json',{'artifacts':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()}})
        (ROOT/'observation-data.js').write_text('window.CAS_OBSERVATION = '+json.dumps(raw,ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':token,'normal_experiments':4,'expected_refusals':6,'expected_sql_errors':1,'owned_temporary_directory_removed':True}))
if __name__=='__main__':main()
