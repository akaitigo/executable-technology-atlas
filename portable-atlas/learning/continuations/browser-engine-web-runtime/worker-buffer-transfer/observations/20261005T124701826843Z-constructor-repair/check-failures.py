"""Independent failure-only checker with exact historical/synthetic served source hashes."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
REPAIRS=[ROOT/'observations/20261005T122916804863Z-failure-repair',ROOT/'observations/20261005T124701826843Z-constructor-repair']
def validate(v):
    r=v['result'];phase=r['phase'];assert r['status']=='EXECUTION_FAILURE' and v['acks']==[]
    if phase=='worker-constructor':
        assert r==dict(status='EXECUTION_FAILURE',phase=phase,error='SecurityError',message='QA_WORKER_CONSTRUCTOR_FAULT',partial={})
        assert not v['worker_terminated'] and [a['event'] for a in v['actions']]==['worker-not-created']
    else:
        assert phase=='before-probe' and r['error']=='Error' and r['message']=='WorkerError' and r.get('partial',{})=={}
        assert v['worker_terminated'] and v['actions'][-1]['event']=='worker-terminated'
        assert any(a['event']=='worker-error' and 'QA_BEFORE_PROBE_FAULT' in a['message'] for a in v['actions'])
        attempts=[a for a in v['actions'] if a['event']=='post-attempt'];assert len(attempts)==1 and attempts[0]['kind']=='probe' and attempts[0]['id'].endswith(':before')
    for n,h in v['source_binding'].items():
        candidates=[ROOT/n]
        if n in ('index.html','experiment.js','server.py','worker.js'):
            candidates+=[d/(n+'.before') for d in REPAIRS]
            if n=='worker.js':candidates+=[d/'fault-worker.js' for d in REPAIRS]
            extension={'index.html':'.html','experiment.js':'-experiment.js','worker.js':'-worker.js'}.get(n)
            if extension:candidates+=[REPAIRS[1]/('served-'+mode+extension) for mode in ('constructor','fault','held')]
        assert any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h for p in candidates),(n,h)
paths=sorted((ROOT/'observations/failures').glob('*/failure.json'));records=[json.loads(p.read_text()) for p in paths]
for v in records:validate(v)
assert {'worker-constructor','before-probe'}<=set(v['result']['phase'] for v in records)
constructor=next(v for v in records if v['result']['phase']=='worker-constructor');rejected=0
for edit in (lambda v:v['result'].update(status='EXPECTED_SERIALIZATION_REFUSAL'),lambda v:v.update(worker_terminated=True),lambda v:v['acks'].append({'kind':'data-ack'})):
    mutant=copy.deepcopy(constructor);edit(mutant)
    try:validate(mutant)
    except AssertionError:rejected+=1
assert rejected==3
print(json.dumps({'execution_failures':len(records),'separate_from_normal_raw':True,'constructor_fault_is_synthetic_QA':True,'source_hashes_match':True,'mutants_rejected':3}))
