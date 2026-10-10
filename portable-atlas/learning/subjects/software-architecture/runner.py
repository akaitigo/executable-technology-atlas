"""Default read-only; --record runs fixed input through real worker processes."""
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


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def record():
    ident = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "observations" / ident
    folder.mkdir(parents=True)
    base = {"id": "a", "sku": "book", "quantity": 2}
    command = lambda payload, **kwargs: {"payload": payload, **kwargs}
    scenarios = {
        "normal": [command(base)],
        "quantity-one": [command(base | {"quantity": 1})],
        "quantity-hundred": [command(base | {"quantity": 100})],
        "quantity-zero": [command(base | {"quantity": 0})],
        "quantity-over": [command(base | {"quantity": 101})],
        "quantity-bool": [command(base | {"quantity": True})],
        "spaces": [command(base | {"id": " a ", "sku": " book "})],
        "blank-sku": [command(base | {"sku": " "})],
        "missing-id": [command({"sku": "book", "quantity": 2})],
        "duplicate-id": [command(base), command(base | {"quantity": 3})],
        "unavailable": [command(base, unavailable=True)],
        "invalid-unavailable": [command(base | {"quantity": 0}, unavailable=True)],
    }
    start = now()
    runs = []
    for variant in ("port", "tied"):
        for storage in ("memory", "sqlite"):
            for scenario, inputs in scenarios.items():
                key = f"{variant}-{storage}-{scenario}"
                case = folder / key
                case.mkdir()
                stdin = json.dumps(inputs, ensure_ascii=False)
                argv = [sys.executable, "worker.py", variant, storage, str(case.relative_to(ROOT))]
                began = now()
                result = subprocess.run(argv, cwd=ROOT, input=stdin, text=True, capture_output=True)
                command_record = {"argv": ["python3", *argv[1:]], "started_at": began, "completed_at": now(), "stdin": stdin, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
                for stream in ("stdin", "stdout", "stderr"):
                    command_record[stream + "_digest"] = sha(command_record[stream].encode())
                write(case / "command.json", command_record)
                write(case / "input.json", inputs)
                trace = [json.loads(line) for line in result.stdout.splitlines()]
                write(case / "trace.json", trace)
                runs.append({"id": key, "variant": variant, "storage": storage, "scenario": scenario, "input": inputs})
    names = ["ports.py", "domain.py", "adapters.py", "bad.py", "worker.py", "runner.py", "checker.py", "test_negative.py", "preview.py", "index.html", "README.md", "sources.json", "coverage.json", "skills/atlas-software-architecture/SKILL.md", "skills/atlas-software-architecture/route.py"]
    obs = {"execution_id": ident, "started_at": start, "completed_at": now(), "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "os": platform.system(), "release": platform.release(), "machine": platform.machine()}, "source_bindings": {n: sha((ROOT / n).read_bytes()) for n in names}, "runs": runs, "external_services": 0, "performance_measured": False, "all_quality_attributes_demonstrated": False}
    write(folder / "observation.json", obs)
    oracle = subprocess.run([sys.executable, "checker.py", "--oracle", str(folder.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    if oracle.returncode:
        raise RuntimeError(oracle.stderr)
    write(folder / "oracle.json", json.loads(oracle.stdout))
    write(folder / "oracle-command.json", {"argv": ["python3", "checker.py", "--oracle", str(folder.relative_to(ROOT))], "stdout": oracle.stdout, "stderr": oracle.stderr, "exit_code": oracle.returncode, "stdout_digest": sha(oracle.stdout.encode()), "stderr_digest": sha(oracle.stderr.encode())})
    index = {p.relative_to(folder).as_posix(): {"digest": sha(p.read_bytes()), "size": p.stat().st_size} for p in folder.rglob("*") if p.is_file()}
    write(folder / "artifact-index.json", index)
    write(ROOT / "current.json", {"directory": str(folder.relative_to(ROOT))})
    print(json.dumps({"directory": str(folder.relative_to(ROOT)), "scenarios": len(scenarios), "runs": len(runs)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="固定48実行を新規原票に記録")
    args = parser.parse_args()
    if args.record:
        record()
    else:
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / "checker.py")]))
