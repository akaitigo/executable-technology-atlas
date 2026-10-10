"""Executable finite requirement/test/evidence traceability. Not stakeholder approval."""
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
from queue_app import QueueApp

ROOT = Path(__file__).resolve().parent
CASES = ("normal", "boundary", "orphan", "stale-revision", "retested-revision", "broken-queue")
TEST_REQUIREMENTS = {"T-CAP-FILL": "R-CAP", "T-CAP-OVER": "R-CAP", "T-FIFO": "R-FIFO", "T-EMPTY": "R-EMPTY"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def requirements(capacity=3, orphan=False):
    # Synthetic requirements, not elicited or approved by real stakeholders.
    revision = {3: 1, 2: 2, 1: 3}[capacity]
    rows = [{"id": "R-CAP", "revision": revision, "statement": f"queueは{capacity}件まで受け入れ、満杯でのenqueueを拒否して内容を保持する。",
             "measure": {"capacity_items": capacity}, "required_tests": ["T-CAP-FILL", "T-CAP-OVER"]},
            {"id": "R-FIFO", "revision": 1, "statement": "受け入れたitemをenqueue順に各1回dequeueする。",
             "measure": {"ordering": "FIFO", "duplicates_created": 0}, "required_tests": ["T-FIFO"]},
            {"id": "R-EMPTY", "revision": 1, "statement": "空queueのdequeueはNoneを返し、内容を空のまま保持する。",
             "measure": {"empty_result": None, "final_items": 0}, "required_tests": ["T-EMPTY"]}]
    if orphan:
        rows.append({"id": "R-DUP", "revision": 1, "statement": "既存値と同じ値のenqueueを拒否し、内容を保持する。",
                     "measure": {"duplicate_acceptances": 0}, "required_tests": ["T-DUP"]})
    return rows


def config(capacity=3, broken=False):
    return {"capacity": capacity, "inject_overflow_bug": broken}


def bindings(cfg):
    source = sha((ROOT / "queue_app.py").read_bytes())
    return {"app_source_digest": source, "app_digest": sha(canonical({"source": source, "config": cfg})),
            "harness_digest": sha((ROOT / "runner.py").read_bytes())}


def fixture(case="normal"):
    if case not in CASES:
        raise ValueError("known finite case required")
    before_capacity = 1 if case == "boundary" else 3
    after_capacity = 2 if case in ("stale-revision", "retested-revision") else before_capacity
    broken = case == "broken-queue"
    return {"case": case, "initial_requirements": requirements(before_capacity),
            "current_requirements": requirements(after_capacity, case == "orphan"),
            "initial_config": config(before_capacity, broken), "current_config": config(after_capacity, broken),
            "retest": case == "retested-revision"}


def test_plan(test_id, capacity):
    if test_id not in TEST_REQUIREMENTS or type(capacity) is not int or not 1 <= capacity <= 3:
        raise ValueError("declared test and capacity 1..3 required")
    values = list("ABC"[:capacity])
    if test_id == "T-CAP-OVER": values.append("Z")
    ops = [{"op": "enqueue", "value": v} for v in values] if test_id != "T-EMPTY" else [{"op": "dequeue"}]
    if test_id == "T-FIFO": ops += [{"op": "dequeue"} for _ in values]
    expected = []
    # Explicit finite assertion examples, separate from QueueApp's implementation.
    for i, operation in enumerate(ops):
        if operation["op"] == "enqueue":
            before = values[:min(i, capacity)]
            accepted = i < capacity
            after = values[:min(i + 1, capacity)]
            output = accepted
        elif test_id == "T-EMPTY": before, after, output = [], [], None
        else:
            offset = i - capacity
            before, after, output = values[offset:], values[offset + 1:], values[offset]
        expected.append({"step": i, "operation": operation, "before": before, "output": output, "after": after})
    return ops, expected


def execute_test(test_id, requirement, cfg, phase):
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    ops, expected = test_plan(test_id, cfg["capacity"])
    app = QueueApp(**cfg)
    actual = []
    for i, op in enumerate(ops):
        before = app.snapshot()
        output = app.enqueue(op["value"]) if op["op"] == "enqueue" else app.dequeue()
        actual.append({"step": i, "operation": op, "before": before, "output": output, "after": app.snapshot()})
    proof = {"evidence_id": phase + ":" + test_id, "test_id": test_id, "requirement_id": requirement["id"],
             "requirement_revision": requirement["revision"], "requirement_digest": sha(canonical(requirement)),
             **bindings(cfg), "config": cfg, "operations": ops, "expected": expected, "actual": actual,
             "passed": actual == expected, "started_at": start,
             "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    proof["evidence_digest"] = sha(canonical(proof))
    return proof


def classify(reqs, proofs, current_binding):
    ids = [r["id"] for r in reqs]
    evidence_ids = [p["evidence_id"] for p in proofs]
    if len(ids) != len(set(ids)) or len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("duplicate requirement/evidence ID")
    if any(not r["required_tests"] or len(r["required_tests"]) != len(set(r["required_tests"])) for r in reqs):
        raise ValueError("nonempty unique required tests required")
    rows = []
    known = {r["id"]: set(r["required_tests"]) for r in reqs}
    unmapped = [p["evidence_id"] for p in proofs if p["requirement_id"] not in known or p["test_id"] not in known[p["requirement_id"]]]
    for req in reqs:
        checks = []
        for tid in req["required_tests"]:
            related = [p for p in proofs if p["requirement_id"] == req["id"] and p["test_id"] == tid]
            accepted, rejected = [], []
            for proof in related:
                reasons = []
                body = {k: v for k, v in proof.items() if k != "evidence_digest"}
                if proof["evidence_digest"] != sha(canonical(body)): reasons.append("evidence-digest-mismatch")
                if proof["requirement_revision"] != req["revision"]: reasons.append("requirement-revision-stale")
                if proof["requirement_digest"] != sha(canonical(req)): reasons.append("requirement-content-stale")
                if proof["app_digest"] != current_binding["app_digest"]: reasons.append("app-config-stale")
                if proof["harness_digest"] != current_binding["harness_digest"]: reasons.append("harness-stale")
                if proof["passed"] != (proof["actual"] == proof["expected"]): reasons.append("test-result-inconsistent")
                if proof["operations"] != test_plan(tid, proof["config"]["capacity"])[0]: reasons.append("test-operations-inconsistent")
                if reasons: rejected.append({"evidence_id": proof["evidence_id"], "reasons": reasons})
                else: accepted.append(proof)
            status = "missing" if not related else ("stale" if not accepted else ("passed" if all(p["passed"] for p in accepted) else "failed"))
            checks.append({"test_id": tid, "status": status, "current_evidence": [p["evidence_id"] for p in accepted], "rejected_evidence": rejected})
        states = [c["status"] for c in checks]
        status = ("verified-local" if all(s == "passed" for s in states) else ("orphan" if all(s == "missing" for s in states)
                  else ("failed" if "failed" in states else ("missing-proof" if "missing" in states else "stale"))))
        rows.append({"requirement_id": req["id"], "revision": req["revision"], "statement": req["statement"],
                     "requirement_digest": sha(canonical(req)), "status": status, "checks": checks})
    return {"rows": rows, "unmapped_evidence": unmapped, "verified": sum(r["status"] == "verified-local" for r in rows),
            "total": len(rows), "finite_checks_complete": bool(rows) and all(r["status"] == "verified-local" for r in rows) and not unmapped,
            "stakeholder_approved": False, "whole_requirements_complete": False}


def requirement_diff(before, after):
    b, a = {r["id"]: r for r in before}, {r["id"]: r for r in after}
    return {"added": [a[k] for k in sorted(a.keys() - b.keys())], "removed": [b[k] for k in sorted(b.keys() - a.keys())],
            "changed": [{"id": k, "before": b[k], "after": a[k]} for k in sorted(a.keys() & b.keys()) if a[k] != b[k]]}


def simulate(plan):
    if plan != fixture(plan.get("case")):
        raise ValueError("declared finite fixtures only")
    reqs = copy.deepcopy(plan["initial_requirements"])
    cfg = copy.deepcopy(plan["initial_config"])
    proofs, events = [], []
    diff = requirement_diff(plan["initial_requirements"], plan["current_requirements"])
    def emit(action, proof=None):
        events.append({"seq": len(events), "action": action, "requirements": copy.deepcopy(reqs), "config": copy.deepcopy(cfg),
                       "matrix": classify(reqs, proofs, bindings(cfg)), "latest_proof": copy.deepcopy(proof),
                       "evidence_ids": [p["evidence_id"] for p in proofs]})
    emit("initial-requirements")
    for tid, rid in TEST_REQUIREMENTS.items():
        proof = execute_test(tid, next(r for r in reqs if r["id"] == rid), cfg, "baseline")
        proofs.append(proof); emit("test-executed", proof)
    if diff["added"] or diff["changed"] or diff["removed"]:
        reqs, cfg = copy.deepcopy(plan["current_requirements"]), copy.deepcopy(plan["current_config"])
        emit("requirements-changed")
    if plan["retest"]:
        for tid, rid in TEST_REQUIREMENTS.items():
            proof = execute_test(tid, next(r for r in reqs if r["id"] == rid), cfg, "current")
            proofs.append(proof); emit("test-reexecuted", proof)
    emit("matrix-evaluated")
    return {"plan": plan, "plan_digest": sha(canonical(plan)), "diff": diff, "proofs": proofs, "events": events,
            "final_matrix": events[-1]["matrix"]}


def observe(case="normal", command=None):
    from oracle import check
    result = simulate(fixture(case))
    return {"input": {"case": case}, "result": result, "oracle": check(result["plan"], result, bindings(result["plan"]["current_config"])),
            "execution": {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "python": platform.python_version(),
                          "platform": platform.system() + " " + platform.machine(), "command": command or ["python3", "-B", "runner.py"],
                          "source_digest": sha((ROOT / "runner.py").read_bytes()), "synthetic_requirements": True,
                          "stakeholder_approval": False, "external_system": False}}


def publish(payload, label="run", root=ROOT / "observations", fail_before_publish=False):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex; stage, target = root / (".staging-" + token), root / (label + "-" + token); stage.mkdir()
    files = {"result.json": canonical(payload) + b"\n", "requirements.json": canonical(payload["result"]["plan"]["current_requirements"]) + b"\n",
             "proofs.json": canonical(payload["result"]["proofs"]) + b"\n", "diff.json": canonical(payload["result"]["diff"]) + b"\n"}
    for name, data in files.items():
        with (stage / name).open("xb") as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
    metadata = {"published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "artifacts": {n: {"sha256": sha(b), "bytes": len(b)} for n, b in files.items()},
                "input_digest": sha(canonical(payload["input"])), "plan_digest": payload["result"]["plan_digest"],
                "source_files": {n: sha((ROOT / n).read_bytes()) for n in ("queue_app.py", "runner.py", "oracle.py", "test_runner.py", "serve.py", "app.js", "index.html", "style.css")}}
    with (stage / "metadata.json").open("xb") as stream: stream.write(canonical(metadata) + b"\n"); stream.flush(); os.fsync(stream.fileno())
    if fail_before_publish: raise OSError("intentional staging failure; prior raw records preserved")
    stage.rename(target); return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--case", choices=CASES, default="normal"); parser.add_argument("--record", action="store_true")
    args = parser.parse_args(); report = observe(args.case, ["python3", "-B", "runner.py", *sys.argv[1:]])
    if not report["oracle"]["all_match"]: raise SystemExit("独立oracle不一致: 記録しません")
    if args.record: print("record: " + str(publish(report).relative_to(ROOT)), file=sys.stderr)
    print(json.dumps(report, ensure_ascii=False, indent=2))
