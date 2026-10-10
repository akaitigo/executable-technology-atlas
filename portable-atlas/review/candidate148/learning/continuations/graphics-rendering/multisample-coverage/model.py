"""Atlas: fixed rational coverage, per-sample depth and a local RGB mean rule."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

FIXTURE_SHA = 'f7af01a16c37ac231d3ac061b1ebcaa43d6ddf4434a657c4b12e401bb6008955'
SCOPE = {'model_only': True, 'gpu_api_calls': 0, 'hardware_measured': False,
         'coverage_recomputed': True, 'depth_quantized': False, 'resolved_depth': False,
         'shader_executed': False, 'network_requests': 0}


def shape(actual, reference):
    if type(actual) is not type(reference):
        raise ValueError('TYPE')
    if type(reference) is dict:
        if set(actual) != set(reference):
            raise ValueError('SCHEMA')
        for key in reference:
            shape(actual[key], reference[key])
    elif type(reference) is list:
        if len(actual) != len(reference):
            raise ValueError('SCHEMA')
        for a, b in zip(actual, reference):
            shape(a, b)


def rational(value):
    try:
        q = F(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError('RATIONAL') from None
    if str(q) != value:
        raise ValueError('RATIONAL')
    return q


def validate_fixture(fixture):
    raw = (Path(__file__).parent / 'fixtures.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise ValueError('FIXTURE_FILE')
    reference = json.loads(raw)
    shape(fixture, reference)  # Includes exact int/bool/float distinctions.
    for offset_list in fixture['layouts'].values():
        for offset in offset_list:
            for value in offset:
                if not 0 < rational(value) < 1:
                    raise ValueError('SAMPLE_RANGE')
    for value in fixture['background_rgb'] + [fixture['clear_depth']]:
        if not 0 <= rational(value) <= 1:
            raise ValueError('RANGE')
    for scene in fixture['scenes']:
        for face in scene['triangles']:
            for point in face['vertices']:
                for value in point:
                    rational(value)
            for value in face['rgb'] + [face['depth']]:
                if not 0 <= rational(value) <= 1:
                    raise ValueError('RANGE')
    if fixture != reference:
        raise ValueError('FIXED_INPUT')


def edge(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0])


def covered(vertices, p):
    for a, b in zip(vertices, vertices[1:] + vertices[:1]):
        e = edge(a, b, p)
        included = b[1] < a[1] or (b[1] == a[1] and b[0] > a[0])
        if e < 0 or (e == 0 and not included):
            return False
    return True


def mean_rgb(samples):
    return [str(sum(F(s['rgb'][c]) for s in samples) / len(samples)) for c in range(3)]


def copy_sample(s):
    return {**s, 'position': list(s['position']), 'rgb': list(s['rgb'])}


def stage(step, drawn, samples):
    return {'step': step, 'drawn': drawn, 'samples': [copy_sample(s) for s in samples],
            'resolved_rgb': mean_rgb(samples)}


def _render(fixture, scene, layout_id, work):
    offsets = fixture['layouts'][layout_id]
    pixels = []
    for pixel in fixture['pixels']:
        positions = [(F(pixel[0]) + F(dx), F(pixel[1]) + F(dy)) for dx, dy in offsets]
        samples = [{'sample_index': i, 'position': [str(x), str(y)], 'winner': None,
                    'depth': fixture['clear_depth'], 'rgb': list(fixture['background_rgb'])}
                   for i, (x, y) in enumerate(positions)]
        stages = [stage(0, None, samples)]; draws = []
        for step, face in enumerate(scene['triangles'], 1):
            vertices = [tuple(F(v) for v in p) for p in face['vertices']]
            events = []
            for i, p in enumerate(positions):
                work['coverage_tests'] += 1
                inside = covered(vertices, p)
                before = copy_sample(samples[i]); accepted = None
                if inside:
                    work['depth_tests'] += 1
                    accepted = F(face['depth']) < F(before['depth'])
                    if accepted:
                        work['accepted_samples_across_draws'] += 1
                        samples[i] = {**before, 'winner': face['id'], 'depth': face['depth'],
                                      'rgb': list(face['rgb'])}
                events.append({'sample_index': i, 'position': [str(v) for v in p],
                               'covered': inside, 'tested_depth': face['depth'] if inside else None,
                               'accepted': accepted, 'before': before, 'after': copy_sample(samples[i])})
            draws.append({'step': step, 'triangle_id': face['id'],
                          'coverage_mask': ''.join('1' if e['covered'] else '0' for e in events),
                          'accepted_mask': ''.join('1' if e['accepted'] is True else '0' for e in events),
                          'events': events})
            stages.append(stage(step, face['id'], samples))
        pixels.append({'pixel': list(pixel), 'stages': stages, 'draws': draws})
    return {'id': scene['id'] + '/' + layout_id, 'scene_id': scene['id'], 'layout_id': layout_id,
            'sample_offsets': [list(v) for v in offsets], 'pixels': pixels}


def new_work():
    return {'coverage_tests': 0, 'depth_tests': 0, 'accepted_samples_across_draws': 0}


def render(fixture, scene_id, layout_id, work=None):
    validate_fixture(fixture)
    if type(scene_id) is not str or scene_id not in [s['id'] for s in fixture['scenes']]:
        raise ValueError('SCENE')
    if type(layout_id) is not str or layout_id not in fixture['layouts']:
        raise ValueError('LAYOUT')
    scene = next(s for s in fixture['scenes'] if s['id'] == scene_id)
    return _render(fixture, scene, layout_id, new_work() if work is None else work)


def evaluate(fixture, work=None):
    validate_fixture(fixture)
    work = new_work() if work is None else work
    results = [_render(fixture, scene, layout, work)
               for scene in fixture['scenes'] for layout in ('center', 'four')]
    return {'schema': 1, 'scope': dict(SCOPE), 'results': results, 'work': dict(work)}
