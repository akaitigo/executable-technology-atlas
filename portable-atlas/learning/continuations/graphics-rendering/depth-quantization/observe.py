"""Atlas: save one finite depth calculation; no GPU or rendering API is invoked."""
import copy
import datetime
import hashlib
import json
import os
import platform
from pathlib import Path
from model import evaluate

ROOT = Path(__file__).resolve().parent


def refusal_inputs(base):
    changes = [
        ('missing-group', 'SCHEMA', lambda x: x.pop('boundaries')),
        ('extra-field', 'SCHEMA', lambda x: x.update(gpu=True)),
        ('schema-bool', 'TYPE', lambda x: x.update(schema_version=True)),
        ('unknown-case', 'UNKNOWN_CASE', lambda x: x['central'][0].update(id='other')),
        ('bits-bool', 'TYPE', lambda x: x['central'][0]['request'].update(bits=True)),
        ('bits-float', 'TYPE', lambda x: x['central'][0]['request'].update(bits=3.0)),
        ('bits-outside', 'BITS', lambda x: x['central'][0]['request'].update(bits=8)),
        ('request-extra', 'SCHEMA', lambda x: x['central'][0]['request'].update(clear=0)),
        ('missing-fragment', 'SCHEMA', lambda x: x['central'][0]['request']['fragments'].pop()),
        ('unknown-fragment', 'FRAGMENT_ID', lambda x: x['central'][0]['request']['fragments'][0].update(id='X')),
        ('duplicate-fragment', 'DUPLICATE_FRAGMENT', lambda x: x['central'][0]['request']['fragments'][1].update(id='A')),
        ('depth-float', 'TYPE', lambda x: x['central'][0]['request']['fragments'][0].update(z=0.4)),
        ('depth-noncanonical', 'RATIONAL', lambda x: x['central'][0]['request']['fragments'][0].update(z='4/10')),
        ('zero-denominator', 'RATIONAL', lambda x: x['central'][0]['request']['fragments'][0].update(z='1/0')),
        ('negative-denominator', 'RATIONAL', lambda x: x['central'][0]['request']['fragments'][0].update(z='-2/-5')),
        ('not-finite', 'RATIONAL', lambda x: x['central'][0]['request']['fragments'][0].update(z='NaN')),
        ('depth-negative', 'DEPTH_RANGE', lambda x: x['central'][0]['request']['fragments'][0].update(z='-1/5')),
        ('depth-above-one', 'DEPTH_RANGE', lambda x: x['central'][0]['request']['fragments'][0].update(z='6/5')),
        ('different-fixed-depth', 'FIXED_INPUT', lambda x: x['central'][0]['request']['fragments'][0].update(z='1/3')),
        ('late-invalid-input', 'RATIONAL', lambda x: x['boundaries'][-1]['request']['fragments'][0].update(z='nan')),
    ]
    for name, reason, change in changes:
        candidate = copy.deepcopy(base); change(candidate)
        yield name, reason, candidate


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('Atlas: actual nice 10 required before finite calculation')
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    result = evaluate(fixture)
    refusals = []
    for name, reason, candidate in refusal_inputs(fixture):
        try:
            evaluate(candidate)
        except ValueError as error:
            assert str(error) == reason, (name, str(error), reason)
            refusals.append({'id': name, 'status': 'INPUT_REFUSED', 'reason': reason,
                             'draws': 0, 'trace': [], 'value': None})
        else:
            raise AssertionError('invalid fixture accepted: ' + name)
    result.update(title='Atlas graphics depth quantization saved calculation', status='observed',
                  observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  runtime={'python': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine()},
                  priority_observed=priority,
                  fixture_sha256=hashlib.sha256((ROOT / 'fixtures.json').read_bytes()).hexdigest(),
                  input_refusals=refusals)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
