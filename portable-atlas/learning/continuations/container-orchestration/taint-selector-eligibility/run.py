"""Atlas: one bounded child; actual priority check precedes producer import."""
import datetime
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUTS = ["CONTRACT.md", "SOURCES.md", "topology.json", "cases.json", "expected.json", "placement.py",
          "produce.py", "verify.py", "run.py", "execute_once.py", "resource_parse.py", "resource_observe.py"]


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise SystemExit("actual nice >= 10 required before producer import")
    destination = ROOT / "observations/run-01"
    if destination.exists():
        raise SystemExit("existing run is immutable")
    destination.mkdir(parents=True)
    inputs = destination / "inputs"
    inputs.mkdir()
    hashes = {}
    for name in INPUTS:
        data = (ROOT / name).read_bytes()
        (inputs / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    from produce import produce
    from verify import verify
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    began = time.monotonic()
    result = produce()
    elapsed = time.monotonic() - began
    result.update(startedAt=started, calculationSeconds=elapsed,
                  toolchain={"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
                  pid=os.getpid(), actualNice=priority, sourceSha256=hashes)
    (destination / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    checked = verify(result)
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise AssertionError("source changed during finite calculation: " + name)
    (ROOT / "verification").mkdir(exist_ok=True)
    (ROOT / "verification/saved-result-check.json").write_text(json.dumps(checked, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": 6, "responses": 12, "inputRefusals": 4,
                      "checks": checked["checks"], "mutationRejections": len(checked["mutations"]),
                      "actualNice": priority, "calculationSeconds": elapsed}))


if __name__ == "__main__":
    main()
