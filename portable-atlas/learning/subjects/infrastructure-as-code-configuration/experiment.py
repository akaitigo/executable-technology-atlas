import copy
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from simulator import SCOPE, apply_plan, digest, encoded, make_plan

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def execute(token):
    started = now()
    out = ROOT / "observations" / token
    out.mkdir(parents=True, exist_ok=False)
    baseline = {"scope": SCOPE, "revision": 7, "resources": {
        "service.web": {"replicas": 2, "port": 8080, "enabled": True},
        "config.banner": {"text": "hello"}}}
    declarations = {"scope": SCOPE, "resources": copy.deepcopy(baseline["resources"])}
    cases = [
        ("noop", "noop", None), ("reconcile", "applied", None), ("drift", "applied", None),
        ("stale-revision", "blocked", "stale-revision"),
        ("silent-drift", "blocked", "stale-observed-hash"),
        ("delete-blocked", "blocked", "delete-approval-required"),
        ("delete-approved", "applied", None), ("wrong-approval", "blocked", "delete-approval-required"),
        ("unknown-value", "blocked", "unknown-value"),
        ("unsupported-attribute", "blocked", "unsupported-attribute"),
        ("tampered-plan", "blocked", "plan-digest-mismatch"),
        ("desired-changed", "blocked", "desired-changed")]
    rows = []
    for ident, expected_status, expected_reason in cases:
        folder = out / ident
        folder.mkdir()
        desired, observed = copy.deepcopy(declarations), copy.deepcopy(baseline)
        if ident == "reconcile":
            desired["resources"]["service.web"]["replicas"] = 3
            desired["resources"]["config.extra"] = {"text": "created"}
        drift_events = []
        if ident == "drift":
            observed["resources"]["service.web"]["replicas"] = 1
            observed["revision"] = 8
            drift_events.append({"event": "out-of-band-synthetic-edit", "revision": 8, "id": "service.web", "replicas": 1})
        if ident.startswith("delete-") or ident == "wrong-approval":
            del desired["resources"]["service.web"]
        if ident == "unknown-value":
            desired["resources"]["service.web"]["replicas"] = None
        if ident == "unsupported-attribute":
            desired["resources"]["service.web"]["extra"] = "unknown"
        if ident in ("stale-revision", "silent-drift", "tampered-plan", "desired-changed"):
            desired["resources"]["service.web"]["replicas"] = 3
        def save(name, value):
            (folder / name).write_bytes(encoded(value))
        def read(name):
            return json.loads((folder / name).read_bytes())
        save("observed-baseline.json", baseline)
        save("desired-planning.json", desired)
        save("observed-planning.json", observed)
        plan = make_plan(read("desired-planning.json"), read("observed-planning.json"))
        save("plan-created.json", plan)
        trusted_plan = digest(read("plan-created.json"))  # held before bundle mutations
        current = copy.deepcopy(observed)
        current_desired = copy.deepcopy(desired)
        if ident == "stale-revision":
            current["revision"] += 1
            drift_events.append({"event": "post-plan-revision-edit", "revision": current["revision"]})
        if ident == "silent-drift":
            current["resources"]["service.web"]["replicas"] = 5
            drift_events.append({"event": "post-plan-content-edit-without-revision", "revision": current["revision"]})
        if ident == "desired-changed":
            current_desired["resources"]["service.web"]["replicas"] = 4
        if ident == "tampered-plan":
            plan["actions"][0]["after"]["replicas"] = 4
        approval = None
        if ident == "delete-approved":
            approval = {"plan_digest": trusted_plan, "delete_ids": ["service.web"]}
        if ident == "wrong-approval":
            approval = {"plan_digest": "sha256:" + "0" * 64, "delete_ids": ["service.web"]}
        save("desired-applying.json", current_desired)
        save("observed-current.json", current)
        save("plan-supplied.json", plan)
        save("approval.json", approval)
        save("trusted-plan-pin.json", {"digest": trusted_plan, "trust_model": "consumer process retains created plan digest before mutations"})
        before_bytes = (folder / "observed-current.json").read_bytes()
        applied = apply_plan(read("plan-supplied.json"), read("desired-applying.json"), read("observed-current.json"), trusted_plan, read("approval.json"))
        save("apply-result.json", applied)
        save("synthetic-store-after.json", applied["state"])
        assert (folder / "observed-current.json").read_bytes() == before_bytes
        assert applied["status"] == expected_status and applied["reason"] == expected_reason, (ident, applied)
        next_plan, again = None, None
        if applied["status"] != "blocked":
            next_plan = make_plan(read("desired-applying.json"), read("synthetic-store-after.json"))
            again = apply_plan(next_plan, read("desired-applying.json"), read("synthetic-store-after.json"), digest(next_plan))
            assert next_plan["actions"] == [] and again["status"] == "noop"
            assert again["state"] == applied["state"]
            save("replan.json", next_plan)
            save("reapply-result.json", again)
        else:
            assert (folder / "synthetic-store-after.json").read_bytes() == before_bytes
        row = {"id": ident, "observed_at": now(), "baseline": baseline, "desired_planning": desired,
               "observed_planning": observed, "desired_applying": current_desired, "observed_current": current,
               "plan_created": read("plan-created.json"), "plan_supplied": read("plan-supplied.json"),
               "trusted_plan_digest": trusted_plan, "approval": approval, "drift_events": drift_events,
               "result": applied, "replan": next_plan, "reapply": again,
               "expected": {"status": expected_status, "reason": expected_reason}}
        save("observation.json", row)
        rows.append(row)
    observation = {"schema_version": 1, "field_id": "infrastructure-as-code-configuration",
                   "lesson_id": "diff-plan-apply-subset", "execution_id": token, "started_at": started, "completed_at": now(),
                   "runtime": {"python": platform.python_version(), "os": platform.system(), "release": platform.release(),
                               "machine": platform.machine(), "attempts": 1, "retries": 0},
                   "source_bindings": {name: "sha256:" + __import__("hashlib").sha256((ROOT / name).read_bytes()).hexdigest()
                                       for name in ("simulator.py", "experiment.py")},
                   "scenarios": rows, "scope": {"synthetic_state_only": True, "external_infrastructure_changed": False,
                   "terraform_executed": False, "distributed_lock_tested": False, "subject_complete": False}}
    (out / "observation.json").write_bytes(encoded(observation))
    print(json.dumps(observation, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    token = sys.argv[1]
    if not re.fullmatch(r"[0-9TZ]+-iac", token):
        raise SystemExit("invalid token")
    execute(token)
