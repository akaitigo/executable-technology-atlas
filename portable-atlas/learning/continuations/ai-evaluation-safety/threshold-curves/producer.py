#!/usr/bin/env python3
"""Atlas: one small calculation over fixed synthetic scores; never read expected.json."""
import hashlib,json,os,platform,resource,sys,traceback
from decimal import Decimal
from pathlib import Path
from threshold_sweep import sweep
ROOT=Path(__file__).resolve().parent
def emit(value):
    print(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False),flush=True)
def main():
    resource.setrlimit(resource.RLIMIT_CPU,(2,2))
    emit({'kind':'environment','project':'Atlas','python_version':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'pid':os.getpid(),'nice':os.getpriority(os.PRIO_PROCESS,0),'cpu_limit_seconds':list(resource.getrlimit(resource.RLIMIT_CPU)),'workers_created':0,'model_or_api_calls':0})
    state_count=0
    for fixture,path in [('main','inputs/predictions.json'),('tie','inputs/tie.json')]:
        raw=(ROOT/path).read_bytes();data=json.loads(raw,parse_float=Decimal)
        result=sweep(data['samples'])
        emit({'kind':'fixture','fixture':fixture,'input_path':path,'input_sha256':hashlib.sha256(raw).hexdigest(),'origin':data['origin'],'auc_computed':False,**{k:v for k,v in result.items() if k!='states'}})
        for state in result['states']:
            emit({'kind':'state','fixture':fixture,**state});state_count+=1
    emit({'kind':'batch-complete','fixture_count':2,'state_count':state_count,'retry_count':0});return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as e:
        emit({'kind':'producer-failure','type':type(e).__name__,'detail':str(e),'traceback':traceback.format_exc()})
        raise SystemExit(1)
