"""Atlas: check saved results against preimplementation literal masks; never run the renderer."""
import argparse
import copy
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCOPE = {'model_only': True, 'gpu_api_calls': 0, 'hardware_measured': False,
         'coverage_recomputed': True, 'depth_quantized': False, 'resolved_depth': False,
         'shader_executed': False, 'network_requests': 0}
REFUSALS = [
    ('missing-layout', 'SCHEMA'), ('extra-key', 'SCHEMA'), ('grid-bool', 'TYPE'),
    ('grid-float', 'TYPE'), ('grid-change', 'FIXED_INPUT'), ('sample-float', 'TYPE'),
    ('sample-outside', 'SAMPLE_RANGE'), ('sample-order', 'FIXED_INPUT'),
    ('fraction-noncanonical', 'RATIONAL'), ('fraction-zero-denominator', 'RATIONAL'),
    ('fraction-nan', 'RATIONAL'), ('depth-outside', 'RANGE'), ('depth-changed', 'FIXED_INPUT'),
    ('color-outside', 'RANGE'), ('color-changed', 'FIXED_INPUT'), ('vertex-missing', 'SCHEMA'),
    ('vertex-changed', 'FIXED_INPUT'), ('draw-order', 'FIXED_INPUT'),
    ('late-invalid-face', 'RATIONAL'), ('unknown-scene', 'SCENE'), ('unknown-layout', 'LAYOUT')]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def same(actual, expected):
    assert type(actual) is type(expected), ('type', type(actual), type(expected))
    if type(expected) is dict:
        assert set(actual) == set(expected), ('keys', set(actual), set(expected))
        for key in expected:
            same(actual[key], expected[key])
    elif type(expected) is list:
        assert len(actual) == len(expected), ('length', len(actual), len(expected))
        for a, e in zip(actual, expected):
            same(a, e)
    else:
        assert actual == expected, ('value', actual, expected)


def expected(fixture, hand):
    """Expand literal masks, without an edge/barycentric/coverage function."""
    results = []; tested = compared = adopted = 0
    for scene in fixture['scenes']:
        for layout in ('center', 'four'):
            table = hand['tables'][scene['id']][layout]
            offsets = fixture['layouts'][layout]; n = len(offsets); pixels = []
            for row, pixel in enumerate(fixture['pixels']):
                positions = [[str(F(pixel[0])+F(o[0])), str(F(pixel[1])+F(o[1]))] for o in offsets]
                samples = [{'sample_index': i, 'position': p, 'winner': None,
                            'depth': '1', 'rgb': ['0', '0', '0']} for i, p in enumerate(positions)]
                def snap(step, face):
                    # Independent color-basis counts, not the producer's channel-summing routine.
                    red = sum(s['winner'] == 'A' for s in samples)
                    blue = sum(s['winner'] in ('B', 'C') for s in samples)
                    return {'step': step, 'drawn': face, 'samples': copy.deepcopy(samples),
                            'resolved_rgb': [str(F(red, n)), '0', str(F(blue, n))]}
                stages = [snap(0, None)]; draws = []
                for step, face in enumerate(scene['triangles'], 1):
                    mask = table['coverage_masks'][face['id']][row]
                    passes = table['accepted_masks'][face['id']][row]
                    events = []
                    for i in range(n):
                        inside = mask[i] == '1'; take = passes[i] == '1'
                        tested += 1; compared += int(inside); adopted += int(take)
                        assert inside or not take
                        before = copy.deepcopy(samples[i])
                        if inside:
                            assert take == (F(face['depth']) < F(before['depth']))
                        if take:
                            samples[i].update(winner=face['id'], depth=face['depth'], rgb=list(face['rgb']))
                        events.append({'sample_index': i, 'position': positions[i], 'covered': inside,
                                       'tested_depth': face['depth'] if inside else None,
                                       'accepted': take if inside else None,
                                       'before': before, 'after': copy.deepcopy(samples[i])})
                    draws.append({'step': step, 'triangle_id': face['id'], 'coverage_mask': mask,
                                  'accepted_mask': passes, 'events': events})
                    stages.append(snap(step, face['id']))
                same([s['winner'] for s in samples], table['winners'][row])
                same([s['depth'] for s in samples], table['depths'][row])
                same(stages[-1]['resolved_rgb'], table['resolved_rgb'][row])
                pixels.append({'pixel': pixel, 'stages': stages, 'draws': draws})
            results.append({'id': scene['id']+'/'+layout, 'scene_id': scene['id'], 'layout_id': layout,
                            'sample_offsets': offsets, 'pixels': pixels})
    assert (tested, compared, adopted) == (160, 94, 87)
    return {'schema': 1, 'scope': SCOPE, 'results': results,
            'work': {'coverage_tests': tested, 'depth_tests': compared,
                     'accepted_samples_across_draws': adopted}}


def check(result, fixture, hand):
    core = expected(fixture, hand)
    metadata = {'title', 'status', 'observed_at_utc', 'runtime', 'priority_observed',
                'fixture_sha256', 'input_refusals'}
    assert set(result) == set(core) | metadata
    for key in core:
        same(result[key], core[key])
    assert result['title'] == 'Atlas graphics multisample saved calculation'
    assert result['status'] == 'observed' and type(result['priority_observed']) is int
    assert result['priority_observed'] == 10
    assert result['fixture_sha256'] == sha(ROOT/'fixtures.json')
    assert type(result['observed_at_utc']) is str and result['observed_at_utc']
    assert set(result['runtime']) == {'python', 'platform', 'machine'}
    assert all(type(x) is str and x for x in result['runtime'].values())
    same(result['input_refusals'], [
        {'id': name, 'status': 'INPUT_REFUSED', 'reason': reason,
         'work': {'coverage_tests': 0, 'depth_tests': 0, 'accepted_samples_across_draws': 0},
         'value': None} for name, reason in REFUSALS])


def altered_results(base):
    changes = [
        ('scope', lambda r: r['scope'].update(hardware_measured=True)),
        ('missing-result', lambda r: r['results'].pop()),
        ('wrong-case', lambda r: r['results'][0].update(scene_id='other')),
        ('wrong-offset', lambda r: r['results'][1]['sample_offsets'][0].__setitem__(0, '1/2')),
        ('coverage-mask', lambda r: r['results'][1]['pixels'][1]['draws'][0].update(coverage_mask='1111')),
        ('accepted-mask', lambda r: r['results'][1]['pixels'][1]['draws'][0].update(accepted_mask='0000')),
        ('unreached-false', lambda r: r['results'][0]['pixels'][1]['draws'][0]['events'][0].update(accepted=False)),
        ('unreached-depth', lambda r: r['results'][0]['pixels'][1]['draws'][0]['events'][0].update(tested_depth='1/2')),
        ('reject-to-pass', lambda r: r['results'][4]['pixels'][0]['draws'][1]['events'][0].update(accepted=True)),
        ('before-depth', lambda r: r['results'][0]['pixels'][0]['draws'][0]['events'][0]['before'].update(depth='0')),
        ('after-winner', lambda r: r['results'][0]['pixels'][0]['draws'][0]['events'][0]['after'].update(winner=None)),
        ('sample-position', lambda r: r['results'][0]['pixels'][0]['stages'][0]['samples'][0]['position'].__setitem__(0, '0')),
        ('sample-rgb', lambda r: r['results'][1]['pixels'][1]['stages'][1]['samples'][0].update(rgb=['0','0','1'])),
        ('wrong-divisor', lambda r: r['results'][1]['pixels'][1]['stages'][1].update(resolved_rgb=['1','0','0'])),
        ('resolved-depth-added', lambda r: r['results'][0]['pixels'][0]['stages'][0].update(resolved_depth='1')),
        ('work-bool', lambda r: r['work'].update(coverage_tests=True)),
        ('refusal-work', lambda r: r['input_refusals'][0]['work'].update(coverage_tests=1)),
        ('fixture-origin', lambda r: r.update(fixture_sha256='0'*64)),
    ]
    for name, change in changes:
        candidate = copy.deepcopy(base); change(candidate)
        yield name, candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('run_directory')
    args = parser.parse_args(); run = (ROOT/args.run_directory).resolve()
    assert run.parent == ROOT/'observations'
    lock = json.loads((ROOT/'contract-lock.json').read_text())
    for name, digest in lock['files'].items():
        assert sha(ROOT/name) == digest, ('contract', name)
    fixture = json.loads((ROOT/'fixtures.json').read_text()); hand = json.loads((ROOT/'hand-oracle.json').read_text())
    report = json.loads((run/'report.json').read_text()); result = json.loads((run/'result.json').read_text())
    assert report['status'] == 'observed' and report['exit_code'] == 0 and report['child_reaped']
    assert report['retry'] == 0 and not report['timed_out'] and not report['later_child_started']
    for name, digest in report['sources'].items():
        assert sha(ROOT/name) == digest, ('source', name)
    for key in ('result', 'stdout', 'stderr'):
        assert sha(run/(key+'.json' if key=='result' else key+'.txt')) == report[key+'_sha256']
    same(json.loads((run/'stdout.txt').read_text()), result)
    guards = [json.loads(s[len('ATLAS_PRIORITY '):]) for s in (run/'stderr.txt').read_text().splitlines() if s.startswith('ATLAS_PRIORITY ')]
    assert len(guards) == 1 and guards[0]['ready'] and guards[0]['observed_nice'] == 10
    check(result, fixture, hand)
    detected = []
    for name, altered in altered_results(result):
        try:
            check(altered, fixture, hand)
        except (AssertionError, KeyError, TypeError, ValueError):
            detected.append(name)
        else:
            raise AssertionError('alteration not rejected: '+name)
    print(json.dumps({'title':'Atlas saved multisample verification','passed':True,
                      'scene_layouts':10,'pixel_results':40,'final_samples':100,
                      'coverage_tests':160,'depth_tests':94,'accepted_samples_across_draws':87,
                      'input_refusals':len(REFUSALS),'alterations_detected':detected,
                      'producer_imported':False,'model_rerun':False,'run':str(run.relative_to(ROOT)),
                      'result_sha256':sha(run/'result.json'),'verify_source_sha256':sha(ROOT/'verify.py')},ensure_ascii=False))


if __name__ == '__main__':
    main()
