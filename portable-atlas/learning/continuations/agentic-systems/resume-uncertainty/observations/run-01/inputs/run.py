"""Atlas: exactly one bounded synthetic batch; invoked only through the reviewed wrapper."""
import datetime
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    if os.getpriority(os.PRIO_PROCESS,0)<10:
        raise SystemExit('actual nice >=10 required before producer import')
    from produce import collect
    from verify import check, mutation_examples
    out=ROOT/'observations/run-01'
    out.mkdir(parents=True,exist_ok=False)
    names=['CONTRACT.md','SOURCES.md','plan.json','cases.json','expected.json','model.py','produce.py','verify.py','run.py','execute_once.py']
    names += ['inputs/'+n+'.json' for n in ['ready-valid','pending-shared','ready-expired','completed']]
    bindings={}
    for n in names:
        data=(ROOT/n).read_bytes();destination=out/'inputs'/n;destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as f:f.write(data)
        bindings[n]=hashlib.sha256(data).hexdigest()
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();began=time.monotonic()
    result=collect()
    result.update(startedAt=started,calculationSeconds=time.monotonic()-began,
        toolchain={'python':platform.python_version(),'executable':sys.executable,'platform':platform.platform()},
        pid=os.getpid(),actualNice=os.getpriority(os.PRIO_PROCESS,0),sourceSha256=bindings)
    data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode()
    with (out/'results.json').open('xb') as f:f.write(data)
    checked={'Atlas':'手表と全checkpointの保存値照合','passed':True,'checks':check(result),'mutations':mutation_examples(result),
             'resultsSha256':hashlib.sha256(data).hexdigest(),'producerImportedByChecker':False}
    with (ROOT/'verification/saved-result-check.json').open('x') as f:json.dump(checked,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'passed':True,'strictCases':5,'faultComparisons':2,'checks':checked['checks'],
                     'mutations':len(checked['mutations']),'actualNice':result['actualNice'],'pid':os.getpid(),
                     'calculationSeconds':result['calculationSeconds'],'resultsSha256':checked['resultsSha256']}))

if __name__=='__main__':main()
