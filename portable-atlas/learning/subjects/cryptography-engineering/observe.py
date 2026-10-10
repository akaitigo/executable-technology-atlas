"""Check read-only by default. Explicit --write updates an atomic local bundle."""
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
import ssl
import subprocess
import tempfile
from runner import ROOT, run_lesson

EVIDENCE = ROOT / "evidence"
SOURCES = ["runner.py", "verify.py", "observe.py", "fixture.json", "oracle.json", "sources.json",
           "index.html", "README.md", "assets/mac-and-memory.svg", "skills/atlas-cryptography-engineering/SKILL.md"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def source_digests():
    return {name: digest((ROOT / name).read_bytes()) for name in SOURCES}


def check_calculator():
    result = subprocess.run([sys.executable, "-B", "verify.py"], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("checker failed; prior successful evidence unchanged\n" + result.stderr)
    # Unittest's elapsed duration is raw execution context, not a timing security test.
    return {"command": "python3 -B verify.py", "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def js_bytes(captured_at, observation):
    return ("const OBSERVED = " + json.dumps({"captured_at_utc": captured_at, "observation": observation},
                                          ensure_ascii=False, allow_nan=False) + ";\n").encode("utf-8")


def verify_bundle(directory):
    if {p.name for p in directory.iterdir()} != {"observation.json", "verification.json", "data.js"}:
        raise ValueError("unexpected or missing evidence member")
    raw = (directory / "observation.json").read_bytes()
    observation = json.loads(raw)
    receipt = json.loads((directory / "verification.json").read_bytes())
    if raw != encode(run_lesson()):
        raise ValueError("raw observation differs from actual calculator")
    if receipt["source_sha256"] != source_digests():
        raise ValueError("source/input binding stale")
    if receipt["input_sha256"] != {name: source_digests()[name] for name in ("fixture.json", "oracle.json")}:
        raise ValueError("input binding mismatch")
    if receipt["checker"]["exit_code"] != 0 or receipt["result"] != "passed":
        raise ValueError("checker did not pass")
    if receipt["timing_security_test"] or receipt["subject_completion"] != "not-claimed":
        raise ValueError("unsupported security/completion claim")
    stamp = datetime.fromisoformat(receipt["captured_at_utc"])
    if stamp.tzinfo is None:
        raise ValueError("capture timestamp must include timezone")
    expected_js = js_bytes(receipt["captured_at_utc"], observation)
    if (directory / "data.js").read_bytes() != expected_js:
        raise ValueError("browser data differs from raw")
    actual_outputs = {name: digest((directory / name).read_bytes()) for name in ("observation.json", "data.js")}
    if receipt["artifact_sha256"] != actual_outputs or receipt["raw_sha256"] != digest(raw):
        raise ValueError("artifact digest mismatch")


def write_bundle(checker):
    captured = datetime.now(timezone.utc).isoformat(timespec="seconds")
    raw = encode(run_lesson())
    js = js_bytes(captured, json.loads(raw))
    src = source_digests()
    receipt = {"schema_version": 1, "captured_at_utc": captured, "result": "passed",
               "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                               "system": platform.system(), "machine": platform.machine(), "openssl": ssl.OPENSSL_VERSION},
               "runner_execution": "observe.py imports and calls runner.run_lesson() in the same Python process", "checker": checker,
               "input_sha256": {name: src[name] for name in ("fixture.json", "oracle.json")},
               "source_sha256": src, "raw_sha256": digest(raw),
               "artifact_sha256": {"observation.json": digest(raw), "data.js": digest(js)},
               "key_material": "public synthetic test keys only", "timing_security_test": False,
               "network_used": False, "production_keys_changed": False, "subject_completion": "not-claimed"}
    # All files generated and validated before publication. No partial member overwrite.
    with tempfile.TemporaryDirectory(prefix=".capture-", dir=ROOT) as temp:
        staging = Path(temp) / "next"
        previous = Path(temp) / "previous"
        staging.mkdir()
        (staging / "observation.json").write_bytes(raw)
        (staging / "data.js").write_bytes(js)
        (staging / "verification.json").write_bytes(encode(receipt))
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
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    checker = check_calculator()
    if args.write:
        write_bundle(checker)
    else:
        verify_bundle(EVIDENCE)
    print("HMAC lesson evidence: " + ("published" if args.write else "checked") + "; raw/oracle/source/browser binding match")
