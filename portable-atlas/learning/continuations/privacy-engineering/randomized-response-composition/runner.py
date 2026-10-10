import argparse,hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES=('contracts.json','expected-distributions.json','calculate.py','runner.py','checker.py','route.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-randomized-response-composition/SKILL.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true')
    if not p.parse_args().record:raise SystemExit('Read-only default. No files changed; use checker.py. Explicit --record only.')
    source={n:sha(ROOT/n) for n in SOURCES};token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-rr');out=ROOT/'observations'/token;out.mkdir(parents=True);start=datetime.now(timezone.utc).isoformat()
    try:
        r=subprocess.run([sys.executable,'calculate.py'],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=5)
        cmd={'argv':['python3','calculate.py'],'started':start,'ended':datetime.now(timezone.utc).isoformat(),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    except subprocess.TimeoutExpired as e:
        dec=lambda v:v.decode() if isinstance(v,bytes) else v or ''
        cmd={'argv':['python3','calculate.py'],'exit':None,'stdout':dec(e.stdout),'stderr':dec(e.stderr),'failure':'timeout; child killed and waited'}
    write(out/'command.json',cmd)
    if cmd['exit']!=0:raise SystemExit('Failure retained; pointer not updated')
    raw={'run_id':token,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':source,**json.loads(cmd['stdout'])}
    write(out/'raw.json',raw)
    for n in ('contracts.json','expected-distributions.json'):(out/n).write_bytes((ROOT/n).read_bytes())
    write(out/'artifact-index.json',{'artifacts':{f.name:{'sha256':sha(f),'bytes':f.stat().st_size} for f in out.iterdir() if f.is_file()}})
    (ROOT/'observation-data.js').write_text('window.RR_OBSERVATION = '+json.dumps(raw,ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':token,'accepted_calculations':2,'expected_refusals':5,'random_samples':0}))
if __name__=='__main__':main()
