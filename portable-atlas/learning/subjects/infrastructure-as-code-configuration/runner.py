"""New observations require explicit --record. Use checker.py for normal reads."""
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
    p = argparse.ArgumentParser()
    p.add_argument("--record", action="store_true")
    args = p.parse_args()
    if not args.record:
        raise SystemExit("No output changed. checker.py is read-only; --record explicitly creates a new synthetic observation.")
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-iac")
    start = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run([sys.executable, "experiment.py", token], cwd=ROOT, capture_output=True, text=True,
                           timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        code, out, err = r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        code = 124
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        err += "\nexperiment timeout: 20 seconds\n"
    err = err.replace(str(ROOT), "<module>")
    err = re.sub(r'File "[^"\n]*/([^/"\n]+)"', r'File "<runtime>/\1"', err)
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=True)
    command = {"execution_id": token, "command": ["python3", "experiment.py", token],
               "cwd": "learning/subjects/infrastructure-as-code-configuration", "started_at": start,
               "completed_at": datetime.now(timezone.utc).isoformat(), "exit_code": code,
               "stdout": out, "stderr": err, "stdout_digest": sha(out.encode()),
               "redaction": "stderr absolute module/runtime paths replaced; error and line numbers retained"}
    (folder / "command.json").write_text(json.dumps(command, ensure_ascii=False, indent=2) + "\n")
    if code:
        print(err, file=sys.stderr)
        raise SystemExit(code)
    obs = json.loads(out)
    index = {f.relative_to(folder).as_posix(): {"digest": sha(f.read_bytes()), "size": f.stat().st_size}
             for f in sorted(folder.rglob("*")) if f.is_file()}
    (folder / "artifact-index.json").write_text(json.dumps(index, indent=2) + "\n")
    payload = {"directory": "observations/" + token, "observation": obs}
    temp = ROOT / (".observation-" + token + ".js")
    temp.write_text("window.IAC_OBSERVATION = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    os.replace(temp, ROOT / "observation-data.js")
    print(json.dumps({"execution_id": token, "exit_code": code, "indexed_files": len(index), "cases": len(obs["scenarios"])}))


if __name__ == "__main__":
    main()
