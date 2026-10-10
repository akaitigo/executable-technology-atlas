"""Atlas: fresh資源記録と優先度実値を確認後、一つの有限子だけを開始する。"""
import datetime
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = Path("/usr/bin/python3")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--decision', type=Path, required=True)
    args = parser.parse_args()
    directory = ROOT / "verification"
    directory.mkdir(exist_ok=True)
    observation = directory / "resource-before-calculation.json"
    gate = json.loads(observation.read_text())
    decision_bytes = args.decision.read_bytes()
    decision = json.loads(decision_bytes)
    stamp = datetime.datetime.fromisoformat(gate["observedAt"])
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
    if not gate.get("readTrusted") or not 0 <= age <= 300:
        raise SystemExit("fresh trusted resource observation required")
    if (decision.get('scope') != 'agent-resume-uncertainty' or decision.get('allowed') is not True
        or decision.get('observationSha256') != hashlib.sha256(observation.read_bytes()).hexdigest()
        or decision.get('rootSlot') is not True or decision.get('rootGuiIdle') is not True
        or decision.get('otherTargets') != 0 or not decision.get('authorization')):
        raise SystemExit('matching root decision and exclusive slot required')
    all_rows = {x['pid']: x for x in gate['processObservation']['processes']}
    identity = ('pid', 'ppid', 'lstart', 'command')
    approved = decision.get('identities', [])
    for known in approved:  # Check PID identity before the browser-name filter.
        actual = all_rows.get(known['pid'])
        if actual is not None and not all(actual[k] == known[k] for k in identity):
            raise SystemExit('approved PID identity changed')
    browsers = gate['processObservation']['browsers']
    if not isinstance(browsers, list) or not all(any(all(x[k] == a[k] for k in identity) for a in approved) for x in browsers):
        raise SystemExit('browser outside this observation-specific root decision')
    if (ROOT / "observations/run-01").exists() or (directory / "execution.json").exists():
        raise SystemExit("existing attempt is immutable; no automatic retry")
    record = {"Atlas": "Agent再開判断の実行記録", "attempt": 1, "retry": 0, "children": [],
              "deadlineSeconds": 15, "resourceObservation": "resource-before-calculation.json",
              "resourceSha256": hashlib.sha256(observation.read_bytes()).hexdigest(),
              "rootDecision": {"path": str(args.decision.resolve()), "sha256": hashlib.sha256(decision_bytes).hexdigest(), "record": decision}}
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
    child = subprocess.Popen([str(PYTHON), "-B", "run.py"], cwd=ROOT, stdout=subprocess.PIPE,
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
