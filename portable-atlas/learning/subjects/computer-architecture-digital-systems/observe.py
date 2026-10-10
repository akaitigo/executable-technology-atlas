"""Explicit --write-evidence is the only publication entrypoint. Default is read-only."""
import argparse
import datetime
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def redraw(case):
    rows = []
    for i, event in enumerate(case["normal"]["trace"]):
        y = 105 + i * 52
        label = "read %d → block %d / index %d / tag %d : %s ; eviction %s ; empty-before %d" % (
            event["address"], event["block"], event["index"], event["tag"],
            "HIT" if event["hit"] else "MISS", event["evicted_block"], event["empty_lines_before"])
        rows.append('<rect x="22" y="%d" width="806" height="39" rx="7" fill="#f9e9cf"/><text x="34" y="%d" font-size="15">%s</text>' % (y, y + 25, label))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="850" height="370" viewBox="0 0 850 370">'
            '<rect width="850" height="370" fill="#f5f7ef"/><g font-family="monospace" fill="#203a33">'
            '<text x="24" y="35" font-size="24">Direct-mapped read trace: 0 → 16 → 0 → 16</text>'
            '<text x="24" y="66" font-size="15">16B capacity / 4B line / 4 slots. Only slot 0 is occupied.</text>'
            + ''.join(rows) + '<text x="24" y="342" font-size="13">Actual simulator trace redraw — NOT a screenshot or CPU measurement</text></g></svg>').encode()


def replace(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary.write(data)
        temporary_path = temporary.name
    os.replace(temporary_path, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    if not args.write_evidence:
        completed = subprocess.run([sys.executable, "-B", "check.py"], cwd=ROOT, capture_output=True, timeout=10)
        sys.stdout.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        return completed.returncode
    started = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    completed = subprocess.run([sys.executable, "-B", "check.py"], cwd=ROOT, capture_output=True, timeout=10)
    if completed.returncode:
        raise RuntimeError("checker failed; prior evidence retained")
    result = json.loads(completed.stdout)
    diagram = redraw(result["cases"]["conflict"])
    source_files = ["cache.py", "check.py", "observe.py", "verify.py", "sources.json"]
    record = {"schema_version": 1, "classification": "actual-Python-logical-simulator-run-not-CPU-measurement",
              "started_at": started,
              "finished_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds"),
              "command": "python3 -B check.py", "publish_command": "python3 -B observe.py --write-evidence",
              "attempts": 1, "retries": 0,
              "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                              "os": platform.system(), "release": platform.release(), "architecture": platform.machine()},
              "input": {name: case["input"] for name, case in result["cases"].items()},
              "source_version": result["model_version"],
              "source_hashes": {name: digest((ROOT / name).read_bytes()) for name in source_files},
              "raw_stdout": {"path": "evidence/stdout.json", "digest": digest(completed.stdout)},
              "raw_stderr": {"path": "evidence/stderr.txt", "digest": digest(completed.stderr)},
              "artifacts": [{"path": "evidence/conflict-trace.svg", "digest": digest(diagram), "classification": "actual-logical-trace-redraw-not-screenshot"}],
              "exit_code": completed.returncode, "result": result}
    replace(ROOT / "evidence/stdout.json", completed.stdout)
    replace(ROOT / "evidence/stderr.txt", completed.stderr)
    replace(ROOT / "evidence/conflict-trace.svg", diagram)
    replace(ROOT / "evidence/run.json", (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode())
    replace(ROOT / "data.js", ("window.CACHE_OBSERVATION = " + json.dumps(record, ensure_ascii=False) + ";\n").encode())
    print(json.dumps({"published": True, "observed_at": started, "raw_digest": digest(completed.stdout)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
