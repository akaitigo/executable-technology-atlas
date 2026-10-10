"""One root-managed stdlib target; one JSON on stdout, no child processes."""
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from model import calculate, InvalidInput

ROOT=Path(__file__).resolve().parent
SOURCES=['model.py','observe.py','fixtures.json','CONTRACT.md','contract-lock.json']
SCOPE={'finite_virtual_tick_model':True,'network_requests':0,'sleep_calls':0,'random_draws':0,
       'real_proxy':False,'response_loss_modelled':False,'general_idempotency_claim':False,
       'browser_launches':0,'server_launches':0}


def changed(value,path,new):
    out=copy.deepcopy(value);target=out
    for k in path[:-1]:target=target[k]
    target[path[-1]]=new
    return out


def refusals(f):
    edits=[('retry-bool',['max_retries'],True),('budget-float',['cases',0,'call_budget'],12.0),
           ('capacity-bool',['capacity_per_tick'],True),('capacity-changed',['capacity_per_tick'],2),
           ('delay-bool',['cases',0,'delays',0,0],True),('delay-float',['cases',0,'delays',0,0],1.0),
           ('delay-zero',['cases',0,'delays',0,0],0),('delay-negative',['cases',0,'delays',0,0],-1),
           ('delay-missing',['cases',0,'delays',0],[1]),('client-order',['clients'],['B','A','C','D']),
           ('case-id',['cases',0,'id'],'unknown'),('extra-case',['cases'],f['cases']+[f['cases'][0]]),
           ('missing-case',['cases'],f['cases'][:-1]),('extra-key',['extra'],0),
           ('schema',['schema'],'unknown'),('last-tick',['last_tick'],8)]
    out=[(n,changed(f,p,v)) for n,p,v in edits]
    bad=copy.deepcopy(f);del bad['attempt_duration'];out.append(('missing-key',bad))
    return out


def main():
    nice=os.getpriority(os.PRIO_PROCESS,0)
    if nice!=10:raise RuntimeError('actual nice must be 10 before target calculation')
    f=json.loads((ROOT/'fixtures.json').read_text());values=calculate(f)
    rejected=[]
    for name,request in refusals(f):
        try:calculate(request)
        except InvalidInput as exc:
            rejected.append(dict(id=name,rejected=True,reason=str(exc),attempts=exc.attempts,state_updates=exc.state_updates))
        else:raise AssertionError('invalid fixture accepted: '+name)
    now=datetime.now(timezone.utc)
    result=dict(schema='atlas-retry-concentration-run-v1',fixture=f,values=values,scope=SCOPE,input_rejections=rejected,
                run=dict(run_id='retry-concentration-'+now.strftime('%Y%m%dT%H%M%S%fZ'),observed_at_utc=now.isoformat(),
                         pid=os.getpid(),actual_nice=nice,source_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}))
    sys.stdout.write(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
