"""Explicit --record regenerates evidence; default is read-only verification."""
import argparse
import hashlib
import json
import platform
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def request(mode="atomic", **changes):
    return dict(id="a", name="教材", quantity=2, mode=mode, fail_second=False, **changes)


def record():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "observations" / run_id
    folder.mkdir(parents=True)
    scenarios = {
        "atomic-normal": [request()],
        "nonatomic-normal": [request("nonatomic")],
        "atomic-second-failure": [request() | {"fail_second": True}],
        "nonatomic-second-failure": [request("nonatomic") | {"fail_second": True}],
        "quantity-one": [request() | {"quantity": 1}],
        "quantity-hundred": [request() | {"quantity": 100}],
        "quantity-zero": [request() | {"quantity": 0}],
        "quantity-over": [request() | {"quantity": 101}],
        "quantity-bool": [request() | {"quantity": True}],
        "blank-name": [request() | {"name": " "}],
        "duplicate-id": [request(), request()],
        "failure-then-next-request": [request() | {"fail_second": True}, request() | {"id": "b"}],
    }
    rows = []
    started = now()
    for ident, inputs in scenarios.items():
        case = folder / ident
        case.mkdir()
        db = sqlite3.connect(case / "service.sqlite")
        db.executescript("CREATE TABLE orders(id TEXT PRIMARY KEY, name TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity BETWEEN 1 AND 100)); CREATE TABLE outbox(order_id TEXT PRIMARY KEY REFERENCES orders(id), event TEXT NOT NULL, payload TEXT NOT NULL);")
        db.close()
        stdin = json.dumps(inputs, ensure_ascii=False)
        began = now()
        result = subprocess.run([sys.executable, "service.py", str((case / "service.sqlite").relative_to(ROOT))], cwd=ROOT, input=stdin, text=True, capture_output=True)
        command = {"argv": ["python3", "service.py", "service.sqlite"], "started_at": began, "completed_at": now(), "stdin": stdin, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
        for key in ("stdin", "stdout", "stderr"):
            command[key + "_digest"] = digest(command[key].encode())
        write(case / "command.json", command)
        write(case / "input.json", inputs)
        trace = [json.loads(line) for line in result.stdout.splitlines()]
        write(case / "trace.json", trace)
        rows.append({"id": ident, "input": inputs, "trace": trace})
    names = ["service.py", "runner.py", "checker.py", "test_negative.py", "preview.py", "index.html", "README.md", "coverage.json", "sources.json", "skills/atlas-backend-application-engineering/SKILL.md", "skills/atlas-backend-application-engineering/route.py"]
    obs = {"execution_id": run_id, "started_at": started, "completed_at": now(), "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "os": platform.system(), "release": platform.release(), "machine": platform.machine()}, "source_bindings": {n: digest((ROOT / n).read_bytes()) for n in names}, "scenarios": rows, "external_services": 0, "framework_executed": False, "concurrency_measured": False}
    write(folder / "observation.json", obs)
    oracle = subprocess.run([sys.executable, "checker.py", "--oracle", str(folder.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    if oracle.returncode:
        raise RuntimeError(oracle.stderr)
    write(folder / "oracle.json", json.loads(oracle.stdout))
    write(folder / "oracle-command.json", {"argv": ["python3", "checker.py", "--oracle", str(folder.relative_to(ROOT))], "stdout": oracle.stdout, "stderr": oracle.stderr, "exit_code": oracle.returncode, "stdout_digest": digest(oracle.stdout.encode()), "stderr_digest": digest(oracle.stderr.encode())})
    index = {p.relative_to(folder).as_posix(): {"digest": digest(p.read_bytes()), "size": p.stat().st_size} for p in folder.rglob("*") if p.is_file()}
    write(folder / "artifact-index.json", index)
    write(ROOT / "current.json", {"directory": str(folder.relative_to(ROOT))})
    print(json.dumps({"directory": str(folder.relative_to(ROOT)), "cases": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="明示的に原票を新規作成する")
    args = parser.parse_args()
    if args.record:
        record()
    else:
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / "checker.py")]))
