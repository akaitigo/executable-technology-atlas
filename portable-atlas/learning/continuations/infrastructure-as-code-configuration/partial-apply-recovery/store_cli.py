"""Create-only sequential synthetic store. Per-write persistence, no group rollback."""
import argparse
import hashlib
import json
import sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def utc():return datetime.now(timezone.utc).isoformat()
def emit(kind,**data):print(json.dumps({'at':utc(),'kind':kind,**data},ensure_ascii=False),flush=True)
def read(path):return json.loads(path.read_text())
def safe(value):
    path=(ROOT/value).resolve()
    if not path.is_relative_to(ROOT/'observations'):raise ValueError('Only task-owned observation paths accepted')
    return path
def plan(desired,state):
    actions=[];known=set(state['resources'])
    for resource in desired['resources']:
        name=resource['id']
        if not set(resource['depends_on']).issubset(known):raise ValueError('Dependency order missing: '+name)
        if name in state['resources']:
            if state['resources'][name]!=resource:raise ValueError('Update/replacement unsupported: '+name)
        else:actions.append({'operation':'create','resource':resource})
        known.add(name)
    return {'observed_revision':state['revision'],'actions':actions,'scope':'synthetic create-only ordered plan'}
def apply(store,actions,fault):
    emit('apply-start',fault=fault,action_count=len(actions))
    for number,action in enumerate(actions,1):
        state=read(store);resource=action['resource'];name=resource['id']
        emit('action-start',number=number,id=name,revision=state['revision'])
        if number==2 and fault=='before-second':
            emit('injected-fault',point='before-second',id=name,revision=state['revision'],rollback=False)
            print('InjectedFault: before-second; persisted state retained',file=sys.stderr);return 70
        if action['operation']!='create':raise ValueError('Unsupported operation')
        if name in state['resources']:
            emit('duplicate-create-rejected',id=name,revision=state['revision'],state_unchanged=True)
            print('DuplicateCreate: '+name+' already exists; blind replay rejected',file=sys.stderr);return 22
        if not set(resource['depends_on']).issubset(state['resources']):raise ValueError('Dependency missing')
        state['resources'][name]=resource;state['revision']+=1
        # One JSON file rewrite per resource; no rollback or all-resource transaction.
        store.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        reread=read(store)
        emit('persisted',number=number,id=name,state=reread,sha256=hashlib.sha256(store.read_bytes()).hexdigest())
        if number==2 and fault=='after-second':
            emit('injected-fault',point='after-second',id=name,revision=reread['revision'],rollback=False)
            print('InjectedFault: after-second; persisted state retained',file=sys.stderr);return 71
    emit('apply-complete',state=read(store),noop=len(actions)==0)
    return 0
def main():
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=('plan','apply','refresh'));parser.add_argument('--store',required=True);parser.add_argument('--desired');parser.add_argument('--plan');parser.add_argument('--fault',choices=('none','before-second','after-second'),default='none');args=parser.parse_args()
    store=safe(args.store)
    if args.operation=='refresh':emit('refresh',state=read(store),sha256=hashlib.sha256(store.read_bytes()).hexdigest());return 0
    if args.operation=='plan':emit('plan',plan=plan(read(safe(args.desired)),read(store)));return 0
    return apply(store,read(safe(args.plan))['actions'],args.fault)
if __name__=='__main__':raise SystemExit(main())
