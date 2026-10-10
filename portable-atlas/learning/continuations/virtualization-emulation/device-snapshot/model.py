"""Finite polling-timer model; no host clock, IO, subprocess, or real VM."""
import copy
import json

PROGRAM = ['NOP','NOP','NOP','READ','STORE0','ACK','READ','STORE1','READ','STORE2']
FIXTURE = {'schema':'atlas-device-snapshot-fixture-v1','machine':'polling-timer-v1','period':3,
           'program':PROGRAM,'initial':{'pc':0,'a':7,'memory':[0,0,0,0],'tick':0,
                                       'device':{'counter':0,'pending':False}},
           'cases':[{'id':'initial','cut':0},{'id':'before-expiry','cut':2},
                    {'id':'pending-latched','cut':3},{'id':'after-ack','cut':6}]}


class InvalidInput(ValueError):
    updates = 0
    reads = 0


def exact(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a == b


def validate_state(s):
    def integer(x, lo, hi):
        return type(x) is int and lo <= x <= hi
    valid = type(s) is dict and set(s) == {'pc','a','memory','tick','device'}
    if valid:
        valid = integer(s['pc'],0,10) and integer(s['tick'],0,10) and s['pc']==s['tick']
        valid = valid and integer(s['a'],0,255) and type(s['memory']) is list and len(s['memory'])==4
        valid = valid and all(integer(x,0,255) for x in s['memory'])
        d=s['device']
        valid = valid and type(d) is dict and set(d)=={'counter','pending'}
        valid = valid and integer(d['counter'],0,2) and type(d['pending']) is bool
    if not valid:
        raise InvalidInput('INVALID_SNAPSHOT')


def save_snapshot(state, *, omit_device=False):
    validate_state(state)
    saved=copy.deepcopy(state)
    schema='atlas-device-snapshot'
    if omit_device:
        del saved['device']
        schema='atlas-device-snapshot-omit-device-demo'
    return dict(schema=schema,version=1,machine='polling-timer-v1',state=saved)


def restore_snapshot(snapshot, *, incomplete_demo=False):
    schema='atlas-device-snapshot-omit-device-demo' if incomplete_demo else 'atlas-device-snapshot'
    if (type(snapshot) is not dict or set(snapshot)!={'schema','version','machine','state'}
            or type(snapshot['schema']) is not str or snapshot['schema']!=schema
            or type(snapshot['version']) is not int or snapshot['version']!=1
            or type(snapshot['machine']) is not str or snapshot['machine']!='polling-timer-v1'):
        raise InvalidInput('INVALID_SNAPSHOT')
    state=copy.deepcopy(snapshot['state'])
    if incomplete_demo:
        if type(state) is not dict or set(state)!={'pc','a','memory','tick'}:
            raise InvalidInput('INVALID_SNAPSHOT')
        state['device']={'counter':0,'pending':False}
    validate_state(state)
    return state


def advance(state):
    """One commit: tick -> timer -> fixed instruction -> pc."""
    out=copy.deepcopy(state)
    pc=out['pc']
    if not 0<=pc<10:
        raise InvalidInput('NO_INSTRUCTION')
    out['tick']+=1
    d=out['device'];d['counter']+=1
    fired=d['counter']==3
    if fired:
        d['counter']=0;d['pending']=True
    timer=dict(counter=d['counter'],pending=d['pending'],fired=fired)
    op=PROGRAM[pc];read=None;write=None
    if op=='READ':
        out['a']=1 if d['pending'] else 0
        read=out['a']
    elif op.startswith('STORE'):
        address=int(op[-1])
        write=dict(address=address,previous=out['memory'][address],value=out['a'])
        out['memory'][address]=out['a']
    elif op=='ACK':
        d['pending']=False
    out['pc']+=1
    event=dict(pc_before=pc,tick=out['tick'],op=op,timer_after=timer,
               read_value=read,write=write,ack=op=='ACK')
    return out,event


def suffix(start):
    validate_state(start)
    state=copy.deepcopy(start);boundaries=[copy.deepcopy(state)];steps=[];reads=[]
    while state['pc']<10:
        state,event=advance(state)
        steps.append(event);boundaries.append(copy.deepcopy(state))
        if event['read_value'] is not None:
            reads.append(dict(tick=event['tick'],value=event['read_value']))
    return dict(boundary_states=boundaries,steps=steps,reads=reads,final_state=copy.deepcopy(state))


def calculate(fixture):
    if not exact(fixture,FIXTURE):
        raise InvalidInput('FIXED_INPUT_REQUIRED')
    cases=[]
    for item in fixture['cases']:
        state=copy.deepcopy(fixture['initial']);prefix=[copy.deepcopy(state)]
        for _ in range(item['cut']):
            state,_event=advance(state);prefix.append(copy.deepcopy(state))
        original=copy.deepcopy(state)
        saved=save_snapshot(state);incomplete=save_snapshot(state,omit_device=True)
        full=restore_snapshot(json.loads(json.dumps(saved,sort_keys=True)))
        faulty=restore_snapshot(json.loads(json.dumps(incomplete,sort_keys=True)),incomplete_demo=True)
        assert exact(original,state) and exact(full,state)
        variants={'continuation':suffix(state),'full-restore':suffix(full),'omit-device':suffix(faulty)}
        correct=variants['continuation'];bad=variants['omit-device']
        differences=[x['tick'] for x,y in zip(correct['boundary_states'],bad['boundary_states']) if not exact(x,y)]
        read_differences=[x['tick'] for x,y in zip(correct['reads'],bad['reads']) if not exact(x,y)]
        cases.append(dict(id=item['id'],cut=item['cut'],prefix_states=prefix,snapshot=saved,
                          incomplete_snapshot=incomplete,variants=variants,
                          comparison=dict(full_suffix_equal=exact(correct,variants['full-restore']),
                                          fault_suffix_equal=exact(correct,bad),
                                          first_state_difference_tick=differences[0] if differences else None,
                                          first_read_difference_tick=read_differences[0] if read_differences else None)))
    return {'schema':'atlas-device-snapshot-hand-v1','cases':cases}
