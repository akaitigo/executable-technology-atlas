import argparse,hashlib,json,os,platform,subprocess,sys,tempfile,shutil
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES=('contracts.json','expected-table.json','fixtures/alpha.txt','fixtures/beta.txt','experiment.py','runner.py','checker.py','route.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-resource-scope-enforcement/SKILL.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true')
    if not p.parse_args().record:raise SystemExit('Read-only default. No files changed; use checker.py. Explicit --record only.')
    source={n:sha(ROOT/n) for n in SOURCES};token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-scope');out=ROOT/'observations'/token;out.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='atlas-resource-scope-') as scratch:
        for name in ('alpha.txt','beta.txt'):shutil.copyfile(ROOT/'fixtures'/name,Path(scratch)/name)
        start=datetime.now(timezone.utc).isoformat()
        try:
            r=subprocess.run([sys.executable,'experiment.py',scratch],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=5)
            cmd={'argv':['python3','experiment.py','<owned-fixture-directory>'],'started':start,'ended':datetime.now(timezone.utc).isoformat(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
        except subprocess.TimeoutExpired as e:
            dec=lambda v:v.decode() if isinstance(v,bytes) else v or ''
            cmd={'argv':['python3','experiment.py','<owned-fixture-directory>'],'exit':None,'stdout':dec(e.stdout),'stderr':dec(e.stderr),'failure':'timeout; child killed and waited'}
        write(out/'command.json',cmd)
        if cmd['exit']!=0:raise SystemExit('Failure retained; pointer not updated')
        raw={'run_id':token,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':source,**json.loads(cmd['stdout'])}
        write(out/'raw.json',raw)
        for n in ('contracts.json','expected-table.json'):(out/n).write_bytes((ROOT/n).read_bytes())
        for n in ('alpha.txt','beta.txt'):shutil.copyfile(Path(scratch)/n,out/n)
        write(out/'artifact-index.json',{'artifacts':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size} for f in out.iterdir() if f.is_file()}})
        (ROOT/'observation-data.js').write_text('window.SCOPE_OBSERVATION = '+json.dumps(raw,ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':token,'normal_comparisons':24,'expected_refusals':6,'owned_fixture_tmp_removed':True}))
if __name__=='__main__':main()
