"""Read-only explicit QA failure evidence, distinct from success collection."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];QA=pathlib.Path(__file__).resolve().parent
p=ROOT/'observations/failures/20261005T123239788754Z/failure.json';v=json.loads(p.read_text())
assert v['case']=='function-refusal' and v['result']==dict(status='EXECUTION_FAILURE',phase='before-probe',error='Error',message='WorkerError')
assert v['acks']==[] and v['worker_terminated'] is True
assert [a['event'] for a in v['actions']]==['post-attempt','post-return','worker-error','worker-terminated']
assert 'QA_BEFORE_PROBE_FAULT' in v['actions'][2]['message']
assert v['actions'][0]['kind']=='probe' and v['actions'][0]['id'].endswith(':before')
for n,h in v['source_binding'].items():
    p=QA/'fault-worker.js' if n=='worker.js' else ROOT/n
    assert hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps({'qa_execution_failures':1,'phase':'before-probe','acks':0,'not_success_or_expected_DataCloneError':True,'fault_source_binding':True}))
