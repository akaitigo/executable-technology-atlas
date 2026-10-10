"""Read-only check by default; explicit --write publishes a complete local bundle."""
import sys
sys.dont_write_bytecode = True
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from runner import ROOT, run_lesson

EVIDENCE = ROOT / "evidence"
SOURCE_FILES = ["runner.py", "verify.py", "observe.py", "fixture.json", "hand-groups.json", "sources.json",
                "index.html", "README.md", "assets/groups-and-utility.svg", "skills/atlas-privacy-engineering/SKILL.md"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def source_digests():
    return {name: sha((ROOT / name).read_bytes()) for name in SOURCE_FILES}


def browser_data(captured, observation):
    return ("const OBSERVED = " + json.dumps({"captured_at_utc": captured, "observation": observation},
                                          ensure_ascii=False, allow_nan=False) + ";\n").encode("utf-8")


def run_checker():
    checked = subprocess.run([sys.executable, "-B", "verify.py"], cwd=ROOT, capture_output=True, text=True)
    if checked.returncode:
        raise RuntimeError("checker failed; prior evidence retained\n" + checked.stderr)
    return {"command": "python3 -B verify.py", "exit_code": checked.returncode,
            "stdout": checked.stdout, "stderr": checked.stderr}


def verify_bundle(directory):
    if {p.name for p in directory.iterdir()} != {"observation.json", "verification.json", "data.js"}:
        raise ValueError("missing/unexpected bundle member")
    raw = (directory / "observation.json").read_bytes()
    receipt = json.loads((directory / "verification.json").read_bytes())
    if raw != encoded(run_lesson()):
        raise ValueError("raw differs from actual processing")
    src = source_digests()
    if receipt["source_sha256"] != src:
        raise ValueError("stale source binding")
    if receipt["input_sha256"] != {name: src[name] for name in ("fixture.json", "hand-groups.json")}:
        raise ValueError("input binding mismatch")
    if receipt["result"] != "passed" or receipt["checker"]["exit_code"] != 0:
        raise ValueError("checker did not pass")
    if receipt["real_reidentification_performed"] or receipt["subject_completion"] != "not-claimed":
        raise ValueError("unsupported real-data/completion claim")
    if datetime.fromisoformat(receipt["captured_at_utc"]).tzinfo is None:
        raise ValueError("missing capture timezone")
    expected_js = browser_data(receipt["captured_at_utc"], json.loads(raw))
    if (directory / "data.js").read_bytes() != expected_js:
        raise ValueError("UI data differs from raw")
    if receipt["raw_sha256"] != sha(raw) or receipt["artifact_sha256"] != {
            name: sha((directory / name).read_bytes()) for name in ("observation.json", "data.js")}:
        raise ValueError("artifact digest mismatch")


def publish(checker):
    captured = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw = encoded(run_lesson())
    js = browser_data(captured, json.loads(raw))
    src = source_digests()
    receipt = {"schema_version": 1, "captured_at_utc": captured, "result": "passed",
               "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                               "system": platform.system(), "machine": platform.machine()},
               "runner_execution": "observe.py imports runner.run_lesson() in the same Python process",
               "checker": checker, "input_sha256": {name: src[name] for name in ("fixture.json", "hand-groups.json")},
               "source_sha256": src, "raw_sha256": sha(raw),
               "artifact_sha256": {"observation.json": sha(raw), "data.js": sha(js)},
               "real_reidentification_performed": False, "network_used": False,
               "dataset": "fictional only; not real-data synthetic-model sampling", "subject_completion": "not-claimed"}
    with tempfile.TemporaryDirectory(prefix=".capture-", dir=ROOT) as temp:
        staging, previous = Path(temp) / "next", Path(temp) / "previous"
        staging.mkdir()
        (staging / "observation.json").write_bytes(raw)
        (staging / "data.js").write_bytes(js)
        (staging / "verification.json").write_bytes(encoded(receipt))
        verify_bundle(staging)
        had_previous = EVIDENCE.exists()
        if had_previous:
            os.rename(EVIDENCE, previous)
        try:
            os.rename(staging, EVIDENCE)
        except BaseException:
            if had_previous:
                os.rename(previous, EVIDENCE)
            raise
        if had_previous:
            shutil.rmtree(previous)  # only this generated bundle's superseded snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    checked = run_checker()
    if args.write:
        publish(checked)
    else:
        verify_bundle(EVIDENCE)
    print("Privacy lesson: " + ("published" if args.write else "checked") + "; hand groups/raw/source/browser binding match")
