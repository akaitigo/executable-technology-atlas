"""Atlas: read saved calculation using literal expectations and separate algebra; no model execution."""
import argparse
import copy
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def multiply(a, b):
    return [[sum(a[i][r] * b[r][j] for r in range(2)) for j in range(2)] for i in range(2)]


def power(a, n):
    result = [[F(1), F(0)], [F(0), F(1)]]
    while n:
        if n % 2:
            result = multiply(result, a)
        a = multiply(a, a)
        n //= 2
    return result


def state_from_independent_formula(name, k):
    if name == 'current-exact':
        return F(0) if k == 0 else F(1, 2)
    if name == 'fixed-noise':
        return F(0) if k == 0 else (F(3, 8) if k % 2 else F(5, 8))
    if name == 'delayed-one':
        a = power([[F(1, 2), F(-1, 2)], [F(1), F(0)]], k)
        return F(1, 2) - (a[0][0] + a[0][1]) / 2
    j = k // 2
    return (1 - F(1, 4) ** j) / 3 if k % 2 == 0 else F(2, 3) - F(1, 4) ** j / 6


def check(result):
    hand = json.loads((ROOT / 'hand-oracle.json').read_text())
    assert type(result['schema']) is int and result['schema'] == 1 and result['status'] == 'observed'
    assert type(result['priority_observed']) is int and result['priority_observed'] == 10
    assert result['fixture_sha256'] == sha(ROOT / 'fixtures.json')
    assert canonical(result['scope']) == canonical({'model_only': True, 'exact_rational': True,
        'real_device_runs': 0, 'sensor_measurements': 0, 'random_draws': 0, 'network_requests': 0,
        'browser_executed': False, 'server_started': False})
    assert canonical(result['cases']) == canonical(hand['cases'])
    assert canonical(result['quantization_cases']) == canonical(hand['quantization_cases'])
    reasons = [('schema-bool', 'TYPE'), ('updates-float', 'TYPE'), ('missing-field', 'SCHEMA'),
               ('extra-field', 'SCHEMA'), ('wrong-initial-history', 'FIXED_INPUT'), ('wrong-gain', 'FIXED_INPUT'),
               ('plant-a-float', 'TYPE'), ('wrong-unit', 'FIXED_INPUT'), ('negative-delay', 'FIXED_INPUT'),
               ('missing-case', 'SCHEMA'), ('extra-case-key', 'SCHEMA'), ('short-noise', 'SCHEMA'),
               ('noise-float', 'TYPE'), ('noise-noncanonical', 'FIXED_INPUT'),
               ('zero-quantization-step', 'FIXED_INPUT'), ('even-rounding', 'FIXED_INPUT'),
               ('unknown-case', 'UNKNOWN_CASE')]
    assert canonical(result['input_refusals']) == canonical([{'id': n, 'status': 'INPUT_REFUSED',
        'reason': why, 'updates': 0, 'boundaries': [], 'value': None} for n, why in reasons])
    for case in result['cases']:
        for point in case['boundaries']:
            k = point['k']
            x = state_from_independent_formula(case['id'], k)
            assert F(point['true_state']) == x
            m, u = F(point['measurement']), F(point['control_input'])
            assert F(point['measurement_error']) == m - x
            assert F(point['true_error']) == 1 - x and F(point['control_error']) == 1 - m
            assert u + m == 1
            if k < 6:
                assert point['input_applied'] is True
                assert F(point['next_state']) == state_from_independent_formula(case['id'], k + 1)
            else:
                assert point['input_applied'] is False and point['next_state'] is None
    for point in result['quantization_cases']:
        x, y = F(point['input']), F(point['output'])
        assert y.denominator == 1 and abs(x - y) <= F(1, 2)
        if abs(x - y) == F(1, 2):
            assert abs(y) > abs(x)
    return {'cases': 4, 'boundaries': 28, 'updates': 24, 'terminal_unapplied_inputs': 4,
            'quantization_cases': 9, 'input_refusals': 17}


def mutants(result):
    changes = [
        ('true-state-overwritten', lambda r: r['cases'][2]['boundaries'][1].update(true_state='1/8')),
        ('delay-uses-current', lambda r: r['cases'][1]['boundaries'][1].update(source_index=1)),
        ('initial-history-changed', lambda r: r['cases'][1]['boundaries'][0].update(source_value='1')),
        ('noise-added-to-plant', lambda r: r['cases'][2]['boundaries'][0].update(next_state='5/8')),
        ('measurement-equals-true', lambda r: r['cases'][2]['boundaries'][0].update(measurement='0')),
        ('measurement-error-sign', lambda r: r['cases'][2]['boundaries'][0].update(measurement_error='-1/4')),
        ('true-error-erased', lambda r: r['cases'][0]['boundaries'][1].update(true_error='0')),
        ('control-error-uses-true', lambda r: r['cases'][2]['boundaries'][0].update(control_error='1')),
        ('half-rounds-even', lambda r: r['cases'][3]['boundaries'][1].update(measurement='0')),
        ('negative-half-rounds-zero', lambda r: r['quantization_cases'][2].update(output='0')),
        ('terminal-applied', lambda r: r['cases'][0]['boundaries'][6].update(input_applied=True)),
        ('terminal-next-is-zero', lambda r: r['cases'][0]['boundaries'][6].update(next_state='0')),
        ('fraction-changed-to-float', lambda r: r['cases'][0]['boundaries'][1].update(true_state=0.5)),
        ('missing-boundary', lambda r: r['cases'][1]['boundaries'].pop()),
        ('refusal-updated', lambda r: r['input_refusals'][0].update(updates=1)),
        ('real-device-claim', lambda r: r['scope'].update(real_device_runs=1)),
    ]
    rejected = []
    for name, change in changes:
        candidate = copy.deepcopy(result)
        change(candidate)
        try:
            check(candidate)
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected.append(name)
        else:
            raise AssertionError('changed record accepted: ' + name)
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', help='saved calculation directory relative to this lesson')
    args = parser.parse_args()
    directory = (ROOT / args.run).resolve()
    assert ROOT / 'observations' in directory.parents
    report = json.loads((directory / 'report.json').read_text())
    assert report['status'] == 'observed' and report['child_reaped'] and report['exit_code'] == 0
    assert report['result_sha256'] == sha(directory / 'result.json')
    for name, digest in report['sources'].items():
        assert sha(ROOT / name) == digest, name
    for name in ['stdout', 'stderr']:
        assert report[name + '_sha256'] == sha(directory / (name + '.txt'))
    result = json.loads((directory / 'result.json').read_text())
    assert canonical(json.loads((directory / 'stdout.txt').read_text())) == canonical(result)
    for name, digest in json.loads((ROOT / 'contract-lock.json').read_text())['files'].items():
        assert sha(ROOT / name) == digest, name
    print(json.dumps({'title': 'Atlas saved measurement feedback verification', 'passed': True,
                      **check(result), 'mutation_refusals': mutants(result), 'model_rerun': False,
                      'source_sha256': sha(Path(__file__)), 'run': args.run}))


if __name__ == '__main__':
    main()
