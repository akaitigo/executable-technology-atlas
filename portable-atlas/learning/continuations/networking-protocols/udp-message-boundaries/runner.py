"""Only --record opens UDP sockets and writes a fresh run; preserve failures."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = ('contracts.json','observe_udp.py','policies.py','runner.py','checker.py','README.md','sources.json','index.html','app.js','styles.css','route.py','skills/atlas-udp-message-boundaries/SKILL.md')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record:
        raise SystemExit('Read-only default: no sockets or files changed. Use checker.py; only explicit --record records.')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-udp')
    folder=ROOT/'observations'/run_id; folder.mkdir(parents=True)
    source_digests={name: sha(ROOT/name) for name in SOURCES}
    input_bytes=(ROOT/'contracts.json').read_bytes(); (folder/'contracts.json').write_bytes(input_bytes)
    started=datetime.now(timezone.utc).isoformat()
    args=[sys.executable,'observe_udp.py']
    try:
        process=subprocess.run(args, cwd=ROOT, env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=8)
        command={'command':['python3','observe_udp.py'],'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'exit':process.returncode,'stdout':process.stdout,'stderr':process.stderr,'outer_timeout_seconds':8}
    except subprocess.TimeoutExpired as error:
        command={'command':['python3','observe_udp.py'],'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'exit':None,'outer_timeout_seconds':8,'failure':'outer timeout; child killed and waited by subprocess.run','stdout':(error.stdout or b'').decode() if isinstance(error.stdout,bytes) else error.stdout,'stderr':(error.stderr or b'').decode() if isinstance(error.stderr,bytes) else error.stderr}
    write(folder/'command.json',command)
    raw=json.loads(command['stdout']) if command['stdout'] else None
    if raw: write(folder/'raw.json',raw)
    write(folder/'manifest.json',{'run_id':run_id,'source_digests':source_digests,'artifacts':{p.name: {'sha256':sha(p),'bytes':p.stat().st_size} for p in folder.iterdir() if p.is_file()}})
    if command['exit']==0:
        payload={'run_id':run_id,'raw':raw,'contracts':json.loads(input_bytes),'source_digests':source_digests}
        (ROOT/'observation-data.js').write_text('window.UDP_OBSERVATION = '+json.dumps(payload,ensure_ascii=False)+';\n')
    print(json.dumps({'run_id':run_id,'exit':command['exit'],'pointer_updated':command['exit']==0},ensure_ascii=False))
    return 0 if command['exit']==0 else 1

if __name__=='__main__':
    raise SystemExit(main())
