"""Atlas: bounded one-time execution of the synthetic field-projection cases."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import sys
from copy import deepcopy
from cases import all_cases
from handler import handle

BASE = Path(__file__).resolve().parent
INPUTS = ['CONTRACT.md','CONTRACT-ADDENDUM.md','fixture.json','expected.json',
          'expected-addendum.json','handler.py','cases.py','run.py','verify.py']

def main():
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise SystemExit('Atlas: nice10 required; no handler calls started')
    signal.alarm(10)
    record = BASE/'observations/run-01'
    if record.exists(): raise SystemExit('Atlas: saved run exists; refusing overwrite')
    started = datetime.datetime.now(datetime.timezone.utc)
    fixture = json.loads((BASE/'fixture.json').read_text())
    outputs = []
    for case in all_cases(fixture):
        current=deepcopy(fixture)
        if case['storeVariant']: current['records']['red-report'].update(case['storeVariant'])
        before=deepcopy([current,case['context'],case['request']])
        outcomes={mode:handle(case['context'],case['request'],current,mode)
                  for mode in ('object_only','projected')}
        outputs.append({**case,**outcomes,'inputsUnchanged':before==[current,case['context'],case['request']]})
    finished=datetime.datetime.now(datetime.timezone.utc)
    result={'Atlas':'架空レコードのfield開示を比較したPython実行結果','executionStatus':'executed',
            'startedAt':started.isoformat(),'finishedAt':finished.isoformat(),
            'elapsedSeconds':(finished-started).total_seconds(),'nice':os.getpriority(os.PRIO_PROCESS,0),
            'python':sys.version,'platform':platform.platform(),'physicalExperiment':False,
            'realAuthentication':False,'httpHandlerStarted':False,'caseCount':len(outputs),
            'inputs':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in INPUTS},'cases':outputs}
    (record/'inputs').mkdir(parents=True)
    for name in INPUTS: (record/'inputs'/name).write_bytes((BASE/name).read_bytes())
    (record/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'Atlas':'40条件を保存','cases':len(outputs),'seconds':result['elapsedSeconds'],'nice':result['nice']}))

if __name__=='__main__': main()
