"""Saved JSON only: no model imports or execution."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
canonical = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def inspect(actual, expected):
    checks = []
    def eq(label, left, right):
        checks.append({'label': label, 'passed': canonical(left) == canonical(right)})
    eq('complete', actual.get('complete'), True)
    eq('errors', actual.get('errors'), [])
    eq('result-count', len(actual.get('results', [])), 12)
    eq('model-started', actual.get('model_cases_started'), 12)
    eq('source-unchanged', actual.get('source_unchanged'), True)
    ex = actual.get('execution', {})
    checks.append({'label': 'actual-nice', 'passed': ex.get('nice_before', -1) >= 10 and ex.get('nice_after', -1) >= 10})
    for name, digest in actual.get('source_sha256', {}).items():
        eq('source/' + name, digest, sha(ROOT / name))
    eq('source-names', sorted(actual.get('source_sha256', {})), ['config_model.py', 'inputs/cases.json', 'run.py'])
    for i, want in enumerate(expected['results']):
        got = actual.get('results', [])[i] if i < len(actual.get('results', [])) else {}
        prefix = str(i)
        for key in ['case_id', 'policy', 'decision', 'reason', 'config', 'provenance']:
            eq(prefix + '/' + key, got.get(key), want[key])
        for key in ['parse_attempts', 'candidate', 'error']:
            eq(prefix + '/diagnostic/' + key, got.get('diagnostic', {}).get(key), want['diagnostic'][key])
        events = got.get('events', [])
        eq(prefix + '/event-count', len(events), len(want['events']))
        for n, event in enumerate(want['events']):
            row = events[n] if n < len(events) else {}
            eq(prefix + '/event/' + str(n) + '/keys', sorted(row), sorted(event))
            for key in event:
                eq(prefix + '/event/' + str(n) + '/' + key, row.get(key), event[key])
        if got.get('decision') == 'refused':
            eq(prefix + '/refusal-config-null', got.get('config'), None)
            eq(prefix + '/refusal-provenance-null', got.get('provenance'), None)
    checks.append({'label': 'unknown-raw-not-echoed', 'passed': 'EXAMPLE_NOT_A_SECRET' not in canonical(actual)})
    return checks


def main():
    saved = Path(sys.argv[1])
    actual = json.loads(saved.read_text())
    expected = json.loads((ROOT / 'expected.json').read_text())
    checks = inspect(actual, expected)
    variants = []
    specs = [
        ('shadowed-strict-adopted', '2/decision', lambda x: x['results'][2].__setitem__('decision', 'accepted')),
        ('wrong-raw-winner', '3/diagnostic/candidate', lambda x: x['results'][3]['diagnostic']['candidate']['timeout_ms'].__setitem__('raw', 'oops')),
        ('false-as-zero', '0/config', lambda x: x['results'][0]['config'].__setitem__('flag_enabled', 0)),
        ('hidden-parse-claimed', '3/diagnostic/parse_attempts', lambda x: x['results'][3]['diagnostic']['parse_attempts'].append(x['results'][2]['diagnostic']['parse_attempts'][-1])),
        ('partial-config-leak', '5/refusal-config-null', lambda x: x['results'][5].__setitem__('config', {})),
        ('unknown-raw-echo', 'unknown-raw-not-echoed', lambda x: x['results'][10]['diagnostic']['error'].__setitem__('raw', 'EXAMPLE_NOT_A_SECRET')),
        ('parse-before-merge', '1/event/2/action', lambda x: x['results'][1]['events'].__setitem__(2, deepcopy(x['results'][1]['events'][3]))),
    ]
    for name, required, change in specs:
        changed = deepcopy(actual)
        change(changed)
        failed = [c['label'] for c in inspect(changed, expected) if not c['passed']]
        variants.append({'name': name, 'required_label': required, 'failed_labels': failed,
                         'rejected_at_required_label': required in failed})
    report = {'scope': 'Saved JSON compared with preimplementation manual table; no producer import/execution',
              'saved_sha256': sha(saved), 'expected_sha256': sha(ROOT / 'expected.json'),
              'checks': checks, 'mutations': variants,
              'passed': all(c['passed'] for c in checks) and all(v['rejected_at_required_label'] for v in variants)}
    output = saved.with_suffix('.verify.json')
    with output.open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'mutations': len(variants), 'output': str(output), 'sha256': sha(output)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
