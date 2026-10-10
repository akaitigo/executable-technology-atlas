#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute the checker, then publish a single consistent observation generation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

from evaluate import ROOT, observation

EVIDENCE = ROOT / "evidence"
SOURCES = ("evaluate.py", "verify.py", "observe.py", "predictions.json", "hand-count.json", "sources.json")


def render(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def browser_data(observed, captured_at):
    value = {"captured_at_utc": captured_at, "observation": observed}
    return ("const OBSERVED = " + json.dumps(value, ensure_ascii=False, allow_nan=False) + ";\n").encode()


def run_checker():
    return subprocess.run(
        [sys.executable, "verify.py"], cwd=ROOT,
        text=True, capture_output=True, check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def write_bundle(observed, checker):
    captured_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    outputs = {"observation.json": render(observed), "data.js": browser_data(observed, captured_at)}
    record = {
        "schema_version": 1,
        "record_type": "synthetic-binary-evaluation-observation",
        "captured_at_utc": captured_at,
        "execution": {
            "runtime": "python-stdlib", "python": platform.python_version(),
            "os": platform.system().lower(), "architecture": platform.machine(),
            "runner": "python3 observe.py --write", "checker": "python3 verify.py",
            "checker_exit_code": checker.returncode,
            "checker_stdout": checker.stdout, "checker_stderr": checker.stderr,
            "network_access": False, "external_model_used": False,
            "training_performed": False, "docker_used": False,
        },
        "source_binding": {name: digest((ROOT / name).read_bytes()) for name in SOURCES},
        "outputs": {name: digest(data) for name, data in outputs.items()},
        "publication": "staging-directory-rename-with-rollback",
        "scope": "metrics for a fixed authored binary-prediction fixture",
        "subject_completion": "not-claimed",
        "result": "passed",
    }
    outputs["verification.json"] = render(record)
    with tempfile.TemporaryDirectory(prefix="ai-eval-observation-", dir=ROOT) as temp_name:
        temp = Path(temp_name)
        staging = temp / "evidence"
        staging.mkdir()
        for name, data in outputs.items():
            (staging / name).write_bytes(data)
        verify_bundle(staging, observed)
        previous = temp / "previous"
        if EVIDENCE.is_symlink():
            raise ValueError("evidence directory cannot be a symlink")
        if EVIDENCE.exists():
            os.replace(EVIDENCE, previous)
        try:
            os.replace(staging, EVIDENCE)
        except BaseException:
            if previous.exists():
                os.replace(previous, EVIDENCE)
            raise


def verify_bundle(directory, observed):
    if {p.name for p in directory.iterdir()} != {"observation.json", "data.js", "verification.json"}:
        raise ValueError("observation bundle file set mismatch")
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError("observation bundle requires regular files")
    if (directory / "observation.json").read_bytes() != render(observed):
        raise ValueError("observation differs from current execution")
    record = json.loads((directory / "verification.json").read_text())
    for name in SOURCES:
        if record["source_binding"].get(name) != digest((ROOT / name).read_bytes()):
            raise ValueError(f"stale source: {name}")
    for name in ("observation.json", "data.js"):
        if record["outputs"].get(name) != digest((directory / name).read_bytes()):
            raise ValueError(f"output digest mismatch: {name}")
    if (directory / "data.js").read_bytes() != browser_data(observed, record["captured_at_utc"]):
        raise ValueError("browser data differs from observed Python output")
    if record["result"] != "passed" or record["execution"]["checker_exit_code"] != 0:
        raise ValueError("checker success is missing")
    if record["subject_completion"] != "not-claimed":
        raise ValueError("subject completion is outside this lesson")
    for name in ("network_access", "external_model_used", "training_performed", "docker_used"):
        if record["execution"].get(name) is not False:
            raise ValueError(f"unexpected execution claim: {name}")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    checker = run_checker()
    observed = observation()
    if args.write:
        write_bundle(observed, checker)
        print("AI evaluation observation: written after independent checker pass")
    else:
        verify_bundle(EVIDENCE, observed)
        print("AI evaluation observation: checked; fixture/oracle/source/browser data match")


if __name__ == "__main__":
    main()
