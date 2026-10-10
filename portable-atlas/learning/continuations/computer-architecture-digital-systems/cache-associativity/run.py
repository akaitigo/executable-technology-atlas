"""One stdlib batch. Root supplies fresh/slot/nice/timeout/child collection."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

from cache_model import simulate

ROOT = Path(__file__).resolve().parent
SOURCES = ['cache_model.py', 'run.py', 'inputs/cases.json']
stamp = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    output = args.output.resolve()
    if ROOT / 'observations' not in output.parents or output.exists():
        raise SystemExit('output must be a new file inside this lesson observations/')
    start = time.monotonic()
    result = {'project': 'Atlas', 'model': 'fixed-cache-associativity-v1',
              'complete': False, 'results': [], 'errors': [], 'model_cases_started': 0,
              'execution': {'pid': os.getpid(), 'ppid': os.getppid(), 'started_at': stamp(),
                            'python': sys.version, 'executable': sys.executable,
                            'bounds_owner': 'root wrapper; this process creates no child'}}
    try:
        nice = os.getpriority(os.PRIO_PROCESS, 0)
        result['execution']['nice_before'] = nice
        result['execution']['cpu_limit'] = list(resource.getrlimit(resource.RLIMIT_CPU))
        if nice < 10:
            raise RuntimeError('actual nice must be >= 10 before any model case')
        result['source_sha256'] = {n: sha(ROOT / n) for n in SOURCES}
        fixture = json.loads((ROOT / 'inputs/cases.json').read_text())
        if (fixture['capacity_bytes'], fixture['line_bytes'], fixture['memory_bytes']) != (16, 4, 256):
            raise ValueError('fixed geometry required')
        if [c['id'] for c in fixture['cases']] != ['conflict', 'overfull-set', 'hit-recency', 'offsets', 'empty']:
            raise ValueError('fixed case order required')
        if fixture['normal_modes'] != ['direct', 'two-way-lru'] or fixture['fault'] != {
            'case': 'hit-recency', 'mode': 'two-way-no-hit-touch',
            'change': 'skip recency touch on hits only'}:
            raise ValueError('fixed mode selection required')
        # Validate all traces before any model read, including later cases.
        from cache_model import validate
        for c in fixture['cases']:
            validate(c['addresses'], 'direct')
        result['fixture'] = fixture
        for case in fixture['cases']:
            modes = fixture['normal_modes'][:]
            if case['id'] == fixture['fault']['case']:
                modes.append(fixture['fault']['mode'])
            for mode in modes:
                result['model_cases_started'] += 1
                value = simulate(case['addresses'], mode)
                value.update(id=case['id'] + '/' + mode, case_id=case['id'])
                result['results'].append(value)
        result['complete'] = len(result['results']) == 11
    except Exception as error:
        result['errors'].append({'type': type(error).__name__, 'message': str(error)})
    finally:
        result['execution'].update(finished_at=stamp(), elapsed_seconds=time.monotonic() - start)
        try:
            result['execution']['nice_after'] = os.getpriority(os.PRIO_PROCESS, 0)
            if result['execution']['nice_after'] < 10:
                raise RuntimeError('actual nice fell below 10')
            if result.get('source_sha256'):
                result['source_unchanged'] = all(sha(ROOT / n) == h for n, h in result['source_sha256'].items())
                if not result['source_unchanged']:
                    raise RuntimeError('fixed source changed during batch')
        except Exception as error:
            result['complete'] = False
            result['errors'].append({'type': type(error).__name__, 'message': str(error), 'stage': 'final-readback'})
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps({'complete': result['complete'], 'errors': result['errors'],
                      'output': str(output), 'sha256': sha(output),
                      'results': len(result['results']), 'model_cases_started': result['model_cases_started']}))
    return 0 if result['complete'] and not result['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
