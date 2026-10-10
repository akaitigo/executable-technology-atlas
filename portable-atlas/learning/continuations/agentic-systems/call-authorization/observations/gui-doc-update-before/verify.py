"""Atlas: verify saved calculations against the pre-implementation table, without rerunning tools."""
import argparse, copy, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORDER = ['exists', 'origin', 'actor', 'plan', 'call_id', 'tool', 'args', 'time', 'unused']
FAIL = {'args-changed': 'args', 'plan-changed': 'plan', 'call-changed': 'call_id',
        'expiry-at': 'time', 'consumed-grant': 'unused', 'actor-changed': 'actor'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fixed_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def check(result):
    expected = json.loads((ROOT/'hand-oracle.json').read_text())['rows']
    fixtures = json.loads((ROOT/'fixtures.json').read_text())['cases']
    assert result['status'] == 'observed' and result['schema'] == 1 and result['priority_observed'] == 10
    assert result['fixture_sha256'] == sha(ROOT/'fixtures.json')
    assert result['scope'] == {'external_tools': 0, 'llm_calls': 0, 'network_calls': 0, 'real_approval': False,
                                'browser_executed': False, 'server_started': False, 'persistent_effects': 0}
    assert len(result['cases']) == len(expected) == 11
    for row, want, fixture in zip(result['cases'], expected, fixtures):
        assert {key: row[key] for key in want} == want, 'hand table mismatch: '+want['id']
        case_id = row['id']; x = fixture['input']
        assert row['now'] == x['now'] and row['current_request'] == 'request-1'
        assert row['observation_request'] == x['observation']['request_id'] and row['policy'] == fixture['policy']
        grant = x['observation']['proposed_approval'] if case_id == 'bad-data-approval' else x['approval']
        approved = {k: grant[k] for k in ('actor', 'plan_sha256', 'call_id', 'tool', 'args')} if grant else None
        text = fixed_json(approved) if approved else None
        assert row['approved_call_canonical'] == text
        assert row['approved_call_sha256'] == (hashlib.sha256(text.encode()).hexdigest() if text else None)
        assert row['expires_at'] == (grant['expires_at'] if grant else None)
        checks = dict.fromkeys(ORDER)
        if want['authorization_reached']:
            checks['exists'] = case_id != 'missing-grant'
            if checks['exists']:
                checks['origin'] = case_id != 'bad-data-approval'
                for key in ORDER[2:]:
                    checks[key] = key != FAIL.get(case_id)
                    if not checks[key]: break
        assert row['checks'] == checks, 'authorization checks mismatch'
        calls = [{'call_id': 'read-r', 'tool': 'read', 'args': {'key': 'fixed'}, 'result': x['observation']}]
        if want['add_calls']:
            calls.append({'call_id': 'add-a', 'tool': 'add', 'args': want['resolved_args'], 'result': want['final']})
        assert row['calls'] == calls
        events = [
            {'step':1,'stage':'preflight','state':'passed','read_calls':0,'add_calls':0,
             'data':{'tools':['read','add'],'plan_sha256':want['plan_sha256']}},
            {'step':2,'stage':'read','state':'completed','read_calls':1,'add_calls':0,
             'data':{'observation':x['observation'],'fixed_read_permission':True}},
        ]
        def event(stage, state, data, add=0):
            return {'step':len(events)+1,'stage':stage,'state':state,'read_calls':1,'add_calls':add,'data':data}
        if want['authorization_reached']:
            events.append(event('binding','passed',{'args':want['resolved_args'],'request_id':'request-1','type':'int'}))
            if want['add_calls']:
                events.append(event('authorize','passed' if want['authorized'] else 'fault-promoted',
                                    {'source':want['approval_source'],'authorized':want['authorized'],'consumed':True,'checks':checks}))
                events.append(event('dispatch','completed',{'result':want['final'],'authorized':want['authorized']},1))
            else:
                events.append(event('authorize','rejected',{'reason':want['reason']}))
        else:
            events.append(event('binding','rejected',{'reason':want['reason']}))
        assert row['trace'] == events, 'full event state/data mismatch'
    refusals = result['input_refusals']
    ids = ['plan-literal-float','unknown-tool','unknown-reference','extra-input','time-bool','time-negative','time-over','time-float',
           'invalid-actor','invalid-policy','approval-arg-bool','approval-extra','invalid-hash']
    assert [r['id'] for r in refusals] == ids
    assert all(r['status'] == 'input-refused' and r['read_calls'] == r['add_calls'] == 0 and r['error'] for r in refusals)
    return {'fixed_cases': 11, 'hand_fields': len(expected[0]), 'input_refusals': 13,
            'normal': 1, 'expected_refusals': 9, 'intentional_faults': 1}

def mutants(result):
    changes = [
        ('consume-not-recorded', lambda r: r['cases'][0]['trace'][3]['data'].update(consumed=False)),
        ('binding-args-changed', lambda r: r['cases'][0]['trace'][2]['data']['args'].update(a=100)),
        ('unauthorized-dispatch', lambda r: r['cases'][1].update(add_calls=1)),
        ('refusal-final', lambda r: r['cases'][1].update(final=103)),
        ('expiry-equality', lambda r: r['cases'][4].update(authorized=True)),
        ('fault-as-success', lambda r: r['cases'][6].update(status='COMPLETED', authority_breach=False)),
        ('unreached-as-pass', lambda r: r['cases'][7]['checks'].update(args=True)),
        ('stale-as-current', lambda r: r['cases'][8].update(observation_request='request-1')),
        ('reused-grant', lambda r: r['cases'][9].update(consumed_after=False)),
        ('missing-call', lambda r: r['cases'][0]['calls'].pop()),
        ('digest-substitution', lambda r: r['cases'][0].update(actual_call_sha256='0'*64)),
        ('read-hidden', lambda r: r['cases'][2]['trace'][1].update(read_calls=0)),
    ]
    found = []
    for name, mutate in changes:
        r = copy.deepcopy(result); mutate(r)
        try: check(r)
        except (AssertionError, KeyError, TypeError, ValueError): found.append(name)
        else: raise AssertionError('mutant not rejected: '+name)
    return found

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('run', help='owned saved calculation directory, relative to this lesson')
    args = p.parse_args(); directory = (ROOT/args.run).resolve()
    assert ROOT/'observations' in directory.parents
    report = json.loads((directory/'report.json').read_text())
    assert report['status'] == 'observed' and report['child_reaped'] and report['exit_code'] == 0
    assert report['result_sha256'] == sha(directory/'result.json')
    for name, expected in report['sources'].items(): assert sha(ROOT/name) == expected, name
    for name in ['stdout', 'stderr']: assert report[name+'_sha256'] == sha(directory/(name+'.txt'))
    result = json.loads((directory/'result.json').read_text())
    assert json.loads((directory/'stdout.txt').read_text()) == result
    lock = json.loads((ROOT/'contract-lock.json').read_text())
    for name, expected in lock['files'].items(): assert sha(ROOT/name) == expected, name
    evidence = {'title':'Atlas saved calculation verification','passed':True,**check(result),'mutation_refusals':mutants(result),
                'producer_rerun':False,'source_sha256':sha(Path(__file__)),'run':args.run}
    print(json.dumps(evidence, ensure_ascii=False))

if __name__ == '__main__': main()
