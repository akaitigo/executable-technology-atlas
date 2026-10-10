#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Lightweight publication/freshness tests; never changes canonical evidence."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from observe import publish
from verify import HERE, INPUTS, digest, validate_saved


def evidence_state():
    return {p.name: (digest(p.read_bytes()), p.stat().st_mtime_ns) for p in (HERE / "evidence").iterdir()}


before = evidence_state()
for command in ("verify.py", "observe.py"):
    subprocess.run([sys.executable, "-B", command], cwd=HERE, check=True)
assert evidence_state() == before, "read-only command altered evidence"

with tempfile.TemporaryDirectory(prefix=".contract-", dir=HERE) as directory:
    root = Path(directory)
    for label in ("artifact-tamper", "artifact-missing", "source-tamper"):
        candidate = root / label
        candidate.mkdir()
        shutil.copytree(HERE / "evidence", candidate / "evidence")
        for name in INPUTS:
            (candidate / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(HERE / name, candidate / name)
        if label == "artifact-tamper":
            with (candidate / "evidence/stdout.json").open("ab") as handle:
                handle.write(b" ")
        elif label == "artifact-missing":
            (candidate / "evidence/verification.json").unlink()
        else:
            with (candidate / "indexer.py").open("ab") as handle:
                handle.write(b"\n# mutation\n")
        try:
            validate_saved(candidate)
        except (AssertionError, FileNotFoundError):
            pass
        else:
            raise AssertionError("accepted " + label)

    live, candidate = root / "live", root / "next"
    live.mkdir()
    candidate.mkdir()
    (live / "result").write_bytes(b"prior-success")
    (candidate / "result").write_bytes(b"new-success")
    previous = digest((live / "result").read_bytes())
    original = os.replace

    def fail_swap(source, destination):
        if Path(source) == candidate:
            raise OSError("injected swap failure")
        return original(source, destination)

    try:
        with patch("observe.os.replace", side_effect=fail_swap):
            publish(candidate, live)
    except OSError:
        pass
    else:
        raise AssertionError("swap failure swallowed")
    assert digest((live / "result").read_bytes()) == previous and candidate.exists()
    publish(candidate, live)
    assert (live / "result").read_bytes() == b"new-success" and not candidate.exists()

raw = validate_saved()
# Author routing walkthrough, not an independent Agent Eval.
assert raw["queries"][0]["doc_ids"] == ["d1"]
assert raw["queries"][1]["doc_ids"] == ["d1", "d2", "d3", "d4"]
assert all(raw["scope"][field] is False for field in ("bm25", "semantic_embedding", "product_engine", "performance_benchmark"))
assert evidence_state() == before
print("PASS: read-only bytes+mtime; tamper/missing/source rejection; atomic rollback; normal/unsupported Skill routing walkthrough")
