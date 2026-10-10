"""Only explicit --record creates a new observation; checker.py is read-only."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    if not parser.parse_args().record:
        raise SystemExit("No output changed. Use read-only checker.py; --record explicitly creates a synthetic observation.")
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-scheduler")
    start = datetime.now(timezone.utc).isoformat()
    try:
        run = subprocess.run([sys.executable, "experiment.py", token], cwd=ROOT, capture_output=True, text=True, timeout=20,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        code, out, err = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as e:
        code = 124
        out = e.stdout or ""
        err = e.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        err += "\nexperiment timeout: 20 seconds\n"
    err = err.replace(str(ROOT), "<module>")
    err = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', err)
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=True)
    command = {"execution_id": token, "command": ["python3", "experiment.py", token], "cwd": "learning/subjects/container-orchestration",
               "started_at": start, "completed_at": datetime.now(timezone.utc).isoformat(), "exit_code": code,
               "stdout": out, "stderr": err, "stdout_digest": sha(out.encode()), "stderr_digest": sha(err.encode()),
               "redaction": "stderr absolute module/runtime paths replaced; primary error and line numbers retained"}
    (folder / "command.json").write_text(json.dumps(command, ensure_ascii=False, indent=2) + "\n")
    if code:
        print(err, file=sys.stderr)
        raise SystemExit(code)
    observation = json.loads(out)
    oracle_start = datetime.now(timezone.utc).isoformat()
    oracle = subprocess.run([sys.executable, "checker.py", "--oracle-json", "observations/" + token], cwd=ROOT,
                            capture_output=True, text=True, timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    oracle_error = oracle.stderr.replace(str(ROOT), "<module>")
    oracle_error = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', oracle_error)
    oracle_command = {"execution_id": token, "command": ["python3", "checker.py", "--oracle-json", "observations/" + token],
                      "started_at": oracle_start, "completed_at": datetime.now(timezone.utc).isoformat(), "exit_code": oracle.returncode,
                      "stdout": oracle.stdout, "stderr": oracle_error, "stdout_digest": sha(oracle.stdout.encode()), "stderr_digest": sha(oracle_error.encode()),
                      "redaction": "stderr absolute module/runtime paths replaced"}
    (folder / "oracle-command.json").write_text(json.dumps(oracle_command, ensure_ascii=False, indent=2) + "\n")
    if oracle.returncode:
        raise SystemExit(oracle.returncode)
    oracle_report = json.loads(oracle.stdout)
    rejected = [r["id"] for r in oracle_report["rows"] if r["verdict"] == "rejected"]
    if rejected != ["bad-over-capacity", "bad-failure"]:
        raise SystemExit("independent oracle mismatch; prior observation pointer preserved")
    (folder / "oracle-report.json").write_text(json.dumps(oracle_report, ensure_ascii=False, indent=2) + "\n")
    index = {f.relative_to(folder).as_posix(): {"digest": sha(f.read_bytes()), "size": f.stat().st_size} for f in sorted(folder.rglob("*")) if f.is_file()}
    (folder / "artifact-index.json").write_text(json.dumps(index, indent=2) + "\n")
    payload = {"directory": "observations/" + token, "observation": observation, "oracle": oracle_report}
    temp = ROOT / (".observation-" + token + ".js")
    temp.write_text("window.SCHEDULER_OBSERVATION = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    os.replace(temp, ROOT / "observation-data.js")
    print(json.dumps({"execution_id": token, "exit_code": code, "cases": len(observation["scenarios"]), "indexed_files": len(index)}))


if __name__ == "__main__":
    main()
