"""Atlas: four fixed finite propagation comparisons; expected is never read."""
import hashlib
import json
import platform
import sys
from pathlib import Path
from arc_consistency import compare

ROOT = Path(__file__).resolve().parent


def emit(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True), flush=True)


def main():
    emit(dict(kind='producer-started', project='Atlas', python=sys.version, platform=platform.platform()))
    path = ROOT / 'inputs/cases.json'
    fixture = json.loads(path.read_text())
    if fixture['variables'] != list('ABCD') or fixture['colors'] != [0, 1] or [c['id'] for c in fixture['cases']] != ['chain-anchored', 'triangle-anchored', 'triangle-free', 'square-free']:
        raise ValueError('fixed four-case fixture required')
    emit(dict(kind='input', fixture=fixture, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    for case in fixture['cases']:
        emit(dict(kind='case', **compare(case)))
    emit(dict(kind='batch-complete', case_count=4, retry=0))


if __name__ == '__main__':
    main()
