"""Explicit recording only; default checker remains read-only."""
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


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="generate a new task-owned observation")
    args = parser.parse_args()
    if not args.record:
        raise SystemExit("No output changed. Use checker.py for read-only verification; --record creates new raw artifacts.")
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-oci-layer")
    command = [sys.executable, "experiment.py", token]
    start = datetime.now(timezone.utc).isoformat()
    try:
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20,
                             env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as error:
        code = 124
        stdout = (error.stdout or b"").decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = (error.stderr or b"").decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
        stderr += "\nexperiment timeout: 20 seconds\n"
    # Keep command failure and traceback, but do not persist private absolute paths.
    stderr = stderr.replace(str(ROOT), "<module>")
    stderr = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', stderr)
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=True)
    record = {"execution_id": token, "command": ["python3", "experiment.py", token],
              "cwd": "learning/subjects/oci-container-engineering", "started_at": start,
              "completed_at": datetime.now(timezone.utc).isoformat(), "exit_code": code,
              "stdout": stdout, "stderr": stderr, "stdout_digest": digest(stdout.encode()),
              "redaction": "stderr absolute module/runtime paths replaced; error and line numbers retained"}
    (folder / "command.json").write_text(json.dumps(record, indent=2) + "\n")
    if code:
        print(stderr, file=sys.stderr)
        raise SystemExit(code)
    observation = json.loads(stdout)
    files = {p.relative_to(folder).as_posix(): {"digest": digest(p.read_bytes()), "size": p.stat().st_size}
             for p in sorted(folder.rglob("*")) if p.is_file()}
    (folder / "artifact-index.json").write_text(json.dumps(files, indent=2) + "\n")
    payload = {"directory": "observations/" + token, "observation": observation}
    temp = ROOT / (".observation-" + token + ".js")
    temp.write_text("window.OCI_OBSERVATION = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    os.replace(temp, ROOT / "observation-data.js")
    print(json.dumps({"execution_id": token, "exit_code": code, "indexed_files": len(files),
                      "cases": len(observation["scenarios"])}))


if __name__ == "__main__":
    main()
