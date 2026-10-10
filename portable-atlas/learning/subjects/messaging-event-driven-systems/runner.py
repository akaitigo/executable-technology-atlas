"""Explicit observation update only; no option does not change any file."""
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


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def command(args, token, timeout):
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        code, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        code = 124
        out = e.stdout or ""
        err = e.stderr or ""
        if isinstance(out, bytes):
            out = out.decode(errors="replace")
        if isinstance(err, bytes):
            err = err.decode(errors="replace")
        err += "\nbounded command timeout\n"
    err = err.replace(str(ROOT), "<module>")
    err = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', err)
    return {"execution_id": token, "command": ["python3", *args], "cwd": "learning/subjects/messaging-event-driven-systems",
            "started_at": started, "completed_at": datetime.now(timezone.utc).isoformat(), "exit_code": code,
            "stdout": out, "stderr": err, "stdout_digest": sha(out.encode()), "stderr_digest": sha(err.encode()),
            "redaction": "stderr absolute module/runtime paths replaced; primary error/line numbers retained"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    if not parser.parse_args().record:
        raise SystemExit("No output changed. checker.py is read-only; --record explicitly creates a task-owned SQLite observation.")
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-events")
    record = command(["experiment.py", token], token, 30)
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    if record["exit_code"]:
        print(record["stderr"], file=sys.stderr)
        raise SystemExit(record["exit_code"])
    obs = json.loads(record["stdout"])
    oracle_command = command(["checker.py", "--oracle-json", "observations/" + token], token, 10)
    (folder / "oracle-command.json").write_text(json.dumps(oracle_command, ensure_ascii=False, indent=2) + "\n")
    if oracle_command["exit_code"]:
        print(oracle_command["stderr"], file=sys.stderr)
        raise SystemExit(oracle_command["exit_code"])
    oracle = json.loads(oracle_command["stdout"])
    (folder / "oracle-report.json").write_text(json.dumps(oracle, ensure_ascii=False, indent=2) + "\n")
    if any(not r["matches_expected"] for r in oracle["rows"]):
        raise SystemExit("independent oracle mismatch; prior observation retained")
    index = {p.relative_to(folder).as_posix(): {"digest": sha(p.read_bytes()), "size": p.stat().st_size} for p in sorted(folder.rglob("*")) if p.is_file()}
    (folder / "artifact-index.json").write_text(json.dumps(index, indent=2) + "\n")
    payload = {"directory": "observations/" + token, "observation": obs, "oracle": oracle}
    temp = ROOT / (".observation-" + token + ".js")
    temp.write_text("window.EVENT_OBSERVATION = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    os.replace(temp, ROOT / "observation-data.js")
    print(json.dumps({"execution_id": token, "cases": len(obs["scenarios"]), "indexed_files": len(index), "exit_code": 0}))


if __name__ == "__main__":
    main()
