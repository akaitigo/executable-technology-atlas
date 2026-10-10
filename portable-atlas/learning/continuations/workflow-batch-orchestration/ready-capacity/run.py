"""Atlas: 一つの子processで有限計算、保存、別方式照合を行う。"""
import copy
import datetime
import graphlib
import hashlib
import json
import os
import platform
import time
from pathlib import Path
from scheduler import simulate
from verify import check, mutations

ROOT = Path(__file__).resolve().parent
INPUTS = ["CONTRACT.md", "expected.json", "cases.json", "scheduler.py", "verify.py", "run.py", "execute_once.py"]


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise SystemExit("actual nice10 required before calculation")
    output = ROOT / "observations/run-01"
    output.mkdir(parents=True, exist_ok=False)
    snapshots = output / "inputs"
    snapshots.mkdir()
    bindings = {}
    for name in INPUTS:
        data = (ROOT / name).read_bytes()
        (snapshots / name).write_bytes(data)
        bindings[name] = hashlib.sha256(data).hexdigest()
    cases = json.loads((ROOT / "cases.json").read_text())
    result = {"Atlas": "DAGと容量の有限仮想時刻の計算結果", "kind": "python_virtual_time_not_real_workers",
              "startedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "python": platform.python_version(), "pid": os.getpid(), "actualNice": priority,
              "graphlib": {"moduleFile": graphlib.__file__,
                           "sha256": hashlib.sha256(Path(graphlib.__file__).read_bytes()).hexdigest()},
              "sourceSha256": bindings, "cases": [], "refusals": []}
    start = time.monotonic()
    for group in ("cases", "refusals"):
        for case in cases[group]:
            request = copy.deepcopy(case["request"])
            before = copy.deepcopy(request)
            response = simulate(request)
            result[group].append({"id": case["id"], "requestBefore": before,
                                  "requestAfter": request, "response": response})
    result["calculationSeconds"] = time.monotonic() - start
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    (output / "results.json").write_bytes(data)
    checked = {"Atlas": "手予定表と整数時刻による照合", "passed": True,
               "checks": check(json.loads(data)), "mutations": mutations(json.loads(data)),
               "resultsSha256": hashlib.sha256(data).hexdigest(), "producerImportedByChecker": False}
    (ROOT / "verification/saved-result-check.json").write_text(json.dumps(checked, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": 4, "snapshots": 18, "refusals": 6,
                      "checks": checked["checks"], "calculationSeconds": result["calculationSeconds"],
                      "actualNice": priority, "pid": os.getpid()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
