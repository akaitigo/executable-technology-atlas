"""Atlas: save one finite calculation after the actual nice-10 guard."""
import copy
import datetime
import hashlib
import json
import os
import platform
from fractions import Fraction
from pathlib import Path
from model import execute, quantize

ROOT = Path(__file__).resolve().parent


def refusal_inputs(base):
    changes = [
        ('schema-bool', 'TYPE', lambda f: f.update(schema=True)),
        ('updates-float', 'TYPE', lambda f: f.update(updates=6.0)),
        ('missing-field', 'SCHEMA', lambda f: f.pop('gain')),
        ('extra-field', 'SCHEMA', lambda f: f.update(real_device=True)),
        ('wrong-initial-history', 'FIXED_INPUT', lambda f: f.update(initial_history='1')),
        ('wrong-gain', 'FIXED_INPUT', lambda f: f.update(gain='2')),
        ('plant-a-float', 'TYPE', lambda f: f.update(plant_a=0.5)),
        ('wrong-unit', 'FIXED_INPUT', lambda f: f.update(unit='measured volts')),
        ('negative-delay', 'FIXED_INPUT', lambda f: f['cases'][1].update(delay_samples=-1)),
        ('missing-case', 'SCHEMA', lambda f: f['cases'].pop()),
        ('extra-case-key', 'SCHEMA', lambda f: f['cases'][0].update(filter=True)),
        ('short-noise', 'SCHEMA', lambda f: f['cases'][2]['noise'].pop()),
        ('noise-float', 'TYPE', lambda f: f['cases'][2]['noise'].__setitem__(0, 0.25)),
        ('noise-noncanonical', 'FIXED_INPUT', lambda f: f['cases'][2]['noise'].__setitem__(0, '2/8')),
        ('zero-quantization-step', 'FIXED_INPUT', lambda f: f['cases'][3].update(quantization_step='0')),
        ('even-rounding', 'FIXED_INPUT', lambda f: f.update(quantization_rule='nearest-ties-even')),
    ]
    for name, reason, change in changes:
        value = copy.deepcopy(base)
        change(value)
        yield name, reason, value, 'current-exact'
    yield 'unknown-case', 'UNKNOWN_CASE', copy.deepcopy(base), 'live-device'


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('Atlas: actual nice 10 is required before model execution')
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    cases = [execute(fixture, item['id']) for item in fixture['cases']]
    probes = ['-3/2', '-51/100', '-1/2', '-49/100', '0', '49/100', '1/2', '51/100', '3/2']
    quantization = [{'input': x, 'output': str(quantize(Fraction(x)))} for x in probes]
    refusals = []
    for name, reason, value, case_id in refusal_inputs(fixture):
        try:
            execute(value, case_id)
        except ValueError as e:
            assert str(e) == reason, (name, str(e), reason)
            refusals.append({'id': name, 'status': 'INPUT_REFUSED', 'reason': reason,
                             'updates': 0, 'boundaries': [], 'value': None})
        else:
            raise AssertionError('invalid input accepted: ' + name)
    result = {'title': 'Atlas measurement feedback saved calculation', 'schema': 1, 'status': 'observed',
              'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'runtime': {'python': platform.python_version(), 'platform': platform.platform(),
                          'machine': platform.machine()},
              'priority_observed': priority,
              'fixture_sha256': hashlib.sha256((ROOT / 'fixtures.json').read_bytes()).hexdigest(),
              'cases': cases, 'quantization_cases': quantization, 'input_refusals': refusals,
              'scope': {'model_only': True, 'exact_rational': True, 'real_device_runs': 0,
                        'sensor_measurements': 0, 'random_draws': 0, 'network_requests': 0,
                        'browser_executed': False, 'server_started': False}}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
