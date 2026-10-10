#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Atomically write or verify the local authorization observation bundle."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

from model import run_scenarios


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
EVIDENCE = ROOT / "evidence"
SOURCE_PATHS = ("model.py", "observe.py", "verify.py", "sources.json")


def render(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def verification(observation: dict) -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, check=True).stdout.strip()
    return {
        "schema_version": 1,
        "record_type": "identity-authorization-learning-verification",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "execution": {
            "runtime": "python-stdlib",
            "python": platform.python_version(),
            "os": platform.system().lower(),
            "architecture": platform.machine(),
            "docker_used": False,
            "network_access": False,
            "external_identity_provider": False,
        },
        "source_binding": {
            "git_head": head,
            "files": {path: digest((ROOT / path).read_bytes()) for path in SOURCE_PATHS},
        },
        "observation": {"path": "evidence/observation.json", "digest": digest(render(observation))},
        "scope": "fixed local authorization policy: exact scope, role inheritance and permission grant revocation",
        "not_claimed": ["authentication implementation", "OAuth", "OIDC", "login", "WebAuthn", "complete RBAC", "ABAC", "ReBAC", "capability authorization"],
        "result": "passed",
    }


def write_bundle(observation: dict) -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="authorization-observation-", dir=ROOT) as temp_name:
        temp = Path(temp_name)
        check = verification(observation)
        (temp / "observation.json").write_bytes(render(observation))
        (temp / "verification.json").write_bytes(render(check))
        os.replace(temp / "observation.json", EVIDENCE / "observation.json")
        os.replace(temp / "verification.json", EVIDENCE / "verification.json")


def check_bundle(observation: dict) -> None:
    stored = json.loads((EVIDENCE / "observation.json").read_text(encoding="utf-8"))
    check = json.loads((EVIDENCE / "verification.json").read_text(encoding="utf-8"))
    if stored != observation:
        raise ValueError("observation.json is stale")
    if check.get("observation", {}).get("digest") != digest(render(observation)):
        raise ValueError("observation digest mismatch")
    if check.get("result") != "passed":
        raise ValueError("verification result is not passed")
    for path in SOURCE_PATHS:
        if check.get("source_binding", {}).get("files", {}).get(path) != digest((ROOT / path).read_bytes()):
            raise ValueError(f"source digest mismatch: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    observation = run_scenarios()
    if not all(observation["assertions"].values()):
        raise ValueError("one or more authorization assertions failed")
    if args.write:
        write_bundle(observation)
        print("authorization observation: written")
    else:
        check_bundle(observation)
        print("authorization observation: verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
