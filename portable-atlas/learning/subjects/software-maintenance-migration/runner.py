"""--record is the only original-evidence update mode; default read-only check."""
import argparse
import hashlib
import json
import platform
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Seed DDL is fixture-owned, not imported from the migrator.
V1 = 'CREATE TABLE "orders" (id TEXT PRIMARY KEY, amount_text TEXT NOT NULL, state TEXT NOT NULL)'
V2 = 'CREATE TABLE "orders" (id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), state_code INTEGER NOT NULL)'


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def record():
    ident = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "observations" / ident
    folder.mkdir(parents=True)
    up = {"direction": "up", "policy": "exact", "inject": "none"}
    down = {"direction": "down", "policy": "exact", "inject": "none"}
    base = [["a", "12.30", "new"], ["b", "0.00", "paid"], ["c", "1.05", "new"]]
    cases = {
        "normal-up": (1, base, [up]),
        "roundtrip": (1, base, [up, down]),
        "empty-roundtrip": (1, [], [up, down]),
        "zero-boundary": (1, [["a", "0.00", "new"]], [up]),
        "lossy-refused": (1, [["a", "1.005", "new"]], [up]),
        "lossy-forced-roundtrip": (1, [["a", "1.005", "new"]], [up | {"policy": "lossy"}, down]),
        "unknown-state-refused": (1, [["a", "12.30", "refunded"]], [up]),
        "noncanonical-refused": (1, [["a", "01.20", "new"]], [up]),
        "overflow-refused": (1, [["a", "92233720368547758.08", "new"]], [up]),
        "failure-after-copy": (1, base, [up | {"inject": "after-copy"}]),
        "failure-after-drop": (1, base, [up | {"inject": "after-drop"}]),
        "down-unknown-refused": (2, [["a", 1230, 30]], [down]),
        "unsupported-version": (99, base, [up]),
    }
    start = now()
    runs = []
    for key, (version, rows, steps) in cases.items():
        case = folder / key
        case.mkdir()
        db = sqlite3.connect(case / "working.sqlite")
        db.execute(V2 if version == 2 else V1)
        db.executemany("INSERT INTO orders VALUES (?, ?, ?)", rows)
        db.execute(f"PRAGMA user_version={version}")
        db.commit()
        db.close()
        shutil.copyfile(case / "working.sqlite", case / "before.sqlite")
        write(case / "input.json", {"source_version": version, "seed_rows": rows, "steps": steps})
        results = []
        for i, step in enumerate(steps, 1):
            stdin = json.dumps(step)
            argv = [sys.executable, "migration.py", str((case / "working.sqlite").relative_to(ROOT))]
            began = now()
            result = subprocess.run(argv, cwd=ROOT, input=stdin, text=True, capture_output=True)
            command = {"argv": ["python3", *argv[1:]], "started_at": began, "completed_at": now(), "stdin": stdin, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
            for stream in ("stdin", "stdout", "stderr"):
                command[stream + "_digest"] = sha(command[stream].encode())
            write(case / f"step-{i}-command.json", command)
            trace = [json.loads(line) for line in result.stdout.splitlines()]
            write(case / f"step-{i}-trace.json", trace)
            shutil.copyfile(case / "working.sqlite", case / f"after-{i}.sqlite")
            results.append({"step": i, "exit_code": result.returncode})
        runs.append({"id": key, "source_version": version, "seed_rows": rows, "steps": steps, "results": results})
    names = ["migration.py", "runner.py", "checker.py", "test_negative.py", "preview.py", "index.html", "README.md", "sources.json", "coverage.json", "skills/atlas-software-maintenance-migration/SKILL.md", "skills/atlas-software-maintenance-migration/route.py"]
    obs = {"execution_id": ident, "started_at": start, "completed_at": now(), "environment": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "os": platform.system(), "release": platform.release(), "machine": platform.machine()}, "source_bindings": {n: sha((ROOT / n).read_bytes()) for n in names}, "runs": runs, "external_services": 0, "production_zero_downtime": False, "other_database_executed": False}
    write(folder / "observation.json", obs)
    oracle = subprocess.run([sys.executable, "checker.py", "--oracle", str(folder.relative_to(ROOT))], cwd=ROOT, text=True, capture_output=True)
    if oracle.returncode:
        raise RuntimeError(oracle.stderr)
    write(folder / "oracle.json", json.loads(oracle.stdout))
    write(folder / "oracle-command.json", {"argv": ["python3", "checker.py", "--oracle", str(folder.relative_to(ROOT))], "stdout": oracle.stdout, "stderr": oracle.stderr, "exit_code": oracle.returncode, "stdout_digest": sha(oracle.stdout.encode()), "stderr_digest": sha(oracle.stderr.encode())})
    index = {p.relative_to(folder).as_posix(): {"digest": sha(p.read_bytes()), "size": p.stat().st_size} for p in folder.rglob("*") if p.is_file()}
    write(folder / "artifact-index.json", index)
    write(ROOT / "current.json", {"directory": str(folder.relative_to(ROOT))})
    print(json.dumps({"directory": str(folder.relative_to(ROOT)), "cases": len(runs), "migration_steps": sum(len(r["steps"]) for r in runs)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="明示的に新規原票を作成する")
    args = parser.parse_args()
    if args.record:
        record()
    else:
        raise SystemExit(subprocess.call([sys.executable, str(ROOT / "checker.py")]))
