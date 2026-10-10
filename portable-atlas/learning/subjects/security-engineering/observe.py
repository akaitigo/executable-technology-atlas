"""Check read-only by default; --write explicitly updates the whole evidence bundle."""
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
SOURCE_FILES = ["runner.py", "verify.py", "observe.py", "fixture.json", "oracle.json", "sources.json", "README.md",
                "index.html", "assets/trust-and-control.svg", "skills/atlas-security-engineering/SKILL.md"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def source_digests():
    return {name: sha((ROOT / name).read_bytes()) for name in SOURCE_FILES}


def js_data(captured, observation):
    return ("const OBSERVED = " + json.dumps({"captured_at_utc": captured, "observation": observation},
                                          ensure_ascii=False, allow_nan=False) + ";\n").encode("utf-8")


def checker():
    run = subprocess.run([sys.executable, "-B", "verify.py"], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError("checker failed; prior evidence retained\n" + run.stderr)
    return {"command":"python3 -B verify.py", "exit_code":run.returncode, "stdout":run.stdout, "stderr":run.stderr}


def verify_bundle(directory):
    if {p.name for p in directory.iterdir()} != {"observation.json", "verification.json", "data.js"}:
        raise ValueError("missing or unexpected bundle member")
    raw = (directory / "observation.json").read_bytes()
    receipt = json.loads((directory / "verification.json").read_bytes())
    if raw != encoded(run_lesson()):
        raise ValueError("raw differs from actual handler execution")
    src = source_digests()
    if receipt["source_sha256"] != src or receipt["input_sha256"] != {n:src[n] for n in ("fixture.json","oracle.json")}:
        raise ValueError("stale source/input binding")
    if receipt["checker"]["exit_code"] != 0 or receipt["result"] != "passed":
        raise ValueError("checker did not pass")
    if receipt["external_attack_performed"] or receipt["subject_completion"] != "not-claimed":
        raise ValueError("unsupported execution/completion claim")
    if datetime.fromisoformat(receipt["captured_at_utc"]).tzinfo is None:
        raise ValueError("capture timezone missing")
    if (directory / "data.js").read_bytes() != js_data(receipt["captured_at_utc"], json.loads(raw)):
        raise ValueError("UI differs from raw")
    if receipt["raw_sha256"] != sha(raw) or receipt["artifact_sha256"] != {
            name:sha((directory / name).read_bytes()) for name in ("observation.json","data.js")}:
        raise ValueError("artifact digest mismatch")


def publish(checked):
    captured = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw = encoded(run_lesson())
    js = js_data(captured, json.loads(raw))
    src = source_digests()
    receipt = {"schema_version":1, "captured_at_utc":captured, "result":"passed",
               "environment":{"python":platform.python_version(), "implementation":platform.python_implementation(),
                              "system":platform.system(), "machine":platform.machine()},
               "runner_execution":"observe.py imports runner.run_lesson() in the same process; pure synthetic handler calls",
               "checker":checked, "input_sha256":{n:src[n] for n in ("fixture.json","oracle.json")},
               "source_sha256":src, "raw_sha256":sha(raw),
               "artifact_sha256":{"observation.json":sha(raw),"data.js":sha(js)},
               "network_used":False, "external_attack_performed":False, "authentication_implemented":False,
               "subject_completion":"not-claimed"}
    with tempfile.TemporaryDirectory(prefix=".capture-", dir=ROOT) as temp:
        staging, previous = Path(temp)/"next", Path(temp)/"previous"
        staging.mkdir()
        (staging/"observation.json").write_bytes(raw)
        (staging/"data.js").write_bytes(js)
        (staging/"verification.json").write_bytes(encoded(receipt))
        verify_bundle(staging)
        existed = EVIDENCE.exists()
        if existed:
            os.rename(EVIDENCE, previous)
        try:
            os.rename(staging, EVIDENCE)
        except BaseException:
            if existed:
                os.rename(previous, EVIDENCE)
            raise
        if existed:
            shutil.rmtree(previous)  # only the superseded generated bundle's temporary snapshot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    checked = checker()
    if args.write:
        publish(checked)
    else:
        verify_bundle(EVIDENCE)
    print("Security lesson: " + ("published" if args.write else "checked") + "; actual handlers/oracle/raw/source/UI bindings match")
