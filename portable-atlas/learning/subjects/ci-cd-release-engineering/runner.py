"""Finite synthetic local release pipeline, not a CI/deploy integration."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid

ROOT = Path(__file__).resolve().parent
CASES = ("normal", "test-swap", "promotion-swap", "failed-test", "missing-history")
POLICY = {"format": "atlas-synthetic-v1", "release": "integer 1..3", "ready": True}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def artifact(release=2, ready=True):
    return b"ATLAS-SYNTHETIC\x00" + canonical({"format": "atlas-synthetic-v1", "release": release, "ready": ready}) + b"\n"


def inspect_artifact(blob):
    checks = {"header": blob.startswith(b"ATLAS-SYNTHETIC\x00"), "schema": False, "ready": False}
    try:
        value = json.loads(blob.split(b"\x00", 1)[1])
        checks["schema"] = (set(value) == {"format", "release", "ready"} and value["format"] == POLICY["format"]
                            and type(value["release"]) is int and 1 <= value["release"] <= 3
                            and type(value["ready"]) is bool)
        checks["ready"] = value.get("ready") is True
    except (ValueError, IndexError, TypeError, AttributeError):
        pass
    return {"artifact_digest": sha(blob), "policy_digest": sha(canonical(POLICY)),
            "checks": checks, "passed": all(checks.values())}


class ImmutableStore:
    """Append-only bytes keyed by SHA-256; never rebuild old release."""
    def __init__(self):
        self._objects = {}

    def put(self, blob):
        if type(blob) is not bytes:
            raise ValueError("immutable bytes only")
        key = sha(blob)
        if key in self._objects and self._objects[key] != blob:
            raise ValueError("digest collision")
        self._objects.setdefault(key, blob)
        return key

    def get(self, key):
        blob = self._objects[key]
        if sha(blob) != key:
            raise ValueError("stored bytes do not match key")
        return blob

    def snapshot(self):
        return {k: {"bytes": len(v), "hex": v.hex()} for k, v in sorted(self._objects.items())}


def fixture(case="normal", rollback=True):
    if case not in CASES or type(rollback) is not bool:
        raise ValueError("known case and boolean rollback required")
    return {"case": case, "rollback": rollback, "previous_hex": None if case == "missing-history" else artifact(1).hex(),
            "build_hex": artifact(2, ready=case != "failed-test").hex(), "replacement_hex": artifact(3).hex()}


def simulate(plan):
    plan = copy.deepcopy(plan)
    if set(plan) != {"case", "rollback", "previous_hex", "build_hex", "replacement_hex"}:
        raise ValueError("unknown or missing plan field")
    if plan != fixture(plan["case"], plan["rollback"]):
        raise ValueError("this finite lesson accepts only its declared fixture bytes")
    store = ImmutableStore()
    active = store.put(bytes.fromhex(plan["previous_hex"])) if plan["previous_hex"] is not None else None
    original_active = active
    original_objects = store.snapshot()
    previous = None
    working = bytes.fromhex(plan["build_hex"])
    test = None
    candidate = None
    events = []

    def emit(stage, status, reason, guards=None):
        events.append({"seq": len(events), "stage": stage, "status": status, "reason": reason,
                       "guards": guards or {}, "working_digest": sha(working), "working_hex": working.hex(),
                       "test": copy.deepcopy(test), "candidate": copy.deepcopy(candidate),
                       "active": active, "previous": previous, "objects": store.snapshot()})

    emit("build", "ok", "synthetic bytes generated; initial active is not rebuilt")
    test = inspect_artifact(working)
    emit("test", "passed" if test["passed"] else "failed", "header/schema/ready checks on actual bytes")
    if plan["case"] == "test-swap":
        working = bytes.fromhex(plan["replacement_hex"])
        emit("substitution", "injected", "test-to-candidate bytes changed; old test record retained")
    guards = {"test_passed": test["passed"], "test_digest_matches": sha(working) == test["artifact_digest"]}
    if not all(guards.values()):
        emit("candidate", "refused", "failed-test" if not test["passed"] else "test-artifact-mismatch", guards)
    else:
        key = store.put(working)
        candidate = {"artifact_digest": key, "test_record_digest": sha(canonical(test))}
        emit("candidate", "accepted", "tested immutable bytes stored under digest", guards)
        if plan["case"] == "promotion-swap":
            working = bytes.fromhex(plan["replacement_hex"])
            emit("substitution", "injected", "candidate-to-promotion bytes changed; candidate retained")
        guards = {"test_passed": test["passed"], "workspace_matches": sha(working) == candidate["artifact_digest"],
                  "test_digest_matches": test["artifact_digest"] == candidate["artifact_digest"],
                  "test_record_matches": sha(canonical(test)) == candidate["test_record_digest"],
                  "stored_bytes_match": sha(store.get(key)) == candidate["artifact_digest"]}
        if not all(guards.values()):
            emit("promotion", "refused", "promotion-binding-mismatch", guards)
        else:
            previous, active = active, key
            emit("promotion", "promoted", "active pointer now selects the tested digest", guards)
    if plan["rollback"]:
        promoted = any(e["stage"] == "promotion" and e["status"] == "promoted" for e in events)
        if not promoted:
            emit("rollback", "not-attempted", "no promotion; active remains unchanged")
        elif previous is None:
            emit("rollback", "refused", "missing-history; no fallback build or invented previous release")
        else:
            active = previous
            store.get(active)  # verify existing immutable bytes before selecting
            emit("rollback", "rolled-back", "previous digest selected; no rebuild or deletion", {"stored_bytes_match": True})
    else:
        emit("rollback", "not-requested", "explicit rollback=false")
    final = events[-1]
    return {"plan": plan, "plan_digest": sha(canonical(plan)), "events": events, "final": final,
            "summary": {"test_passed": test["passed"], "candidate_accepted": candidate is not None,
                        "promoted": any(e["status"] == "promoted" for e in events),
                        "rollback_status": final["status"], "active": active, "original_active": original_active,
                        "previous_bytes_unchanged": all(store.snapshot().get(k) == v for k, v in original_objects.items()),
                        "history_present_initially": bool(original_objects), "trace_events": len(events)}}


def observe(case="normal", rollback=True, command=None):
    from oracle import check
    result = simulate(fixture(case, rollback))
    return {"input": {"case": case, "rollback": rollback}, "result": result,
            "oracle": check(result["plan"], result),
            "execution": {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          "python": platform.python_version(), "platform": platform.system() + " " + platform.machine(),
                          "command": command or ["python3", "-B", "runner.py"], "source_digest": sha((ROOT / "runner.py").read_bytes()),
                          "synthetic_local_state": True, "external_ci": False, "deployed": False}}


def publish(payload, label="run", root=ROOT / "observations", fail_before_publish=False):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    stage, target = root / (".staging-" + token), root / (label + "-" + token)
    stage.mkdir()
    # Keep actual synthetic artifact bytes beside their lifecycle, not just digest labels.
    files = {"result.json": canonical(payload) + b"\n"}
    for name, value in payload["result"]["plan"].items():
        if name.endswith("_hex") and value is not None:
            files[name[:-4] + ".bin"] = bytes.fromhex(value)
    for name, data in files.items():
        with (stage / name).open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
    metadata = {"published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "artifacts": {n: {"sha256": sha(b), "bytes": len(b)} for n, b in files.items()},
                "input_digest": sha(canonical(payload["input"])), "plan_digest": payload["result"]["plan_digest"],
                "source_files": {n: sha((ROOT / n).read_bytes()) for n in ("runner.py", "oracle.py", "test_runner.py", "serve.py", "app.js", "index.html", "style.css")}}
    with (stage / "metadata.json").open("xb") as stream:
        stream.write(canonical(metadata) + b"\n"); stream.flush(); os.fsync(stream.fileno())
    if fail_before_publish:
        raise OSError("intentional staging failure; old records preserved")
    stage.rename(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="normal")
    parser.add_argument("--no-rollback", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    payload = observe(args.case, not args.no_rollback, ["python3", "-B", "runner.py", *sys.argv[1:]])
    if args.record:
        print("record: " + str(publish(payload).relative_to(ROOT)), file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
