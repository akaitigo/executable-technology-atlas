import argparse,hashlib,json,os,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES=('contracts.json','calculate.py','runner.py','checker.py','route.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-small-sample-interval-coverage/SKILL.md')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record:raise SystemExit('Read-only default. No files changed; use checker.py. Explicit --record only.')
    source={name:sha(ROOT/name) for name in SOURCES};token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-wald');folder=ROOT/'observations'/token;folder.mkdir(parents=True)
    started=utc()
    try:
        proc=subprocess.run([sys.executable,'calculate.py'],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=5)
        command={'command':['python3','calculate.py'],'started_at':started,'ended_at':utc(),'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'timeout_seconds':5}
    except subprocess.TimeoutExpired as error:
        decode=lambda value:value.decode() if isinstance(value,bytes) else value or ''
        command={'command':['python3','calculate.py'],'started_at':started,'ended_at':utc(),'exit':None,'stdout':decode(error.stdout),'stderr':decode(error.stderr),'failure':'child timeout; killed and waited','timeout_seconds':5}
    write(folder/'command.json',command)
    if command['exit']!=0:raise SystemExit('Execution failure retained; pointer not updated')
    raw={'run_id':token,'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib'},'source_digests':source,**json.loads(command['stdout'])}
    write(folder/'raw.json',raw);(folder/'contracts.json').write_bytes((ROOT/'contracts.json').read_bytes())
    write(folder/'artifact-index.json',{'artifacts':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in folder.iterdir() if p.is_file()}})
    (ROOT/'observation-data.js').write_text('window.WALD_OBSERVATION = '+json.dumps(raw,ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':token,'accepted_calculations':3,'expected_refusals':7,'random_samples':0}))
if __name__=='__main__':main()
