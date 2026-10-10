"""Explicit --record regenerates observations; default never writes."""
import argparse
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from experiment import CASES
ROOT=Path(__file__).resolve().parent

def sha(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record: raise SystemExit('No files changed. Use checker.py for read-only checks; --record for explicit new observation.')
    token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-cdc')
    folder=ROOT/'observations'/token
    folder.mkdir(parents=True)
    metadata={'execution_id':token,'started_at':now(),'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'os':platform.system(),'os_release':platform.release(),'machine':platform.machine(),'journal_mode':'DELETE'},'scope':'synthetic SQLite source/outbox polling and finite consumer; no WAL CDC/Kafka', 'source_digests':{p:sha((ROOT/p).read_bytes()) for p in ('experiment.py','runner.py','checker.py','app.js','index.html','styles.css','sources.json','README.md','skills/atlas-event-streaming-cdc/SKILL.md','quick_validate.py')}}
    commands=[]
    for name,data in CASES.items():
        case=folder/name
        case.mkdir()
        write(case/'input.json',data)
        start=now()
        result=subprocess.run([sys.executable,'experiment.py',str(case)],cwd=ROOT,capture_output=True,text=True,timeout=20,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        command={'case':name,'started_at':start,'completed_at':now(),'command':['python3','experiment.py',f'observations/{token}/{name}'],'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr.replace(str(ROOT),'<module>')}
        command['input_digest']=sha((case/'input.json').read_bytes())
        commands.append(command)
        write(folder/'commands.json',commands)
        if result.returncode: raise SystemExit('experiment failed; commands retained')
    oracle_command=subprocess.run([sys.executable,'checker.py','--oracle-json',str(folder)],cwd=ROOT,capture_output=True,text=True,timeout=20,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    write(folder/'oracle-command.json',{'command':['python3','checker.py','--oracle-json',f'observations/{token}'],'exit_code':oracle_command.returncode,'stdout':oracle_command.stdout,'stderr':oracle_command.stderr.replace(str(ROOT),'<module>')})
    if oracle_command.returncode: raise SystemExit('oracle failed; evidence retained')
    oracle=json.loads(oracle_command.stdout)
    write(folder/'oracle-report.json',oracle)
    if not all(x['matches_expected'] for x in oracle['rows']): raise SystemExit('oracle mismatch; prior UI retained')
    metadata['completed_at']=now()
    write(folder/'run.json',metadata)
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()})
    (ROOT/'observation-data.js').write_text('window.CDC_OBSERVATION = '+json.dumps({'directory':f'observations/{token}','run':metadata,'oracle':oracle,'inputs':CASES,'timelines':{name:[json.loads(x) for x in (folder/name/'timeline.jsonl').read_text().splitlines()] for name in CASES}},ensure_ascii=False)+';\n')
    print(json.dumps({'execution_id':token,'cases':len(CASES),'matches':True}))
if __name__=='__main__': main()
