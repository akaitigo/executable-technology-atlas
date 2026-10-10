"""Atlas: producerをimportせず、固定手表と保存入力を照合する。"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check(saved):
    expected = json.loads((ROOT / 'expected.json').read_text())
    fixture = json.loads((ROOT / 'cases.json').read_text())
    consumer = json.loads((ROOT / 'consumer-policy.json').read_text())
    count = 0
    def eq(a, b):
        nonlocal count
        count += 1
        assert a == b, (a, b)
    eq([x['id'] for x in saved['cases']], [x['id'] for x in expected['cases']])
    artifact = (ROOT / 'fixtures/artifact.bin').read_bytes()
    eq(artifact, b'abc')
    for row, wanted, case in zip(saved['cases'], expected['cases'], fixture['cases']):
        raw = (ROOT / case['fixture']).read_bytes()
        bundle = json.loads(raw)
        eq(row['fixtureSha256'], hashlib.sha256(raw).hexdigest())
        eq(row['bundle_before'], bundle)
        eq(row['bundle_after'], bundle)
        eq(row['consumer_policy_before'], consumer)
        eq(row['consumer_policy_after'], consumer)
        eq(row['artifact'], {'hex': '616263', 'size': 3, 'sha256': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'})
        for method in ('independent_policy', 'bundle_policy_fault'):
            eq(row[method], wanted[method])
            for key in expected['checkOrder']:
                eq(row[method]['checks'][key], wanted[method]['checks'][key])
            eq(row[method]['signatureCheck'], 'not-run')
            eq(row[method]['authenticatedBuilder'], None)
            eq(row[method]['releaseDecision'], 'out-of-scope')
    a, b = [next(x for x in saved['cases'] if x['id'] == ident) for ident in fixture['equalClaimsPair']]
    eq(a['bundle_before']['claims'], b['bundle_before']['claims'])
    eq(a['independent_policy'], b['independent_policy'])
    eq([a['bundle_policy_fault']['claimsMatchPolicy'], b['bundle_policy_fault']['claimsMatchPolicy']], [False, True])
    eq(sum(x['independent_policy']['claimsMatchPolicy'] for x in saved['cases']), 1)
    eq(sum(x['bundle_policy_fault']['claimsMatchPolicy'] for x in saved['cases']), 2)
    return count


def mutation_checks(saved):
    changes = [
        ('missing-case', lambda d: d['cases'].pop()),
        ('builder-mismatch-hidden', lambda d: d['cases'][1]['independent_policy']['checks'].__setitem__('builder_id', True)),
        ('unrecognized-parameter-hidden', lambda d: d['cases'][5]['independent_policy']['checks'].__setitem__('parameter_keys', True)),
        ('parameter-values-redefined', lambda d: d['cases'][5]['independent_policy']['checks'].__setitem__('parameter_values', False)),
        ('bundle-policy-trusted-by-strict', lambda d: d['cases'][6].__setitem__('independent_policy', copy.deepcopy(d['cases'][6]['bundle_policy_fault']))),
        ('claims-match-as-authentication', lambda d: d['cases'][0]['independent_policy'].__setitem__('authenticatedBuilder', 'verified')),
        ('input-mutated', lambda d: d['cases'][0]['consumer_policy_after'].__setitem__('builder_id', 'changed')),
        ('wrong-artifact', lambda d: d['cases'][0]['artifact'].__setitem__('hex', '616264')),
    ]
    result = []
    for name, mutate in changes:
        bad = copy.deepcopy(saved)
        mutate(bad)
        try:
            check(bad)
        except (AssertionError, KeyError, TypeError):
            result.append({'name': name, 'rejected': True})
        else:
            raise AssertionError('undetected mutation: ' + name)
    return result
