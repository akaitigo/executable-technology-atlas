"""Atlas: fixed typing/strict/diagnostic contrasts; never read expected.json."""
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path
from type_model import InputRefused, validate, derive, erase

ROOT = Path(__file__).resolve().parent


def emit(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True), flush=True)


def main():
    emit({'kind': 'producer-started', 'project': 'Atlas', 'python': platform.python_version()})
    source = ROOT / 'inputs/prerequisite-small-step.py'
    spec = importlib.util.spec_from_file_location('atlas_type_comparison', source)
    old = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    fixture = ROOT / 'inputs/cases.json'
    data = json.loads(fixture.read_text())
    emit({'kind': 'input', 'sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
          'fixture': data, 'prerequisite_sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    for case in data['cases']:
        try:
            validate(case['term'], case['diagnostic_budget'])
        except InputRefused as error:
            emit({'kind': 'input-refused', 'case_id': case['id'], 'reason': str(error)})
            return 2
        typing = derive(case['term'])
        erased = erase(case['term'])
        counts = {'strict': 0, 'diagnostic': 0}
        def evaluate(branch):
            counts[branch] += 1
            return old.run(erased, case['diagnostic_budget'])
        strict_result = evaluate('strict') if typing['status'] == 'accepted' else None
        diagnostic_result = evaluate('diagnostic')
        emit({'kind': 'case-result', 'case_id': case['id'], 'input': case,
              'typing': typing, 'erased_term': erased,
              'strict': {'status': 'evaluated' if typing['status'] == 'accepted' else 'type-rejected',
                         'evaluator_calls': counts['strict'], 'result': strict_result},
              'diagnostic': {'purpose': 'separate annotation-erased comparison; not strict dispatch',
                             'evaluator_calls': counts['diagnostic'], 'result': diagnostic_result}})
    emit({'kind': 'batch-complete', 'case_count': len(data['cases']), 'retry': 0})
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        emit({'kind': 'execution-failure', 'error_type': type(error).__name__, 'message': str(error)})
        raise
