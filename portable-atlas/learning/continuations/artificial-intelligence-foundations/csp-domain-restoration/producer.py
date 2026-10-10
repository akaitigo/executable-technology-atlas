"""Atlas: one finite model batch, nine saved results; expected is never read."""
import hashlib
import json
import platform
import sys
from pathlib import Path
from csp import solve

ROOT = Path(__file__).resolve().parent

def emit(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True), flush=True)

def main():
    emit({'kind': 'producer-started', 'project': 'Atlas', 'python': sys.version, 'platform': platform.platform()})
    path = ROOT / 'inputs/problems.json'
    fixture = json.loads(path.read_text())
    if fixture['variables'] != list('ABCD') or fixture['colors'] != [0, 1] or len(fixture['problems']) != 4 or len(fixture['runs']) != 9:
        raise ValueError('fixed finite fixture shape required')
    emit({'kind': 'input', 'fixture': fixture, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    problems = {p['id']: p for p in fixture['problems']}
    for request in fixture['runs']:
        result = solve(problems[request['problem']], request['mode'])
        emit({'kind': 'case', **result})
    emit({'kind': 'batch-complete', 'case_count': 9, 'retry': 0})

if __name__ == '__main__':
    main()
