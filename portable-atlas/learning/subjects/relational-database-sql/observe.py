#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Capture one real SQLite run and publish its evidence as one directory generation."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from verify import validate_document

HERE = Path(__file__).resolve().parent
SOURCE_FILES = ("experiment.py", "observe.py", "verify.py", "sources.json")


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def publish_directory(staging, destination):
    backup = HERE / f".evidence-previous-{uuid.uuid4().hex}"
    moved_previous = False
    try:
        if destination.exists():
            os.replace(destination, backup)
            moved_previous = True
        os.replace(staging, destination)
    except BaseException:
        if moved_previous and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    else:
        if moved_previous:
            shutil.rmtree(backup)


def main():
    command = [sys.executable, "experiment.py"]
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = subprocess.run(
        command,
        cwd=HERE,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"experiment failed ({result.returncode}): {result.stderr}")
    raw = json.loads(result.stdout)
    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document = {
        "schema_version": 1,
        "subject": "relational-database-sql",
        "lesson": "sql-null-three-valued-logic-join-constraints",
        "status": "passed",
        "observed_at": finished_at,
        "started_at": started_at,
        "command": "python3 experiment.py",
        "reproduce_command": "python3 observe.py && python3 verify.py",
        "process": {"exit_code": 0, "attempts": 1, "retries": 0},
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "sqlite": raw["execution"]["sqlite_version"],
            "sqlite_source_id": raw["execution"]["sqlite_source_id"],
            "os": platform.system(),
            "architecture": platform.machine(),
        },
        "dialect_scope": "SQLite 3.51.0 as exposed by this Python 3.9.6 stdlib runtime",
        "source_digests": {name: sha256(HERE / name) for name in SOURCE_FILES},
        "raw_stdout_sha256": "sha256:" + hashlib.sha256(result.stdout.encode()).hexdigest(),
        "oracle_summary": {
            "equals_null_rows": 0,
            "is_null_rows": 1,
            "inner_join_rows": 3,
            "left_join_rows": 4,
            "left_where_rows": 1,
            "left_on_rows": 3,
            "constraint_rejections": 3,
            "unique_null_rows": 2,
        },
        "evidence_classification": {
            "raw_actual": ["raw-results.json", "stderr.txt"],
            "derived_view": "data.js mirrors this document and raw-results.json for the browser",
        },
    }
    validate_document(document, raw)

    staging = Path(tempfile.mkdtemp(prefix=".evidence-next-", dir=HERE))
    try:
        raw_bytes = result.stdout.encode()
        (staging / "raw-results.json").write_bytes(raw_bytes)
        (staging / "stderr.txt").write_text(result.stderr)
        (staging / "run.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        js_payload = {"run": document, "raw": raw}
        (staging / "data.js").write_text(
            "window.SQL_LESSON = "
            + json.dumps(js_payload, ensure_ascii=False, separators=(",", ":"))
            + ";\n"
        )
        for path in staging.iterdir():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
        publish_directory(staging, HERE / "evidence")
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    print(
        f"Observed SQLite {raw['execution']['sqlite_version']}: "
        "NULL/3VL + JOIN retention + 3 constraint rejections; atomic publish PASS"
    )


if __name__ == "__main__":
    main()
