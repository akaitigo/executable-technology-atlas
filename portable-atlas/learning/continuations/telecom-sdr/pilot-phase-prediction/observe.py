"""Atlas: one finite saved calculation; comparison truth stays outside the receiver."""
import copy
import datetime
import hashlib
import json
import os
import platform
from fractions import Fraction as F
from pathlib import Path
from model import receive, mul, encoded

ROOT = Path(__file__).resolve().parent
SCOPE = {'model_only': True, 'exact_rational': True, 'real_device_runs': 0, 'rf_samples': 0,
         'matlab_runs': 0, 'pll_implemented': False, 'random_draws': 0, 'network_requests': 0,
         'browser_executed': False, 'server_started': False}


def refusal_inputs(base):
    changes = [
        ('missing-field', 'SCHEMA', lambda x: x.pop('known_pilots')),
        ('extra-truth', 'SCHEMA', lambda x: x.update(true_channel=[])),
        ('extra-case-id', 'SCHEMA', lambda x: x.update(case_id='constant-rate')),
        ('pilot-bit-bool', 'TYPE', lambda x: x['known_pilots'][0].update(bit=False)),
        ('pilot-bit-one', 'FIXED_INPUT', lambda x: x['known_pilots'][0].update(bit=1)),
        ('pilot-index-float', 'TYPE', lambda x: x['known_pilots'][1].update(n=1.0)),
        ('pilot-gap', 'FIXED_INPUT', lambda x: x['known_pilots'][1].update(n=2)),
        ('short-pilots', 'SCHEMA', lambda x: x['received_pilots'].pop()),
        ('short-payload', 'SCHEMA', lambda x: x['received_payload'].pop()),
        ('payload-index-bool', 'TYPE', lambda x: x['payload_indices'].__setitem__(0, True)),
        ('payload-index-order', 'FIXED_INPUT', lambda x: x.update(payload_indices=[3, 2, 4, 5])),
        ('fraction-float', 'TYPE', lambda x: x['received_payload'][0].__setitem__(0, 1.0)),
        ('fraction-noncanonical', 'RATIONAL', lambda x: x['received_payload'][0].__setitem__(0, '2/2')),
        ('fraction-zero-denominator', 'RATIONAL', lambda x: x['received_payload'][0].__setitem__(0, '1/0')),
        ('fraction-nan', 'RATIONAL', lambda x: x['received_payload'][0].__setitem__(0, 'NaN')),
        ('pilot-not-unit', 'AMPLITUDE', lambda x: x['received_pilots'][0].__setitem__(0, '2')),
        ('payload-zero', 'AMPLITUDE', lambda x: x['received_payload'].__setitem__(0, ['0', '0'])),
    ]
    for name, reason, change in changes:
        value = copy.deepcopy(base)
        change(value)
        yield name, reason, value, 'hold-latest'
    yield 'unknown-method', 'UNKNOWN_METHOD', copy.deepcopy(base), 'pll'


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('Atlas: actual nice 10 required before finite calculation')
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    truths = json.loads((ROOT / 'comparison-truth.json').read_text())
    cases = []
    for item, truth in zip(fixture['cases'], truths['cases']):
        assert item['id'] == truth['id']
        # Only the harness can see a true channel or the payload's correct bits.
        expected_rx = [encoded(mul((F(1 - 2 * bit), F(0)), tuple(F(x) for x in channel)))
                       for bit, channel in zip(truth['payload_bits'], truth['channel'][2:])]
        assert expected_rx == item['request']['received_payload']
        methods = []
        for method in fixture['methods']:
            receiver = receive(copy.deepcopy(item['request']), method)
            bits = receiver['decoded_bits']
            errors = None if bits is None else [n for n, bit, expected in zip([2, 3, 4, 5], bits, truth['payload_bits']) if bit != expected]
            comparison = {'truth_bits': list(truth['payload_bits']), 'compared_bits': 0 if bits is None else 4,
                          'errors': None if bits is None else len(errors), 'error_indices': errors}
            methods.append({'receiver': receiver, 'comparison': comparison})
        cases.append({'id': item['id'], 'pilot_z': copy.deepcopy(item['request']['received_pilots']), 'methods': methods})
    refusals = []
    for name, reason, request, method in refusal_inputs(fixture['cases'][0]['request']):
        try:
            receive(request, method)
        except ValueError as e:
            assert str(e) == reason, (name, str(e), reason)
            refusals.append({'id': name, 'status': 'INPUT_REFUSED', 'reason': reason,
                             'demodulated_count': 0, 'rows': [], 'value': None})
        else:
            raise AssertionError('invalid receiver input accepted: ' + name)
    sha = lambda name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    result = {'title': 'Atlas telecom phase saved calculation', 'schema': 1, 'status': 'observed',
              'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'runtime': {'python': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine()},
              'priority_observed': priority, 'fixture_sha256': sha('fixtures.json'),
              'comparison_truth_sha256': sha('comparison-truth.json'), 'cases': cases,
              'input_refusals': refusals, 'scope': SCOPE}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
