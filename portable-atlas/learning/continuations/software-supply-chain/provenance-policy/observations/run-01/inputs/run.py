"""Atlas: 実nice確認後、固定7入力の保存計算を1回だけ実行。"""
import datetime
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice < 10:
        raise SystemExit('actual nice >= 10 required before producer import')
    output = ROOT / 'observations/run-01'
    if output.exists():
        raise SystemExit('existing run is immutable')
    inputs = ['CONTRACT.md', 'SOURCES.md', 'consumer-policy.json', 'cases.json', 'expected.json',
              'policy.py', 'produce.py', 'verify.py', 'run.py', 'execute_once.py']
    inputs += [str(p.relative_to(ROOT)) for p in sorted((ROOT / 'fixtures').iterdir()) if p.is_file()]
    output.mkdir(parents=True)
    sources = {}
    for name in inputs:
        target = output / 'inputs' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
        sources[name] = hashlib.sha256(target.read_bytes()).hexdigest()
    from produce import collect
    from verify import check, mutation_checks
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    began = time.perf_counter()
    saved = collect()
    duration = time.perf_counter() - began
    saved.update(startedAt=started, calculationSeconds=duration,
                 toolchain={'python': sys.version, 'executable': sys.executable, 'platform': platform.platform()},
                 pid=os.getpid(), actualNice=nice, sourceSha256=sources)
    raw = (json.dumps(saved, ensure_ascii=False, indent=2) + '\n').encode()
    (output / 'results.json').write_bytes(raw)
    count = check(saved)
    mutations = mutation_checks(saved)
    record = {'Atlas': '別実装の保存値照合', 'passed': True, 'checks': count, 'mutations': mutations,
              'resultsSha256': hashlib.sha256(raw).hexdigest(), 'producerImportedByChecker': False}
    (ROOT / 'verification/saved-result-check.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'cases': 7, 'responses': 14, 'checks': count, 'mutations': len(mutations),
                      'actualNice': nice, 'pid': os.getpid(), 'calculationSeconds': duration, 'resultsSha256': record['resultsSha256']}))


if __name__ == '__main__':
    main()
