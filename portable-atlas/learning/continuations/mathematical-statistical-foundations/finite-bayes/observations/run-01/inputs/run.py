"""Atlas: one bounded recording of predefined cases, no browser."""
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from bayes import calculate

BASE=Path(__file__).resolve().parent
if os.getpriority(os.PRIO_PROCESS,0)<10:raise SystemExit('Atlas: actual nice10 required')
started=datetime.datetime.now(datetime.timezone.utc);tick=time.monotonic()
out=BASE/'observations/run-01';out.mkdir(parents=True,exist_ok=False);(out/'inputs').mkdir()
files=['CONTRACT.md','cases.json','expected.json','bayes.py','run.py','verify.py','execute_once.py']
inputs={}
for name in files:
    content=(BASE/name).read_bytes();(out/'inputs'/name).write_bytes(content);inputs[name]=hashlib.sha256(content).hexdigest()
spec=json.loads((BASE/'cases.json').read_text())
def record(case):
    request=copy.deepcopy(case['request']);before=copy.deepcopy(request)
    result=calculate(request)
    return {'id':case['id'],'requestBefore':before,'requestAfter':request,'outcome':result}
raw={'Atlas':'有限仮説Bayesの保存計算','startedAt':started.isoformat(),'python':platform.python_version(),
     'platform':platform.platform(),'actualNice':os.getpriority(os.PRIO_PROCESS,0),'inputs':inputs,
     'cases':[record(x) for x in spec['cases']],'refusals':[record(x) for x in spec['refusals']],
     'samplingPerformed':False,'browserExecuted':False}
raw['elapsedSeconds']=time.monotonic()-tick;raw['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(out/'results.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'Atlas':'Bayes run saved','cases':len(raw['cases']),'refusals':len(raw['refusals']),'elapsedSeconds':raw['elapsedSeconds']},ensure_ascii=False))
