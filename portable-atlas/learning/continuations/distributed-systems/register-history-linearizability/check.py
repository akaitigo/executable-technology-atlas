"""All permutations + literal last-write spec. No producer imports."""
import copy,hashlib,itertools,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def spec(order):
    for index,operation in enumerate(order):
        if operation['op']=='read':
            earlier=[prior['arg'] for prior in order[:index] if prior['op']=='write']
            expected=earlier[-1] if earlier else 0
            if operation['out']!=expected:return False,{'operation':operation['id'],'expected':expected,'returned':operation['out']}
    return True,None
def oracle_permutations(history):
    answer=[]
    for order in itertools.permutations(history):
        positions={o['id']:i for i,o in enumerate(order)}
        respects_time=all(positions[left['id']]<positions[right['id']] for left in history for right in history if left['res']<right['inv'])
        if respects_time and spec(order)[0]:answer.append([o['id'] for o in order])
    return answer
def validate(case,raw,expected,history):
    assert raw['history']==history
    actual=raw['result'];want=expected[case]
    assert actual['status']==want['status']
    if want['status']=='INPUT_REJECTED':
        assert actual=={'status':'INPUT_REJECTED','reason':want['reason'],'edges':[],'witnesses':[],'trace':[{'event':'input_rejected','reason':want['reason']}],'response_sort':None};return
    # Independent contract checks on the eight schema-valid input histories.
    assert 1<=len(history)<=4 and len({o['id'] for o in history})==len(history)
    ticks=[o[k] for o in history for k in ('inv','res')];assert all(type(t) is int and 0<=t<=100 for t in ticks) and len(set(ticks))==len(ticks)
    for o in history:
        assert o['inv']<o['res']
        if o['op']=='read':assert type(o['out']) is int and 0<=o['out']<=2 and 'arg' not in o
        else:assert o['op']=='write' and type(o['arg']) is int and 0<=o['arg']<=2 and o['out']=='ok'
    assert all(a['res']<b['inv'] or b['res']<a['inv'] for i,a in enumerate(history) for b in history[i+1:] if a['client']==b['client'])
    independent=oracle_permutations(history)
    assert sorted(independent)==sorted(want['witnesses'])==sorted(actual['witnesses'])
    assert actual['reason'] is None
    edges=[[a['id'],b['id']] for a,b in itertools.permutations(history,2) if a['res']<b['inv']]
    assert sorted(actual['edges'])==sorted(edges)
    by_id={o['id']:o for o in history};sorted_response=sorted(history,key=lambda o:o['res']);legal,failure=spec(sorted_response)
    assert legal==want['response_sort']
    assert actual['response_sort']=={'order':[o['id'] for o in sorted_response],'accepted':legal,'failure':failure}
    assert sorted([e['order'] for e in actual['trace'] if e['event']=='legal_candidate'])==sorted(independent)
    for event in actual['trace']:
        if event['event']=='read_mismatch':
            order=[by_id[n] for n in event['prefix']];valid,why=spec(order);assert not valid and why=={'operation':event['prefix'][-1],'expected':event['expected'],'returned':event['returned']}
        if event['event']=='available':
            prefix=event['prefix'];choices=[o['id'] for o in history if o['id'] not in prefix and all(p['id'] in prefix for p in history if p['res']<o['inv'])]
            assert event['choices']==choices
            past=[by_id[n]['arg'] for n in prefix if by_id[n]['op']=='write'];assert event['state']==(past[-1] if past else 0)
def verify():
    expected=json.loads((ROOT/'oracle.json').read_text());histories=json.loads((ROOT/'histories.json').read_text());paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for path in paths:
        raw=json.loads(path.read_text());assert list(raw)==list(expected)
        for case in raw:
            validate(case,raw[case],expected,histories[case])
            for name,digest in raw[case]['source_binding'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    raw=json.loads(paths[-1].read_text());rejected=0
    for kind in ('stale-witness','missing-edge','bad-sort','bad-reason','read-mismatch'):
        case={'stale-witness':'after-write-stale','missing-edge':'after-write-fresh','bad-sort':'overlap-read-one','bad-reason':'pending','read-mismatch':'after-write-stale'}[kind];mutant=copy.deepcopy(raw[case]);result=mutant['result']
        if kind=='stale-witness':result['witnesses']=[['r1','w1']]
        if kind=='missing-edge':result['edges']=[]
        if kind=='bad-sort':result['response_sort']['accepted']=True
        if kind=='bad-reason':result['reason']='TIME_ORDER'
        if kind=='read-mismatch':next(e for e in result['trace'] if e['event']=='read_mismatch')['expected']=0
        try:validate(case,mutant,expected,histories[case])
        except AssertionError:rejected+=1
        else:raise AssertionError('independent oracle accepted corruption')
    print(json.dumps({'well_formed_histories':8,'linearizable':6,'not_linearizable':2,'expected_input_refusals':6,'mutants_rejected':rejected,'recorded_runs':len(paths),'oracle':'all permutations + separate last-write specification'}))
if __name__=='__main__':verify()
