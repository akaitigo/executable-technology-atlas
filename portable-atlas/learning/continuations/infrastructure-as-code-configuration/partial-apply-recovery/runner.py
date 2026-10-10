"""Explicit recording only. Real child commands mutate one owned store per case."""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCES=('contracts.json','store_cli.py','runner.py','checker.py','route.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-partial-apply-recovery/SKILL.md')
def utc():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def run(folder,label,args):
    started=utc()
    try:
        proc=subprocess.run([sys.executable,'store_cli.py',*args],cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=5)
        result={'command':['python3','store_cli.py',*args],'started_at':started,'ended_at':utc(),'exit':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'timeout_seconds':5}
    except subprocess.TimeoutExpired as error:
        decode=lambda value:value.decode() if isinstance(value,bytes) else value or ''
        result={'command':['python3','store_cli.py',*args],'started_at':started,'ended_at':utc(),'exit':None,'stdout':decode(error.stdout),'stderr':decode(error.stderr),'timeout_seconds':5,'failure':'child timeout; killed and waited by subprocess.run'}
    write(folder/(label+'-command.json'),result)
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true')
    if not p.parse_args().record:raise SystemExit('Read-only default: no store or files changed. Use checker.py; explicit --record only.')
    source={name:sha(ROOT/name) for name in SOURCES}
    token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-partial');folder=ROOT/'observations'/token;folder.mkdir(parents=True)
    contract=json.loads((ROOT/'contracts.json').read_text());write(folder/'contracts.json',contract)
    raw={'run_id':token,'started_at':utc(),'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib','store':'task-owned real JSON file, synthetic resources'},'cases':[],'source_digests':source}
    for c in contract['cases']:
        case=folder/c['id'];case.mkdir();store=case/'store.json';write(store,contract['initial']);write(case/'initial.json',contract['initial']);write(case/'desired.json',contract['desired'])
        rel=lambda path:str(path.relative_to(ROOT))
        base=['--store',rel(store)]
        initial_cmd=run(case,'initial-plan',['plan',*base,'--desired',rel(case/'desired.json')])
        original=json.loads(initial_cmd['stdout'])['plan'];write(case/'original-plan.json',original)
        first=run(case,'first-apply',['apply',*base,'--plan',rel(case/'original-plan.json'),'--fault',c['fault']])
        # Actual file read after child exits. NEVER reset store on failure.
        partial=json.loads(store.read_text());write(case/'partial.json',partial)
        blind=run(case,'blind-replay',['apply',*base,'--plan',rel(case/'original-plan.json')])
        write(case/'after-blind.json',json.loads(store.read_text()))
        refreshed=run(case,'refresh',['refresh',*base]);observed=json.loads(refreshed['stdout'])['state'];write(case/'refreshed.json',observed)
        new_cmd=run(case,'replan',['plan',*base,'--desired',rel(case/'desired.json')]);newplan=json.loads(new_cmd['stdout'])['plan'];write(case/'recovery-plan.json',newplan)
        recovery=run(case,'recovery-apply',['apply',*base,'--plan',rel(case/'recovery-plan.json')]);write(case/'final.json',json.loads(store.read_text()))
        noop_cmd=run(case,'second-plan',['plan',*base,'--desired',rel(case/'desired.json')]);noop=json.loads(noop_cmd['stdout'])['plan'];write(case/'noop-plan.json',noop)
        before=(sha(store),store.stat().st_mtime_ns);again=run(case,'noop-apply',['apply',*base,'--plan',rel(case/'noop-plan.json')]);after=(sha(store),store.stat().st_mtime_ns)
        item={'id':c['id'],'fault':c['fault'],'first_exit':first['exit'],'partial':partial,'blind_exit':blind['exit'],'after_blind':json.loads((case/'after-blind.json').read_text()),'refreshed':observed,'recovery_plan':newplan,'recovery_exit':recovery['exit'],'final':json.loads((case/'final.json').read_text()),'noop_plan':noop,'noop_exit':again['exit'],'noop_store_hash_mtime_unchanged':before==after,'trace':[json.loads(line) for line in first['stdout'].splitlines()]}
        raw['cases'].append(item)
    raw['ended_at']=utc();write(folder/'raw.json',raw)
    write(folder/'artifact-index.json',{'artifacts':{str(path.relative_to(folder)):{'sha256':sha(path),'bytes':path.stat().st_size} for path in sorted(folder.rglob('*')) if path.is_file()}})
    (ROOT/'observation-data.js').write_text('window.PARTIAL_OBSERVATION = '+json.dumps({'raw':raw,'contracts':contract},ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':token,'cases':len(raw['cases']),'recorded':True}))
if __name__=='__main__':main()
