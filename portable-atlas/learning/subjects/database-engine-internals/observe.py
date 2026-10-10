#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Capture a new process and atomically publish a validated evidence generation."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from verify import INPUTS, digest, validate, validate_saved

HERE = Path(__file__).resolve().parent


def publish(staging, destination):
    backup = destination.with_name(".evidence-previous-" + uuid.uuid4().hex)
    previous = destination.exists()
    if previous:
        os.replace(destination, backup)
    try:
        os.replace(staging, destination)
    except BaseException:
        if previous:
            os.replace(backup, destination)
        raise
    if previous:
        shutil.rmtree(backup)


def main():
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = subprocess.run([sys.executable, "experiment.py"], cwd=HERE, capture_output=True,
                            timeout=15, check=False)
    if result.returncode:
        raise RuntimeError("Actual runner failed: " + result.stderr.decode())
    raw = json.loads(result.stdout)
    validate(raw)
    report = {
        "subject": "database-engine-internals", "status": "passed",
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": "python3 experiment.py", "runtime": raw["runtime"],
        "process": {"attempts": 1, "retries": 0, "exit_code": result.returncode},
        "stdout_digest": digest(result.stdout), "stderr_digest": digest(result.stderr),
        "source_digests": {name: digest((HERE / name).read_bytes()) for name in INPUTS},
        "publication": "full-run-passed; staged-directory-rename-with-rollback; retain-prior-success",
        "oracle": "independent 16-row result multiset and order; 3 raw plan/schema variants",
    }
    staging_root = Path(tempfile.mkdtemp(prefix=".observation-", dir=HERE))
    staging = staging_root / "evidence"
    staging.mkdir()
    try:
        (staging / "stdout.json").write_bytes(result.stdout)
        (staging / "stderr.txt").write_bytes(result.stderr)
        (staging / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        (staging / "data.js").write_text("window.ENGINE_LESSON = " + json.dumps(
            {"run": report, "raw": raw}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + ";\n")
        for path in staging.iterdir():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
        # Validate candidate against source files without modifying the published generation.
        for name in INPUTS:
            (staging_root / name).symlink_to(HERE / name)
        validate_saved(staging_root)
        publish(staging, HERE / "evidence")
    finally:
        shutil.rmtree(staging_root)
    print("PASS: actual SQLite %s; SCAN / SEARCH / SCAN; 16 equal rows in each case" % raw["runtime"]["sqlite_version"])


if __name__ == "__main__":
    main()
