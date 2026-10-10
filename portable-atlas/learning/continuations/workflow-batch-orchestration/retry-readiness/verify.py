"""Atlas: inspect saved results against fixed hand intervals; never run the model."""
import argparse, copy, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def historical_source(name, expected):
    current = ROOT / name
    if sha(current) == expected:
        return current
    item = json.loads((ROOT / 'observations/historical-source-map.json').read_text())['files'][name]
    assert item['sha256'] == expected, name
    saved = (ROOT / item['path']).resolve()
    assert ROOT in saved.parents and sha(saved) == expected, name
    return saved


def check(result):
    hand = json.loads((ROOT / 'hand-oracle.json').read_text())
    assert result['schema'] == 1 and type(result['schema']) is int and result['status'] == 'observed'
    assert result['priority_observed'] == 10 and result['fixture_sha256'] == sha(ROOT / 'fixtures.json')
    assert canonical(result['scope']) == canonical({'model_only': True, 'logical_time': True,
        'real_sleep_calls': 0, 'network_requests': 0, 'worker_runs': 0, 'airflow_runs': 0,
        'browser_executed': False, 'server_started': False})
    assert canonical(result['cases']) == canonical(hand['cases'])
    reasons = [('schema-bool','INTEGER_REQUIRED'), ('budget-float','INTEGER_REQUIRED'),
        ('delay-bool','INTEGER_REQUIRED'), ('missing-field','SCHEMA'), ('extra-field','SCHEMA'),
        ('reverse-edge','FIXED_INPUT'), ('negative-budget','FIXED_INPUT'), ('zero-delay','FIXED_INPUT'),
        ('different-duration','FIXED_INPUT'), ('different-result','FIXED_INPUT'), ('missing-case','CASE_SCHEMA'),
        ('unknown-error','FAILURE_LABEL'), ('nonstring-error','FAILURE_LABEL'), ('future-success-changed','FIXED_CASE'),
        ('unknown-mode','FIXED_CASE'), ('case-extra-field','CASE_SCHEMA'), ('unknown-case','UNKNOWN_CASE')]
    assert canonical(result['input_refusals']) == canonical([{'id': name, 'status': 'INPUT_REFUSED',
        'reason': reason, 'b_calls': 0, 'd_calls': 0, 'boundaries': [], 'value': None} for name, reason in reasons])
    # Independent interval containment and algebra, without importing the event-loop implementation.
    for case, fixed in zip(result['cases'], hand['cases']):
        for point in case['boundaries']:
            t = point['t']
            begun = sum(a['start'] <= t for a in fixed['b_attempts'])
            assert point['attempts_started'] == begun and point['retries_left'] == 2 - max(0, begun - 1)
            assert (point['b_state'] == 'running') == any(a['start'] <= t < a['end'] for a in fixed['b_attempts'])
            assert (point['d_state'] == 'running') == any(a['start'] <= t < a['end'] for a in fixed['d_attempts'])
            completed = [a for a in fixed['b_attempts'] if a['end'] <= t and a['outcome'] == 'SUCCESS']
            assert point['b_value'] == (7 if completed else None)
            assert point['d_value'] == (14 if any(a['end'] <= t for a in fixed['d_attempts']) else None)
        for failure in case['failure_decisions']:
            assert failure['retryable'] == (failure['error'] == 'TRANSIENT')
            assert failure['retry_planned'] == (failure['retryable'] and failure['remaining_retries'] > 0)
            assert failure['next_due'] == (failure['at'] + 2 if failure['retry_planned'] else None)
        for comparison in case['retry_checks']:
            assert comparison['eligible'] == (comparison['at'] >= comparison['due'])
    assert sum(len(c['boundaries']) for c in result['cases']) == 21
    assert sum(c['b_calls'] for c in result['cases']) == 8 and sum(c['d_calls'] for c in result['cases']) == 1
    return {'cases': 4, 'boundaries': 21, 'b_calls': 8, 'd_calls': 1,
            'failure_decisions': 6, 'retry_checks': 12, 'input_refusals': 17}


def mutants(result):
    changes = [
        ('early-due', lambda r: r['cases'][0]['failure_decisions'][0].update(next_due=2)),
        ('before-is-eligible', lambda r: r['cases'][0]['retry_checks'][1].update(eligible=True)),
        ('equal-is-ineligible', lambda r: r['cases'][0]['retry_checks'][2].update(eligible=False)),
        ('budget-decreased-while-waiting', lambda r: r['cases'][0]['boundaries'][1].update(retries_left=1)),
        ('budget-not-decreased-at-start', lambda r: r['cases'][0]['boundaries'][3].update(retries_left=2)),
        ('permanent-retryable', lambda r: r['cases'][1]['failure_decisions'][0].update(retryable=True)),
        ('future-result-leak', lambda r: r['cases'][1]['boundaries'][1].update(b_value=7)),
        ('terminal-new-due', lambda r: r['cases'][2]['failure_decisions'][2].update(next_due=9)),
        ('fault-marked-normal', lambda r: r['cases'][3].update(classification='NORMAL')),
        ('sticky-block-cleared', lambda r: r['cases'][3]['boundaries'][4].update(d_state='pending')),
        ('fake-downstream-call', lambda r: r['cases'][3].update(d_calls=1)),
        ('missing-failure', lambda r: r['cases'][2]['failure_decisions'].pop()),
        ('float-tick', lambda r: r['cases'][0]['boundaries'][3].update(t=3.0)),
        ('refusal-called-task', lambda r: r['input_refusals'][0].update(b_calls=1)),
        ('live-scope-claim', lambda r: r['scope'].update(airflow_runs=1)),
    ]
    rejected = []
    for name, change in changes:
        candidate = copy.deepcopy(result); change(candidate)
        try: check(candidate)
        except (AssertionError, KeyError, TypeError, ValueError): rejected.append(name)
        else: raise AssertionError('changed record accepted: ' + name)
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', help='saved directory relative to this lesson')
    args = parser.parse_args(); directory = (ROOT / args.run).resolve()
    assert ROOT / 'observations' in directory.parents
    report = json.loads((directory / 'report.json').read_text())
    assert report['status'] == 'observed' and report['child_reaped'] and report['exit_code'] == 0
    assert report['result_sha256'] == sha(directory / 'result.json')
    source_paths = {name: str(historical_source(name, digest).relative_to(ROOT)) for name, digest in report['sources'].items()}
    for name in ['stdout', 'stderr']: assert report[name + '_sha256'] == sha(directory / (name + '.txt'))
    result = json.loads((directory / 'result.json').read_text())
    assert canonical(json.loads((directory / 'stdout.txt').read_text())) == canonical(result)
    contract_paths = {name: str(historical_source(name, digest).relative_to(ROOT)) for name, digest in
                      json.loads((ROOT / 'contract-lock.json').read_text())['files'].items()}
    print(json.dumps({'title': 'Atlas saved retry readiness verification', 'passed': True, **check(result),
        'mutation_refusals': mutants(result), 'model_rerun': False, 'source_sha256': sha(Path(__file__)),
        'execution_source_paths': source_paths, 'contract_source_paths': contract_paths, 'run': args.run}))


if __name__ == '__main__': main()
