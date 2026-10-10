"""Independent byte/ownership/protocol checks; never imports/runs browser producer."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def independent(f):
    original=list(f['bytes']);length=len(original);total=sum(original);mutation=[f['mutate_first_to']]+original[1:]
    refused=f['contains_function'];detached=f['transfer'] and not refused
    return dict(status='EXPECTED_SERIALIZATION_REFUSAL' if refused else 'DELIVERED',sender_after_length=0 if detached else length,sender_after_bytes=None if detached else original,sender_access_error='TypeError' if detached else None,worker_before_bytes=None if refused else original,worker_after_bytes=None if refused else mutation,worker_length=None if refused else length,worker_sum=None if refused else total,post_error='DataCloneError' if refused else None,received_data=0 if refused else 1)
def validate(v):
    fixtures=json.loads((ROOT/'fixtures.json').read_text());hand=json.loads((ROOT/'oracle.json').read_text());name=v['case'];f=fixtures[name];assert v['fixture']==f
    expected=independent(f);assert expected==hand[name]
    r=v['result'];assert all(r[k]==value for k,value in expected.items())
    original=dict(byte_length=len(f['bytes']),bytes=f['bytes'],access_error=None);assert r['sender_before']==original
    assert r['sender_immediate']==dict(byte_length=expected['sender_after_length'],bytes=expected['sender_after_bytes'],access_error=expected['sender_access_error'])
    assert v['utc'].endswith('Z') and v['runtime']['userAgent'] and v['runtime']['timeout_ms']==5000
    session=v['session'];assert v['data_id']==session+':data';ids=[session+':before',session+':data',session+':after']
    before=dict(id=ids[0],kind='probe-ack',received_data=0,received_ids=[])
    after=dict(id=ids[2],kind='probe-ack',received_data=expected['received_data'],received_ids=[] if f['contains_function'] else [ids[1]])
    assert r['initial_probe']==before and r['final_probe']==after
    if f['contains_function']:
        assert r['data_ack'] is None and v['acks']==[before,after]
    else:
        ack=dict(id=ids[1],kind='data-ack',received_data=1,received_ids=[ids[1]],byte_length=len(f['bytes']),before=f['bytes'],after=[f['mutate_first_to']]+f['bytes'][1:],sum=sum(f['bytes']))
        assert r['data_ack']==ack and v['acks']==[before,ack,after]
    actions=v['actions'];attempts=[a['id'] for a in actions if a['event']=='post-attempt'];assert attempts==ids
    throws=[a for a in actions if a['event']=='post-throw'];assert throws==([] if not f['contains_function'] else [dict(event='post-throw',utc=throws[0]['utc'],id=ids[1],name='DataCloneError')])
    assert all(a['event'] not in ('timeout','worker-error') for a in actions)
    received=[a['id'] for a in actions if a['event']=='worker-message'];assert received==[a['id'] for a in v['acks']]
    assert actions[-1]['event']=='worker-terminated' and v['worker_terminated'] is True
    for n,h in v['source_binding'].items():
        source=ROOT/n
        if hashlib.sha256(source.read_bytes()).hexdigest()!=h and n in ('index.html','server.py','experiment.js'):
            candidates=[ROOT/d/(n+'.before') for d in ('observations/20261005T122916804863Z-failure-repair','observations/20261005T124701826843Z-constructor-repair')]
            source=next(p for p in candidates if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h)
        assert hashlib.sha256(source.read_bytes()).hexdigest()==h
    assert set(v['source_binding'])=={'worker.js','experiment.js','fixtures.json','oracle.json','index.html','server.py'}
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths,'explicit real IAB record required';cases={}
    for p in paths:
        v=json.loads(p.read_text());validate(v);cases[v['case']]=v
    assert set(cases)=={'clone','transfer','function-refusal'}
    mutations=[]
    def reject(label,case,edit):
        value=copy.deepcopy(cases[case]);edit(value)
        try:validate(value)
        except (AssertionError,KeyError,IndexError):mutations.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('transfer still owned','transfer',lambda v:v['result'].update(sender_after_length=4))
    reject('wrong worker sum','clone',lambda v:v['result'].update(worker_sum=9))
    reject('worker mutation leaked into sender','clone',lambda v:v['result'].update(sender_after_bytes=[9,2,3,4]))
    reject('function was received','function-refusal',lambda v:v['result']['final_probe'].update(received_data=1,received_ids=[v['data_id']]))
    reject('missing after-probe ACK','function-refusal',lambda v:v['acks'].pop())
    return dict(recorded_runs=len(paths),normal_cases=2,expected_serialization_refusals=1,oracle='independent byte arithmetic/ownership + explicit protocol IDs/counts, hand table before runs',mutations_rejected=mutations)
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
