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

from copy import deepcopy
from config_model import evaluate

ROOT = Path(__file__).resolve().parent
SOURCES = ['config_model.py', 'run.py', 'inputs/cases.json']
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
    result = {'project': 'Atlas', 'model': 'fixed-config-shadowed-validation-v1',
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
        if [c['id'] for c in fixture['cases']] != [
            'normal-boundary', 'shadowed-integer', 'unshadowed-integer',
            'invalid-winning-bool', 'shadowed-boolean', 'unknown-field']:
            raise ValueError('fixed six-case order required')
        if fixture['policies'] != ['all-layer', 'winning-only']:
            raise ValueError('fixed two-policy order required')
        for case in fixture['cases']:
            for policy in fixture['policies']:
                layers = {'default': deepcopy(fixture['defaults']),
                          'env-input': deepcopy(case['env']),
                          'task-json': deepcopy(case['task'])}
                result['model_cases_started'] += 1
                result['results'].append(evaluate(case['id'], layers, policy))
        result['complete'] = len(result['results']) == 12
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
