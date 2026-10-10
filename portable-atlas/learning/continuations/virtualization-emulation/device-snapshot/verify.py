"""Read saved values only; never imports or executes the producer."""
import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIXTURE_REFUSALS=['period-bool','period-float','period-changed','opcode','extra-instruction',
                  'initial-a-bool','cut-float','missing-case','extra-key']
SNAPSHOT_REFUSALS=['schema','version','version-bool','version-float','machine','extra-key',
                   'counter-float','counter-range','pending-int','memory-length','a-range','pc-tick',
                   'state-type','missing-device','missing-pending','fault-schema-in-normal']


def exact(a,b):
    assert type(a) is type(b), ('type',type(a).__name__,type(b).__name__)
    if isinstance(a,dict):
        assert a.keys()==b.keys(),'keys'
        for k in a:exact(a[k],b[k])
    elif isinstance(a,list):
        assert len(a)==len(b),'length'
        for x,y in zip(a,b):exact(x,y)
    else:assert a==b,('value',a,b)


def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()


def check(data):
    assert set(data)=={'schema','run','fixture','values','scope','input_rejections'}
    assert data['schema']=='atlas-device-snapshot-run-v1'
    fixture=json.loads((ROOT/'fixtures.json').read_text())
    oracle=json.loads((ROOT/'hand-oracle.json').read_text())
    exact(data['fixture'],fixture)
    exact(data['values'],oracle)  # Literal table fixed before implementation.
    exact(data['scope'],{'finite_model':True,'guest_host_clock':False,'sleep_calls':0,'real_VM':False,
                        'QEMU':False,'HVF':False,'network_requests':0,'browser_launches':0,'server_launches':0,
                        'general_migration_claim':False})
    refused=[dict(kind='fixture',id=n,rejected=True,reason='FIXED_INPUT_REQUIRED',updates=0,reads=0) for n in FIXTURE_REFUSALS]
    refused += [dict(kind='snapshot',id=n,rejected=True,reason='INVALID_SNAPSHOT',updates=0,reads=0) for n in SNAPSHOT_REFUSALS]
    exact(data['input_rejections'],refused)
    run=data['run'];assert set(run)=={'run_id','observed_at_utc','pid','actual_nice','source_hashes'}
    assert type(run['pid']) is int and run['pid']>0
    assert type(run['actual_nice']) is int and run['actual_nice']==10
    timestamp=datetime.fromisoformat(run['observed_at_utc'])
    assert timestamp.utcoffset() is not None and timestamp.utcoffset().total_seconds()==0
    assert run['run_id']=='device-snapshot-'+timestamp.strftime('%Y%m%dT%H%M%S%fZ')
    names=['model.py','observe.py','fixtures.json','CONTRACT.md','contract-lock.json']
    exact(run['source_hashes'],{n:sha(ROOT/n) for n in names})
    lock=json.loads((ROOT/'contract-lock.json').read_text())
    for n,h in lock['files'].items():assert sha(ROOT/n)==h,n
    # Independent saved-state relations: arithmetic phase and last expiry/ACK,
    # not an instruction interpreter or a replay of the producer's loop.
    for case in data['values']['cases']:
        cut=case['cut']
        for name,v in case['variants'].items():
            first=v['boundary_states'][0];counter=first['device']['counter']
            expires=list(range(cut+3-counter,11,3))
            if first['device']['pending']:expires=[cut]+expires
            for state in v['boundary_states']:
                t=state['tick']
                assert state['pc']==t
                assert state['device']['counter']==divmod(counter+t-cut,3)[1]
                # ACK executes at t6 after this tick's expiry; a later expiry relatches.
                last_expiry=max([x for x in expires if x<=t],default=-1)
                last_ack=6 if cut<6<=t else -1
                assert state['device']['pending']==(last_expiry>last_ack)
            assert [e['tick'] for e in v['steps'] if e['timer_after']['fired']]==[x for x in expires if x>cut]
            for e in v['steps']:
                after=v['boundary_states'][e['tick']-cut]
                assert e['pc_before']==e['tick']-1
                assert after['device']['pending']==(False if e['ack'] else e['timer_after']['pending'])
                if e['read_value'] is not None:
                    assert e['read_value']==int(e['timer_after']['pending'])==after['a']
                if e['write'] is not None:
                    w=e['write'];before=v['boundary_states'][e['tick']-cut-1]
                    assert w['previous']==before['memory'][w['address']]
                    assert w['value']==before['a']==after['memory'][w['address']]
            exact(v['final_state'],v['boundary_states'][-1])
        exact(case['variants']['continuation'],case['variants']['full-restore'])
        exact(case['snapshot']['state'],case['prefix_states'][-1])
        assert 'device' not in case['incomplete_snapshot']['state']
    return dict(cases=4,variants=12,suffix_boundaries=99,suffix_updates=87,read_observations=33,
                timer_expiries=26,input_rejections=25)


def tamper_checks(data):
    edits=[('counter',['values','cases',1,'snapshot','state','device','counter'],0),
           ('pending',['values','cases',2,'snapshot','state','device','pending'],False),
           ('ack-order',['values','cases',0,'variants','continuation','boundary_states',6,'device','pending'],True),
           ('fault-read',['values','cases',1,'variants','omit-device','reads',0,'value'],1),
           ('fault-memory',['values','cases',2,'variants','omit-device','final_state','memory',0],1),
           ('false-equivalence',['values','cases',1,'comparison','fault_suffix_equal'],True),
           ('read-vs-state-difference',['values','cases',1,'comparison','first_read_difference_tick'],2),
           ('timer-expiry',['values','cases',1,'variants','omit-device','steps',0,'timer_after','fired'],True),
           ('null-to-zero',['values','cases',0,'variants','continuation','steps',0,'read_value'],0),
           ('snapshot-schema',['values','cases',0,'snapshot','schema'],'atlas-device-snapshot-omit-device-demo'),
           ('bool-as-int',['values','cases',0,'snapshot','version'],True),
           ('scope',['scope','real_VM'],True),('priority',['run','actual_nice'],0),
           ('refusal-updated',['input_rejections',0,'updates'],1),
           ('fixture-float',['fixture','period'],3.0),('missing-case',['values','cases'],data['values']['cases'][:-1])]
    output=[]
    for name,path,value in edits:
        bad=copy.deepcopy(data);target=bad
        for k in path[:-1]:target=target[k]
        target[path[-1]]=value
        try:check(bad)
        except (AssertionError,ValueError,KeyError,TypeError):output.append(dict(id=name,rejected=True))
        else:raise AssertionError('saved tamper accepted: '+name)
    return output


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--result',required=True,type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args();data=json.loads(args.result.read_text())
    report=dict(passed=True,result_path=str(args.result.resolve()),result_sha256=sha(args.result),
                verify_source_sha256=sha(Path(__file__)),run_id=data['run']['run_id'],checked=check(data),
                tamper_checks=tamper_checks(data),producer_executions=0)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
