"""Hand-authored independent oracle reader. No executor/runner import."""
import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
STAGES={
 'normal':['preflight_accepted','dispatch','tool_result','bound','dispatch','tool_result','end'],
 'missing-field':['preflight_accepted','dispatch','tool_result','rejected'],
 'string-value':['preflight_accepted','dispatch','tool_result','rejected'],
 'bool-value':['preflight_accepted','dispatch','tool_result','rejected'],
 'unknown-reference':['rejected'],'cycle':['rejected'],
 'bad-coercion':['preflight_accepted','dispatch','tool_result','bad_coercion','bound','dispatch','tool_result','end'],
 'bad-promotion':['preflight_accepted','dispatch','tool_result','bound','bad_promotion','dispatch','tool_result','end']}
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def validate(case,raw,expected,fixture):
    actual=raw['result'];want=expected[case]
    assert canonical(raw['input'])==canonical(fixture)
    assert actual['status']==want['status'] and actual['final']==want['final'] and actual['violation'] is want['violation']
    assert actual['calls']==want['calls']
    rejection=actual['rejection']
    if want['reason']:
        assert rejection=={'reason':want['reason'],'phase':want['phase'],'node':'a','arg':None if case=='cycle' else 'left'}
    else:assert rejection is None
    trace=actual['trace'];assert [e['stage'] for e in trace]==STAGES[case]
    assert [e['seq'] for e in trace]==list(range(1,len(trace)+1))
    assert [{k:e[k] for k in ('node','tool','args')} for e in trace if e['stage']=='dispatch']==want['calls']
    if want['calls']:
        assert canonical(actual['results']['r'])==canonical(fixture['read_result'])
        read_event=next(e for e in trace if e['stage']=='tool_result')
        assert canonical(read_event['result'])==canonical(fixture['read_result'])
    else:assert actual['results']=={}
    if want['final'] is not None:assert type(actual['results']['a']['value']) is int and actual['results']['a']['value']==want['final']
    if case=='normal':
        assert actual['results']['r']['proposed_plan']=={'tool':'add','args':{'left':100,'right':3}}
        assert actual['calls'][1]['args']=={'left':4,'right':3}
    if case in ('normal','bad-promotion','bad-coercion'):
        bound=next(e for e in trace if e['stage']=='bound');assert bound=={'seq':5 if case=='bad-coercion' else 4,'stage':'bound','node':'a','arg':'left','source':'r','field':'value','value':4}
    assert actual['authored_plan_hash']==hashlib.sha256(canonical(fixture['plan']).encode()).hexdigest()
def verify():
    expected=json.loads((ROOT/'oracle.json').read_text());fixtures=json.loads((ROOT/'fixtures.json').read_text());paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for path in paths:
        raw=json.loads(path.read_text());assert list(raw)==list(expected)
        for case in expected:
            validate(case,raw[case],expected,fixtures[case])
            for name,digest in raw[case]['source_binding'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest
    raw=json.loads(paths[-1].read_text());rejected=0
    for kind in ('final','call','rejection','trace','proposal'):
        case='normal' if kind in ('final','proposal') else 'string-value';mutant=copy.deepcopy(raw[case])
        if kind=='final':mutant['result']['final']=103
        if kind=='call':mutant['result']['calls'].append({'node':'a','tool':'add','args':{'left':4,'right':3}})
        if kind=='rejection':mutant['result']['rejection']['phase']='preflight'
        if kind=='trace':mutant['result']['trace'].pop()
        if kind=='proposal':mutant['result']['results']['r'].pop('proposed_plan')
        try:validate(case,mutant,expected,fixtures[case])
        except AssertionError:rejected+=1
        else:raise AssertionError('oracle accepted corruption')
    print(json.dumps({'strict_cases':6,'strict_completed':1,'expected_refusals':5,'bad_comparisons':2,'mutants_rejected':rejected,'recorded_runs':len(paths),'scope':'fixed typed-dataflow only'}))
if __name__=='__main__':verify()
