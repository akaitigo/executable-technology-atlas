"""Explicit --record creates evidence; default verifies without writing."""
import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "id,quantity,price\na,2,1.25\nb,1,0.10\na,2,1.25\nbad,nope,2.00\n"


def sha(raw): return "sha256:" + hashlib.sha256(raw).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def record():
    ident = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "observations" / ident
    folder.mkdir(parents=True)
    normal = {"csv": BASE, "mode": "replace", "bad_rows": "quarantine", "inject": "none"}
    cases = {
        "normal": [normal],
        "replace-rerun": [normal, normal],
        "append-rerun": [normal | {"mode": "append"}, normal | {"mode": "append"}],
        "silent-skip": [normal | {"bad_rows": "silent-skip"}],
        "all-bad": [normal | {"csv": "id,quantity,price\nx,0,1.00\ny,2,1.005\n"}],
        "empty": [normal | {"csv": "id,quantity,price\n"}],
        "zero-price": [normal | {"csv": "id,quantity,price\nz,1,0.00\n"}],
        "quantity-upper": [normal | {"csv": "id,quantity,price\nu,100,1.00\n"}],
        "quantity-over": [normal | {"csv": "id,quantity,price\nu,101,1.00\n"}],
        "conflicting-id": [normal | {"csv": "id,quantity,price\na,2,1.25\na,3,1.25\n"}],
        "schema-refusal-after-success": [normal, normal | {"csv": "id,price,quantity\na,1.25,2\n"}],
        "transform-failure-after-success": [normal, normal | {"csv": "id,quantity,price\nc,1,1.00\n", "inject": "transform"}],
        "publish-failure-after-success": [normal, normal | {"csv": "id,quantity,price\nc,1,1.00\n", "inject": "before-publish"}],
    }
    started = now()
    runs = []
    for key, requests in cases.items():
        case = folder / key
        case.mkdir()
        write(case / "input.json", requests)
        attempts = []
        for i, request in enumerate(requests, 1):
            stdin = json.dumps(request, ensure_ascii=False)
            began = now()
            result = subprocess.run([sys.executable, "pipeline.py", str((case / "publication").relative_to(ROOT))], cwd=ROOT, input=stdin, text=True, capture_output=True)
            command = {"argv": ["python3", "pipeline.py", str((case / "publication").relative_to(ROOT))], "started_at": began, "completed_at": now(), "stdin": stdin, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
            for stream in ("stdin", "stdout", "stderr"):
                command[stream + "_digest"] = sha(command[stream].encode())
            write(case / f"attempt-{i}-command.json", command)
            write(case / f"attempt-{i}-trace.json", [json.loads(line) for line in result.stdout.splitlines()])
            (case / f"attempt-{i}-source.csv").write_bytes(request["csv"].encode())
            state = case / f"after-{i}"
            state.mkdir()
            publication = case / "publication"
            if (publication / "current.json").exists():
                pointer = json.loads((publication / "current.json").read_text())
                shutil.copyfile(publication / "current.json", state / "current.json")
                for source in (publication / "generations" / pointer["generation"]).iterdir():
                    shutil.copyfile(source, state / source.name)
            attempts.append({"attempt": i, "exit_code": result.returncode})
        runs.append({"id": key, "requests": requests, "attempts": attempts})
    names = ["pipeline.py", "runner.py", "checker.py", "test_negative.py", "preview.py", "index.html", "README.md", "sources.json", "coverage.json", "skills/atlas-data-engineering-orchestration/SKILL.md", "skills/atlas-data-engineering-orchestration/route.py"]
    obs = {"execution_id": ident, "started_at": started, "completed_at": now(), "environment": {"python": platform.python_version(), "os": platform.system(), "release": platform.release(), "machine": platform.machine()}, "source_bindings": {n: sha((ROOT / n).read_bytes()) for n in names}, "runs": runs, "external_services": 0, "production_scheduler": False, "remote_ETL": False}
    write(folder / "observation.json", obs)
    oracle = subprocess.run([sys.executable, "checker.py", "--oracle", str(folder.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    if oracle.returncode: raise RuntimeError(oracle.stderr)
    write(folder / "oracle.json", json.loads(oracle.stdout))
    write(folder / "oracle-command.json", {"argv": ["python3", "checker.py", "--oracle", str(folder.relative_to(ROOT))], "stdout": oracle.stdout, "stderr": oracle.stderr, "exit_code": oracle.returncode, "stdout_digest": sha(oracle.stdout.encode()), "stderr_digest": sha(oracle.stderr.encode())})
    write(folder / "artifact-index.json", {p.relative_to(folder).as_posix(): {"digest": sha(p.read_bytes()), "size": p.stat().st_size} for p in folder.rglob("*") if p.is_file()})
    write(ROOT / "current.json", {"directory": str(folder.relative_to(ROOT))})
    print(json.dumps({"directory": str(folder.relative_to(ROOT)), "cases": len(runs), "attempts": sum(len(r["requests"]) for r in runs)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    if args.record: record()
    else: raise SystemExit(subprocess.call([sys.executable, str(ROOT / "checker.py")]))
