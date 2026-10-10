"""Atlas: one finite network child; verify priority before importing the experiment."""
import datetime
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ["CONTRACT.md", "SOURCES.md", "cases.json", "expected.json", "boundary.py", "experiment.py",
          "verify.py", "run.py", "execute_once.py", "resource_parse.py", "resource_observe.py",
          "fixtures/problem.json", "fixtures/problem-8192.json", "fixtures/problem-8193.json"]


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise SystemExit("actual nice >= 10 required before experiment import")
    destination = ROOT / "observations/run-01"
    if destination.exists():
        raise SystemExit("existing attempt is immutable")
    destination.mkdir(parents=True)
    hashes = {}
    for name in INPUTS:
        data = (ROOT / name).read_bytes()
        out = destination / "inputs" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    from experiment import produce
    from verify import verify
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    began = time.monotonic()
    result = produce()
    result.update(startedAt=started, experimentSeconds=time.monotonic() - began,
                  toolchain={"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
                  pid=os.getpid(), actualNice=priority, sourceSha256=hashes)
    # JSON round-trip is intentional: the checker evaluates the stored representation.
    path = destination / "results.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    checked = verify(json.loads(path.read_text()))
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise AssertionError("source changed during experiment: " + name)
    (ROOT / "verification").mkdir(exist_ok=True)
    (ROOT / "verification/saved-result-check.json").write_text(json.dumps(checked, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "requests": 4, "attempt": 1, "retry": 0,
                      "checks": checked["checks"], "mutationRejections": len(checked["mutations"]),
                      "actualNice": priority, "experimentSeconds": result["experimentSeconds"], "cleanup": result["cleanup"]}))


if __name__ == "__main__":
    main()
