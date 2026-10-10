"""Atlas: mandatory actual priority guard before the finite Bayes execution."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent
gate=BASE/'verification/resource-before-calculation.json'
if not gate.exists() or not json.loads(gate.read_text())['allowed']:
    raise SystemExit('Atlas: fresh resource decision missing')
stamp=datetime.datetime.fromisoformat(json.loads(gate.read_text())['recordedAt'])
if (datetime.datetime.now(datetime.timezone.utc)-stamp).total_seconds()>300:
    raise SystemExit('Atlas: resource decision older than five minutes')
if (BASE/'observations/run-01').exists():
    raise SystemExit('Atlas: existing run retained, no duplicate execution')
os.nice(10)
if os.getpriority(os.PRIO_PROCESS,0)<10:
    raise SystemExit('Atlas: nice10 not applied; no child started')
started=datetime.datetime.now(datetime.timezone.utc)
record={'Atlas':'有限Bayesの計算','startedAt':started.isoformat(),'actualNice':os.getpriority(os.PRIO_PROCESS,0),'children':[]}
try:
    for name in ('run.py','verify.py'):
        p=subprocess.run([sys.executable,'-B',str(BASE/name)]+(['--record'] if name=='verify.py' else []),cwd=BASE,capture_output=True,text=True,timeout=15)
        (BASE/'verification'/(name+'.stdout.txt')).write_text(p.stdout)
        (BASE/'verification'/(name+'.stderr.txt')).write_text(p.stderr)
        record['children'].append({'program':name,'exitCode':p.returncode,'timeoutSeconds':15,'reaped':True})
        if p.returncode:raise RuntimeError(name+' failed')
    record['passed']=True
finally:
    record['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['elapsedSeconds']=(datetime.datetime.now(datetime.timezone.utc)-started).total_seconds()
    (BASE/'verification/execution.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False))
