"""Atlas: emit the five fixed contrasts; expected.json is never imported."""
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

from small_step import InputRefused, run as small_run

ROOT = Path(__file__).resolve().parent


def emit(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True), flush=True)


def main():
    emit({'kind': 'producer-started', 'project': 'Atlas', 'python': platform.python_version()})
    source = ROOT / 'inputs/prerequisite-interpreter.py'
    spec = importlib.util.spec_from_file_location('atlas_small_step_prerequisite', source)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    fixture = ROOT / 'inputs/cases.json'
    data = json.loads(fixture.read_text())
    emit({'kind': 'input', 'sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
          'fixture': data, 'prerequisite_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    for case in data['cases']:
        try:
            small = small_run(case['ast'], case['budget'])
        except InputRefused as error:
            emit({'kind': 'input-refused', 'case_id': case['id'], 'reason': str(error)})
            return 2
        big = old.run(case['ast'], dynamic=False)
        emit({'kind': 'case-result', 'case_id': case['id'], 'input': case,
              'small_step': small, 'big_step': big,
              'comparison': {'kind': 'same input, different observation units',
                             'applied_rule_steps': small['applied_steps'],
                             'big_step_node_enters': big['evaluations'],
                             'big_step_trace_events': len(big['trace']),
                             'event_count_is_not_rule_count': True}})
    emit({'kind': 'batch-complete', 'case_count': len(data['cases']), 'retry': 0})
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        emit({'kind': 'execution-failure', 'error_type': type(error).__name__, 'message': str(error)})
        raise
