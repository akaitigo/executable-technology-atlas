"""Atlas: one bounded production run; expected values are never imported."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from algorithm import METHODS, sort_records, compare_search

BASE = Path(__file__).resolve().parent
INPUTS = ('CONTRACT.md', 'fixture.json', 'expected.json', 'rejection-cases.json', 'algorithm.py', 'run.py', 'verify.py')

def main():
    if os.getpriority(os.PRIO_PROCESS, 0) < 10:
        raise SystemExit('Atlas: actual nice10 required')
    destination = BASE / 'observations/run-01'
    destination.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    result = {'Atlas': '安定整列と準備費用の実計算', 'startedAt': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'platform': platform.platform(), 'actualNice': os.getpriority(os.PRIO_PROCESS, 0),
              'inputs': {}, 'cases': [], 'refusals': []}
    snapshot = destination / 'inputs'
    snapshot.mkdir()
    for name in INPUTS:
        content = (BASE / name).read_bytes()
        (snapshot / name).write_bytes(content)
        result['inputs'][name] = hashlib.sha256(content).hexdigest()
    fixture = json.loads((BASE / 'fixture.json').read_text())
    for case in fixture['cases']:
        before = deepcopy(case['records'])
        row = {'id': case['id'], 'label': case['label'], 'input': before, 'outcomes': {}}
        for method in METHODS:
            outcome = sort_records(case['records'], method)
            outcome['search'] = compare_search(case['records'], outcome, fixture['queries'])
            row['outcomes'][method] = outcome
        row['inputAfter'] = deepcopy(case['records'])
        row['inputUnchanged'] = row['inputAfter'] == before
        result['cases'].append(row)
    for case in json.loads((BASE / 'rejection-cases.json').read_text())['cases']:
        before = deepcopy(case['records'])
        error, answer = None, None
        try:
            answer = sort_records(case['records'], case['method'])
        except ValueError as exc:
            error = str(exc)
        result['refusals'].append({'id': case['id'], 'method': case['method'], 'input': before,
                                  'inputAfter': case['records'], 'reason': error, 'result': answer})
    result['elapsedSeconds'] = time.monotonic() - start
    result['finishedAt'] = datetime.now(timezone.utc).isoformat()
    (destination / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'Atlas': '有限実計算完了', 'cases': len(result['cases']), 'sorts': 18, 'refusals': len(result['refusals']), 'elapsedSeconds': result['elapsedSeconds'], 'actualNice': result['actualNice']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
