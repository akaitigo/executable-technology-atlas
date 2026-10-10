"""実buildのcommand stdout/stderrを保存し、成功時だけUI観測を更新。"""
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
    execution_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-supply-chain"
    directory = ROOT / "observations" / execution_id
    directory.mkdir(parents=True, exist_ok=False)
    started = now()
    args = ["python3", "experiment.py", execution_id]
    try:
        result = subprocess.run([sys.executable, *args[1:]], cwd=ROOT, capture_output=True, text=True, timeout=15,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        exit_code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as error:
        exit_code = 124
        stdout, stderr = error.stdout or b"", error.stderr or b""
        stdout = stdout.decode() if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode() if isinstance(stderr, bytes) else stderr
        stderr += "\nouter command timeout 15 seconds"
    command = {"execution_id": execution_id, "command": args, "cwd": "learning/subjects/software-supply-chain",
               "started_at": started, "completed_at": now(), "exit_code": exit_code,
               "stdout": stdout, "stderr": stderr, "stdout_digest": "sha256:" + hashlib.sha256(stdout.encode()).hexdigest()}
    (directory / "command.json").write_text(json.dumps(command, ensure_ascii=False, indent=2) + "\n")
    if exit_code:
        print(json.dumps({"status": "failed", "execution_id": execution_id, "exit_code": exit_code}))
        return exit_code
    observation = json.loads(stdout)
    artifacts = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            artifacts.append({"path": str(path.relative_to(directory)), "digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
                              "size": path.stat().st_size})
    manifest = {"execution_id": execution_id, "signed": False, "artifacts": artifacts,
                "scope": "local-learning-only", "observed_at": observation["completed_at"]}
    (directory / "artifact-index.json").write_text(json.dumps(manifest, indent=2) + "\n")
    published = {"observation": observation, "directory": "observations/" + execution_id,
                 "command": {key: command[key] for key in ["command", "cwd", "started_at", "completed_at", "exit_code", "stdout_digest"]},
                 "artifact_index": manifest}
    temporary = ROOT / ".observation-data.next.js"
    temporary.write_text("window.SUPPLY_CHAIN_OBSERVATION = " + json.dumps(published, ensure_ascii=False) + ";\n")
    temporary.replace(ROOT / "observation-data.js")
    print(json.dumps({"status": "pass", "execution_id": execution_id, "scenario_count": len(observation["scenarios"]),
                      "repeat_build": observation["repeat_build"], "files": len(artifacts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
