"""Atlas: check saved bytes with fixed hand expectations and half-open quantization bins."""
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


def check(result):
    hand = json.loads((ROOT / 'hand-oracle.json').read_text())
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    assert type(result['schema_version']) is int and result['schema_version'] == 1
    assert result['status'] == 'observed'
    assert type(result['priority_observed']) is int and result['priority_observed'] == 10
    assert result['fixture_sha256'] == sha(ROOT / 'fixtures.json')
    for field in ['scope', 'central', 'boundaries']:
        assert canonical(result[field]) == canonical(hand[field]), field
    for group in ['central', 'boundaries']:
        for case, inp in zip(result[group], fixture[group]):
            maximum = 2 ** case['bits'] - 1
            exact_before = {'depth': '1', 'winner': None}
            integer_before = {'code': maximum, 'winner': None}
            for row, fragment in zip(case['trace'], inp['request']['fragments']):
                z = F(fragment['z']); q = row['code']
                # This validator locates a bin; it does not call the quotient/remainder producer.
                bins = [j for j in range(maximum + 1)
                        if F(2 * j - 1, 2 * maximum) <= z
                        and (z < F(2 * j + 1, 2 * maximum) or (j == maximum and z == 1))]
                assert bins == [q]
                assert F(row['reconstructed']) == F(q, maximum)
                assert F(row['rounding_error']) == F(q, maximum) - z
                assert row['exact_before'] == exact_before and row['quantized_before'] == integer_before
                ep = z < F(exact_before['depth']); qp = q < integer_before['code']
                assert row['exact_pass'] is ep and row['quantized_pass'] is qp
                if ep: exact_before = {'depth': str(z), 'winner': fragment['id']}
                if qp: integer_before = {'code': q, 'winner': fragment['id']}
                assert row['exact_after'] == exact_before and row['quantized_after'] == integer_before
            assert case['exact_final'] == exact_before and case['quantized_final'] == integer_before
    reasons = [('missing-group','SCHEMA'),('extra-field','SCHEMA'),('schema-bool','TYPE'),
        ('unknown-case','UNKNOWN_CASE'),('bits-bool','TYPE'),('bits-float','TYPE'),('bits-outside','BITS'),
        ('request-extra','SCHEMA'),('missing-fragment','SCHEMA'),('unknown-fragment','FRAGMENT_ID'),
        ('duplicate-fragment','DUPLICATE_FRAGMENT'),('depth-float','TYPE'),('depth-noncanonical','RATIONAL'),
        ('zero-denominator','RATIONAL'),('negative-denominator','RATIONAL'),('not-finite','RATIONAL'),
        ('depth-negative','DEPTH_RANGE'),('depth-above-one','DEPTH_RANGE'),
        ('different-fixed-depth','FIXED_INPUT'),('late-invalid-input','RATIONAL')]
    assert canonical(result['input_refusals']) == canonical([
        {'id': n, 'status': 'INPUT_REFUSED', 'reason': reason, 'draws': 0, 'trace': [], 'value': None}
        for n, reason in reasons])
    return {'central_cases': 6, 'boundaries': 12, 'fragment_rows': 24, 'comparisons': 48, 'input_refusals': 20}


def mutants(result):
    changes = [
        ('same-bin-lost', lambda r: r['central'][0]['trace'][1].update(code=4)),
        ('true-depth-rounded', lambda r: r['central'][0]['trace'][0].update(z='3/7')),
        ('scaled-wrong', lambda r: r['central'][0]['trace'][0].update(scaled='3')),
        ('round-error-sign', lambda r: r['central'][0]['trace'][0].update(rounding_error='-1/35')),
        ('equal-overwrites', lambda r: r['central'][0]['trace'][1].update(quantized_pass=True)),
        ('ba-winner-from-truth', lambda r: r['central'][1]['quantized_final'].update(winner='A')),
        ('before-state-wrong', lambda r: r['central'][1]['trace'][1]['quantized_before'].update(code=4)),
        ('tie-order-hidden', lambda r: r['central'][5]['exact_final'].update(winner='A')),
        ('half-rounds-down', lambda r: r['boundaries'][2]['trace'][0].update(code=3)),
        ('clear-bin-accepted', lambda r: r['boundaries'][4]['trace'][0].update(quantized_pass=True)),
        ('far-end-accepted', lambda r: r['boundaries'][5]['trace'][0].update(exact_pass=True)),
        ('background-is-fragment', lambda r: r['boundaries'][11]['quantized_final'].update(winner='F')),
        ('missing-row', lambda r: r['central'][0]['trace'].pop()),
        ('code-float', lambda r: r['central'][0]['trace'][0].update(code=3.0)),
        ('refusal-draws', lambda r: r['input_refusals'][0].update(draws=1)),
        ('gpu-claim', lambda r: r['scope'].update(gpu_api_calls=1)),
    ]
    rejected = []
    for name, change in changes:
        candidate = copy.deepcopy(result); change(candidate)
        try: check(candidate)
        except (AssertionError, KeyError, TypeError, ValueError): rejected.append(name)
        else: raise AssertionError('changed record accepted: ' + name)
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('run'); args = parser.parse_args()
    directory = (ROOT / args.run).resolve(); assert ROOT / 'observations' in directory.parents
    report = json.loads((directory / 'report.json').read_text())
    assert report['status'] == 'observed' and report['child_reaped'] and report['exit_code'] == 0
    assert report['result_sha256'] == sha(directory / 'result.json')
    for name, digest in report['sources'].items(): assert sha(ROOT / name) == digest, name
    for name in ['stdout', 'stderr']: assert report[name + '_sha256'] == sha(directory / (name + '.txt'))
    for name, digest in json.loads((ROOT / 'contract-lock.json').read_text())['files'].items():
        assert sha(ROOT / name) == digest, name
    result = json.loads((directory / 'result.json').read_text())
    assert canonical(json.loads((directory / 'stdout.txt').read_text())) == canonical(result)
    print(json.dumps({'title': 'Atlas saved depth verification', 'passed': True, **check(result),
                      'mutation_refusals': mutants(result), 'model_rerun': False,
                      'source_sha256': sha(Path(__file__)), 'run': args.run}))


if __name__ == '__main__':
    main()
