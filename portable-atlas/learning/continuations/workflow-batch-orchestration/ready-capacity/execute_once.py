"""Atlas: fresh資源記録と優先度実値を確認後、一つの有限子だけを開始する。"""
import datetime
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    directory = ROOT / "verification"
    directory.mkdir(exist_ok=True)
    gate = json.loads((directory / "resource-before-calculation.json").read_text())
    stamp = datetime.datetime.fromisoformat(gate["observedAt"])
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
    if not gate.get("allowed") or not 0 <= age <= 300:
        raise SystemExit("fresh allowed resource observation required")
    if (ROOT / "observations/run-01").exists() or (directory / "execution.json").exists():
        raise SystemExit("existing attempt is immutable; no automatic retry")
    record = {"Atlas": "有限計算の実行記録", "attempt": 1, "retry": 0, "children": [],
              "deadlineSeconds": 15, "resourceObservation": "resource-before-calculation.json"}
    try:
        current = os.getpriority(os.PRIO_PROCESS, 0)
        if current < 10:
            os.setpriority(os.PRIO_PROCESS, 0, 10)
        record["actualNice"] = os.getpriority(os.PRIO_PROCESS, 0)
        if record["actualNice"] < 10:
            raise RuntimeError("nice guard failed")
    except (OSError, RuntimeError) as exc:
        record.update(started=False, error=str(exc))
        (directory / "execution.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        raise SystemExit("priority guard refused; child not started")
    began = time.monotonic()
    child = subprocess.Popen([sys.executable, "-B", "run.py"], cwd=ROOT, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, start_new_session=True)
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
    record.update(started=True, elapsedSeconds=time.monotonic() - began, passed=child.returncode == 0 and not timed_out)
    record["children"].append({"pid": child.pid, "exitCode": child.returncode, "timeout": timed_out,
                               "reaped": child.poll() is not None, "stdout": stdout[:8192], "stderr": stderr[:8192]})
    (directory / "execution.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(record, ensure_ascii=False))
    raise SystemExit(0 if record["passed"] else 1)


if __name__ == "__main__":
    main()
