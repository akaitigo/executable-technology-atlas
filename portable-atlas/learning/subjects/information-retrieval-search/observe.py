#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Evidence is only updated with --write-evidence; ordinary invocation is read-only."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from verify import INPUTS, digest, validate, validate_saved, negatives

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


def capture():
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result = subprocess.run([sys.executable, "-B", "experiment.py"], cwd=HERE, capture_output=True,
                            timeout=15, check=False)
    if result.returncode:
        raise RuntimeError("runner failed: " + result.stderr.decode())
    raw = json.loads(result.stdout)
    verdicts = validate(raw)
    report = {"subject": "information-retrieval-search", "status": "passed-with-demonstrated-anomalies",
        "command": "python3 -B experiment.py", "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime": raw["runtime"], "input": raw["input"],
        "process": {"attempts": 1, "retries": 0, "exit_code": result.returncode},
        "source_digests": {name: digest((HERE / name).read_bytes()) for name in INPUTS},
        "stdout_digest": digest(result.stdout),
        "publication": "full-run-passed; directory rename with rollback; retain prior success"}
    root = Path(tempfile.mkdtemp(prefix=".candidate-", dir=HERE))
    staging = root / "evidence"
    staging.mkdir()
    try:
        (staging / "stdout.json").write_bytes(result.stdout)
        (staging / "stderr.txt").write_bytes(result.stderr)
        (staging / "run.json").write_text(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
        (staging / "verification.json").write_text(json.dumps({"oracle": "independent-character-walk-fullscan", "verdicts": verdicts}, sort_keys=True, ensure_ascii=False, indent=2) + "\n")
        (staging / "data.js").write_text("window.IR_LESSON = " + json.dumps({"raw": raw, "run": report, "verdicts": verdicts}, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + ";\n")
        inventory = {name: {"digest": digest((staging/name).read_bytes()), "bytes": (staging/name).stat().st_size}
                     for name in ("stdout.json", "stderr.txt", "run.json", "verification.json", "data.js")}
        (staging / "artifacts.json").write_text(json.dumps(inventory, sort_keys=True, indent=2) + "\n")
        for path in staging.iterdir():
            with path.open("rb") as handle:
                os.fsync(handle.fileno())
        for name in INPUTS:
            (root/name).parent.mkdir(parents=True, exist_ok=True)
            (root/name).symlink_to(HERE/name)
        validate_saved(root)
        publish(staging, HERE/"evidence")
    finally:
        shutil.rmtree(root)
    print("PASS: 13 actual queries; stale-hit + missing-hit retained; rebuilt index matches fullscan")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="既定はread-only検査、明示optionだけ原票更新")
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    if args.write_evidence:
        capture()
    else:
        raw = validate_saved()
        print("PASS: saved observation read-only; negative=%d; no raw update" % negatives(raw))
