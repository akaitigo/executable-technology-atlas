"""One root-managed stdlib batch, JSON stdout only; no subprocesses."""
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from model import calculate, restore_snapshot, InvalidInput

ROOT=Path(__file__).resolve().parent
SOURCES=['model.py','observe.py','fixtures.json','CONTRACT.md','contract-lock.json']
SCOPE={'finite_model':True,'guest_host_clock':False,'sleep_calls':0,'real_VM':False,
       'QEMU':False,'HVF':False,'network_requests':0,'browser_launches':0,'server_launches':0,
       'general_migration_claim':False}


def changed(value,path,new):
    out=copy.deepcopy(value);target=out
    for k in path[:-1]:target=target[k]
    target[path[-1]]=new
    return out


def fixture_refusals(f):
    edits=[('period-bool',['period'],True),('period-float',['period'],3.0),('period-changed',['period'],4),
           ('opcode',['program',0],'HOST'),('extra-instruction',['program'],f['program']+['NOP']),
           ('initial-a-bool',['initial','a'],True),('cut-float',['cases',0,'cut'],0.0),
           ('missing-case',['cases'],f['cases'][:-1]),('extra-key',['extra'],0)]
    return [(n,changed(f,p,v)) for n,p,v in edits]


def snapshot_refusals(s):
    edits=[('schema',['schema'],'other'),('version',['version'],2),('version-bool',['version'],True),
           ('version-float',['version'],1.0),('machine',['machine'],'other'),('extra-key',['extra'],0),
           ('counter-float',['state','device','counter'],0.0),('counter-range',['state','device','counter'],3),
           ('pending-int',['state','device','pending'],1),('memory-length',['state','memory'],[0,0,0]),
           ('a-range',['state','a'],256),('pc-tick',['state','pc'],1),('state-type',['state'],[])]
    out=[(n,changed(s,p,v)) for n,p,v in edits]
    bad=copy.deepcopy(s);del bad['state']['device'];out.append(('missing-device',bad))
    bad=copy.deepcopy(s);del bad['state']['device']['pending'];out.append(('missing-pending',bad))
    return out


def main():
    nice=os.getpriority(os.PRIO_PROCESS,0)
    if nice!=10:raise RuntimeError('actual nice must be 10 before target calculation')
    f=json.loads((ROOT/'fixtures.json').read_text());values=calculate(f)
    rejections=[]
    groups=[('fixture',fixture_refusals(f),calculate),
            ('snapshot',snapshot_refusals(values['cases'][0]['snapshot']),restore_snapshot),
            ('snapshot',[('fault-schema-in-normal',values['cases'][0]['incomplete_snapshot'])],restore_snapshot)]
    for kind,items,fn in groups:
        for name,request in items:
            try:fn(request)
            except InvalidInput as exc:
                rejections.append(dict(kind=kind,id=name,rejected=True,reason=str(exc),updates=exc.updates,reads=exc.reads))
            else:raise AssertionError('invalid input accepted: '+name)
    now=datetime.now(timezone.utc)
    data=dict(schema='atlas-device-snapshot-run-v1',fixture=f,values=values,scope=SCOPE,input_rejections=rejections,
              run=dict(run_id='device-snapshot-'+now.strftime('%Y%m%dT%H%M%S%fZ'),observed_at_utc=now.isoformat(),
                       pid=os.getpid(),actual_nice=nice,source_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}))
    sys.stdout.write(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


if __name__=='__main__':main()
