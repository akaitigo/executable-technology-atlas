"""Atlas: one saved rational multisample calculation, with no GPU execution."""
import copy
import datetime
import hashlib
import json
import os
import platform
from pathlib import Path
from model import evaluate, render, new_work

ROOT = Path(__file__).resolve().parent


def refusals(fixture):
    changes = [
        ('missing-layout', 'SCHEMA', lambda x: x['layouts'].pop('four')),
        ('extra-key', 'SCHEMA', lambda x: x.update(gpu=True)),
        ('grid-bool', 'TYPE', lambda x: x['grid'].__setitem__(0, True)),
        ('grid-float', 'TYPE', lambda x: x['grid'].__setitem__(0, 2.0)),
        ('grid-change', 'FIXED_INPUT', lambda x: x['grid'].__setitem__(0, 3)),
        ('sample-float', 'TYPE', lambda x: x['layouts']['four'][0].__setitem__(0, 0.25)),
        ('sample-outside', 'SAMPLE_RANGE', lambda x: x['layouts']['four'][0].__setitem__(0, '1')),
        ('sample-order', 'FIXED_INPUT', lambda x: x['layouts']['four'].reverse()),
        ('fraction-noncanonical', 'RATIONAL', lambda x: x['layouts']['four'][0].__setitem__(0, '2/8')),
        ('fraction-zero-denominator', 'RATIONAL', lambda x: x['layouts']['four'][0].__setitem__(0, '1/0')),
        ('fraction-nan', 'RATIONAL', lambda x: x['layouts']['four'][0].__setitem__(0, 'NaN')),
        ('depth-outside', 'RANGE', lambda x: x['scenes'][0]['triangles'][0].update(depth='2')),
        ('depth-changed', 'FIXED_INPUT', lambda x: x['scenes'][0]['triangles'][0].update(depth='1/3')),
        ('color-outside', 'RANGE', lambda x: x['background_rgb'].__setitem__(0, '-1')),
        ('color-changed', 'FIXED_INPUT', lambda x: x['scenes'][0]['triangles'][0]['rgb'].__setitem__(0, '1/2')),
        ('vertex-missing', 'SCHEMA', lambda x: x['scenes'][0]['triangles'][0]['vertices'].pop()),
        ('vertex-changed', 'FIXED_INPUT', lambda x: x['scenes'][0]['triangles'][0]['vertices'][0].__setitem__(0, '1')),
        ('draw-order', 'FIXED_INPUT', lambda x: x['scenes'][2]['triangles'].reverse()),
        ('late-invalid-face', 'RATIONAL', lambda x: x['scenes'][-1]['triangles'][-1].update(depth='1/0')),
    ]
    for name, reason, change in changes:
        candidate = copy.deepcopy(fixture); change(candidate)
        yield name, reason, candidate, 'edge-low', 'center'
    yield 'unknown-scene', 'SCENE', copy.deepcopy(fixture), 'unknown', 'center'
    yield 'unknown-layout', 'LAYOUT', copy.deepcopy(fixture), 'edge-low', 'unknown'


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('Atlas: actual nice 10 required before finite calculation')
    raw = (ROOT / 'fixtures.json').read_bytes(); fixture = json.loads(raw)
    result = evaluate(fixture)
    rejected = []
    for name, reason, candidate, scene, layout in refusals(fixture):
        work = new_work()
        try:
            render(candidate, scene, layout, work)
        except ValueError as error:
            assert str(error) == reason, (name, str(error), reason)
            assert work == new_work(), (name, work)
            rejected.append({'id': name, 'status': 'INPUT_REFUSED', 'reason': reason,
                             'work': dict(work), 'value': None})
        else:
            raise AssertionError('invalid fixed input accepted: ' + name)
    result.update(title='Atlas graphics multisample saved calculation', status='observed',
                  observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  runtime={'python': platform.python_version(), 'platform': platform.platform(),
                           'machine': platform.machine()}, priority_observed=priority,
                  fixture_sha256=hashlib.sha256(raw).hexdigest(), input_refusals=rejected)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
