"""Atlas: independent initial store for every finite request and strategy."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import sys
from copy import deepcopy
from handler import handle

BASE=Path(__file__).resolve().parent
INPUTS=['CONTRACT.md','fixture.json','cases.json','expected.json','handler.py','run.py','verify.py']
MODES=['bulk_assign','incremental_check','validate_then_apply']
def main():
    if os.getpriority(os.PRIO_PROCESS,0)<10:raise SystemExit('Atlas: actual nice10 required; no calls started')
    signal.alarm(10);record=BASE/'observations/run-01'
    if record.exists():raise SystemExit('Atlas: existing result retained; no overwrite')
    started=datetime.datetime.now(datetime.timezone.utc)
    fixture=json.loads((BASE/'fixture.json').read_text());cases=json.loads((BASE/'cases.json').read_text())['cases'];outputs=[]
    for case in cases:
        outcomes={}
        for mode in MODES:
            store=deepcopy(fixture['records']);before=deepcopy(store)
            context=deepcopy(case['context']);request=deepcopy(case['request']);fixed=deepcopy(fixture)
            result=handle(context,request,store,fixture,mode)
            delta=[{'object_id':obj,'field':field,'before':before[obj][field],'after':store[obj][field]}
                   for obj in before for field in before[obj] if before[obj][field]!=store[obj][field]]
            outcomes[mode]={**result,'afterStore':deepcopy(store),'storeDelta':delta,
                            'contextUnchanged':context==case['context'],'requestUnchanged':request==case['request'],
                            'fixtureUnchanged':fixture==fixed}
        outputs.append({**case,'beforeStore':deepcopy(fixture['records']),'outcomes':outcomes})
    end=datetime.datetime.now(datetime.timezone.utc)
    result={'Atlas':'書込項目と拒否時storeのPython実行結果','executionStatus':'executed','startedAt':started.isoformat(),
            'finishedAt':end.isoformat(),'elapsedSeconds':(end-started).total_seconds(),'nice':os.getpriority(os.PRIO_PROCESS,0),
            'python':sys.version,'platform':platform.platform(),'caseCount':len(outputs),'modeCount':3,
            'freshStoreForEachCaseAndMode':True,'realAuthentication':False,'realDatabaseTransaction':False,
            'httpHandlerStarted':False,'inputs':{n:hashlib.sha256((BASE/n).read_bytes()).hexdigest() for n in INPUTS},'cases':outputs}
    (record/'inputs').mkdir(parents=True)
    for n in INPUTS:(record/'inputs'/n).write_bytes((BASE/n).read_bytes())
    (record/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'Atlas':'24要求×3方式を保存','caseCount':len(outputs),'responses':len(outputs)*3,'seconds':result['elapsedSeconds'],'nice':result['nice']},ensure_ascii=False))
if __name__=='__main__':main()
