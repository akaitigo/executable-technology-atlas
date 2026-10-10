"""Record actual executions of the finite model against task-owned JSON files."""
import copy
import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from model import canonical, reconcile

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot(count, revision=4):
    return {"revision": revision, "pods": [{"id": "pod-" + str(i), "node": "node-a" if i % 2 else "node-b"} for i in range(1, count + 1)]}


def main(token):
    if not re.fullmatch(r"[0-9TZ]+-scheduler", token):
        raise ValueError("invalid run token")
    start = now()
    folder = ROOT / "observations" / token
    folder.mkdir(parents=True, exist_ok=False)
    health = {"node-a": True, "node-b": True}
    lost = {"node-a": False, "node-b": True}
    recovered = {"revision": 5, "pods": [{"id": "pod-" + str(i), "node": None if i % 2 else "node-b"} for i in range(1, 5)]}
    cases = [
        ("create", 2, snapshot(0), health, False),
        ("scale-up", 4, snapshot(2), health, False),
        ("scale-down", 1, snapshot(4), health, False),
        ("node-failure-fit", 2, snapshot(2), lost, False),
        ("node-failure-pending", 4, snapshot(4), lost, False),
        ("node-recovery", 4, recovered, health, False),
        ("over-capacity", 5, snapshot(0), health, False),
        ("both-down", 2, snapshot(2), {"node-a": False, "node-b": False}, False),
        ("zero", 0, snapshot(2), health, False),
        ("stale-revision", 2, snapshot(2), health, False),
        ("invalid-negative", -1, snapshot(2), health, False),
        ("invalid-bool", True, snapshot(2), health, False),
        ("unknown-node", 2, snapshot(2), {"node-a": True, "node-x": True}, False),
        ("duplicate-pod", 2, {"revision": 4, "pods": [snapshot(1)["pods"][0]] * 2}, health, False),
        ("bad-over-capacity", 5, snapshot(0), health, True),
        ("bad-failure", 4, snapshot(4), lost, True),
    ]
    rows = []
    for ident, desired, state, node_health, bad in cases:
        row_folder = folder / ident
        row_folder.mkdir()
        request = {"desired_replicas": desired, "health": copy.deepcopy(node_health), "expected_revision": state["revision"] - int(ident == "stale-revision")}
        inputs = {"request": request, "state": state, "implementation": "bad-ignore-capacity" if bad else "capacity-aware", "capacity": {"node-a": 2, "node-b": 2}}
        (row_folder / "input.json").write_bytes(canonical(inputs))
        actual = json.loads((row_folder / "input.json").read_bytes())
        result = reconcile(actual["request"], actual["state"], bad)
        (row_folder / "result.json").write_bytes(canonical(result))
        (row_folder / "after-state.json").write_bytes(canonical(result["state"]))
        (row_folder / "events.json").write_bytes(canonical(result["events"]))
        second = None
        if not bad and result["outcome"] != "blocked":
            next_request = {**request, "expected_revision": result["state"]["revision"]}
            second = reconcile(next_request, result["state"])
            assert second["state"] == result["state"] and not second["changed"]
            (row_folder / "second-input.json").write_bytes(canonical({"request": next_request, "state": result["state"]}))
            (row_folder / "second-result.json").write_bytes(canonical(second))
        if result["outcome"] == "blocked":
            assert result["state"] == state and result["pre_digest"] == result["post_digest"]
        assert json.loads((row_folder / "input.json").read_bytes()) == inputs
        rows.append({"id": ident, "observed_at": now(), "input": actual, "result": result, "second": second})
    sources = {f: "sha256:" + hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ("model.py", "experiment.py")}
    observation = {"schema_version": 1, "field_id": "container-orchestration", "lesson_id": "two-node-scheduler",
                   "execution_id": token, "started_at": start, "completed_at": now(), "source_bindings": sources,
                   "runtime": {"python": platform.python_version(), "os": platform.system(), "release": platform.release(), "machine": platform.machine()},
                   "attempts": 1, "retries": 0, "real_kubernetes_executed": False, "containers_started": 0,
                   "external_mutations": 0, "subject_complete": False, "scenarios": rows}
    (folder / "observation.json").write_bytes(canonical(observation))
    print(json.dumps(observation, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main(sys.argv[1])
