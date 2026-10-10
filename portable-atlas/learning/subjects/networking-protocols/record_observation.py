"""実コマンド生stdout/stderrをrun毎に保持。観測成功時だけUIデータを公開。"""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def main():
    execution_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-tcp-stream"
    target = ROOT / "observations" / execution_id
    target.mkdir(parents=True, exist_ok=False)
    started = now()
    command = ["python3", "observe_tcp.py"]
    try:
        process = subprocess.run([sys.executable, "observe_tcp.py"], cwd=ROOT, capture_output=True,
                                 text=True, timeout=20, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        code, stdout, stderr = process.returncode, process.stdout, process.stderr
    except subprocess.TimeoutExpired as error:
        code, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
        stderr += "\nouter timeout 20 seconds"
    record = {"execution_id": execution_id, "started_at": started, "completed_at": now(),
              "command": command, "cwd": "learning/subjects/networking-protocols",
              "exit_code": code, "stdout": stdout, "stderr": stderr,
              "stdout_digest": "sha256:" + hashlib.sha256(stdout.encode()).hexdigest(),
              "scope": "learning-only", "counts_toward_subject_completion": False}
    (target / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    if code:
        print(json.dumps({"status": "failed", "execution_id": execution_id, "exit_code": code}))
        return code
    document = json.loads(stdout)
    document["execution_id"] = execution_id
    observation = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    (target / "observation.json").write_text(observation)
    manifest = {"execution_id": execution_id, "status": document["status"], "observed_at": document["completed_at"],
                "artifacts": [{"path": name, "digest": "sha256:" + hashlib.sha256((target / name).read_bytes()).hexdigest()}
                              for name in ["command.json", "observation.json"]]}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    published = {"observation": document, "record": {key: record[key] for key in
                 ["command", "cwd", "exit_code", "started_at", "completed_at", "stdout_digest"]},
                 "artifact_directory": "observations/" + execution_id, "manifest": manifest}
    temporary = ROOT / ".observation-data.next.js"
    temporary.write_text("window.TCP_OBSERVATION = " + json.dumps(published, ensure_ascii=False) + ";\n")
    temporary.replace(ROOT / "observation-data.js")
    print(json.dumps({"status": "pass", "execution_id": execution_id,
                      "recv_lengths": [run["oracle"]["recv_lengths"] for run in document["runs"]],
                      "cleanup": [run["cleanup"] for run in document["runs"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
