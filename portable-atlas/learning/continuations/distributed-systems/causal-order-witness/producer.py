"""Atlas: emit complete records for exactly four fixed comparisons, once."""
import datetime
import hashlib
import json
import platform
import sys
from pathlib import Path
from model import compare

ROOT = Path(__file__).resolve().parent


def emit(record):
    print(json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)


def main():
    emit({'kind': 'started', 'project': 'Atlas', 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'python': sys.version, 'platform': platform.platform(), 'target_retry': 0})
    content = (ROOT / 'inputs/events.json').read_bytes()
    fixture = json.loads(content)
    emit({'kind': 'fixture', 'sha256': hashlib.sha256(content).hexdigest(), 'input': fixture})
    for case in fixture['cases']:
        emit({'kind': 'case-result', 'result': compare(fixture, case)})
    emit({'kind': 'batch-complete', 'case_count': 4, 'pair_rows': 60, 'retry_count': 0})


if __name__ == '__main__':
    main()
