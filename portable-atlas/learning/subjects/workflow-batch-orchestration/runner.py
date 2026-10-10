"""Finite sequential DAG teaching runner. Pure synthetic tasks; no worker/network."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import uuid

ROOT = Path(__file__).resolve().parent
CASES = ("normal", "fail-once", "always-fail", "cycle")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_digest():
    return hashlib.sha256((ROOT / "runner.py").read_bytes()).hexdigest()


def fixture(case="normal", retries=1, seed=2):
    if case not in CASES:
        raise ValueError("unknown case")
    if type(retries) is not int or not 0 <= retries <= 2:
        raise ValueError("retries must be integer 0..2")
    if type(seed) is not int or not 1 <= seed <= 9:
        raise ValueError("seed must be integer 1..9")
    plan = {"seed": seed, "retries": retries, "tasks": {
        "A": {"deps": [], "op": "input", "fail_first": 0},
        "B": {"deps": ["A"], "op": "double", "fail_first": {"fail-once": 1, "always-fail": 3}.get(case, 0)},
        "C": {"deps": ["A"], "op": "add3", "fail_first": 0},
        "D": {"deps": ["B", "C"], "op": "sum", "fail_first": 0},
    }}
    if case == "cycle":
        plan["tasks"]["A"]["deps"] = ["D"]
        plan["tasks"]["A"]["op"] = "sum"
    return plan


def validate(plan):
    if not isinstance(plan, dict) or set(plan) != {"seed", "retries", "tasks"}:
        raise ValueError("plan fields must be seed/retries/tasks")
    if type(plan["seed"]) is not int or not 1 <= plan["seed"] <= 9:
        raise ValueError("seed must be integer 1..9")
    if type(plan["retries"]) is not int or not 0 <= plan["retries"] <= 2:
        raise ValueError("retries must be integer 0..2")
    tasks = plan["tasks"]
    if not isinstance(tasks, dict) or not 1 <= len(tasks) <= 6:
        raise ValueError("1..6 tasks required")
    if any(not isinstance(k, str) or not k.isascii() or not k.isalpha() or len(k) != 1 for k in tasks):
        raise ValueError("task IDs must be single ASCII letters")
    for spec in tasks.values():
        if not isinstance(spec, dict) or set(spec) != {"deps", "op", "fail_first"}:
            raise ValueError("invalid task fields")
        deps = spec["deps"]
        if not isinstance(deps, list) or any(not isinstance(d, str) or d not in tasks for d in deps):
            raise ValueError("unknown dependency")
        if len(set(deps)) != len(deps):
            raise ValueError("duplicate dependency")
        if spec["op"] not in ("input", "double", "add3", "sum"):
            raise ValueError("unsupported operation")
        if spec["op"] == "input" and deps:
            raise ValueError("input task must have no predecessors")
        if spec["op"] in ("double", "add3") and len(deps) != 1:
            raise ValueError("unary operation needs one predecessor")
        if type(spec["fail_first"]) is not int or not 0 <= spec["fail_first"] <= 3:
            raise ValueError("fail_first must be integer 0..3")


def topology(plan):
    """Own Kahn-style ordering; deterministic sorted ready node selection."""
    validate(plan)
    remaining = set(plan["tasks"])
    order = []
    while remaining:
        ready = sorted(n for n in remaining if all(d in order for d in plan["tasks"][n]["deps"]))
        if not ready:
            raise ValueError("cycle: rejected before task execution")
        node = ready[0]
        order.append(node)
        remaining.remove(node)
    return order


def independent_oracle(plan):
    """Enumerate all permutations and recursively evaluate expectations, not runner events."""
    validate(plan)
    names = sorted(plan["tasks"])
    orders = []
    for order in itertools.permutations(names):
        pos = {n: i for i, n in enumerate(order)}
        if all(pos[d] < pos[n] for n in names for d in plan["tasks"][n]["deps"]):
            orders.append(list(order))
    if not orders:
        return {"permutations_examined": len(list(itertools.permutations(names))), "valid_orders": [], "cycle": True, "expected": {}}
    expected = {}

    def expected_node(n):
        if n in expected:
            return expected[n]
        spec = plan["tasks"][n]
        ancestors = [expected_node(d) for d in spec["deps"]]
        if any(d["state"] != "succeeded" for d in ancestors):
            item = {"state": "blocked", "value": None, "attempts": 0}
        elif spec["fail_first"] > plan["retries"]:
            item = {"state": "failed", "value": None, "attempts": plan["retries"] + 1}
        else:
            values = [d["value"] for d in ancestors]
            expected_value = {"input": lambda: plan["seed"], "double": lambda: 2 * values[0],
                              "add3": lambda: values[0] + 3, "sum": lambda: sum(values)}[spec["op"]]()
            item = {"state": "succeeded", "value": expected_value, "attempts": spec["fail_first"] + 1}
        expected[n] = item
        return item

    for n in names:
        expected_node(n)
    return {"permutations_examined": len(list(itertools.permutations(names))), "valid_orders": orders,
            "cycle": False, "expected": expected}


def invoke(spec, values, attempt, seed):
    if attempt <= spec["fail_first"]:
        raise ArithmeticError("synthetic failure; no side effects")
    if spec["op"] == "input":
        return seed
    if spec["op"] == "double":
        return values[0] * 2
    if spec["op"] == "add3":
        return values[0] + 3
    return sum(values)


def run(plan, previous=None):
    """previous successes may be reused only with unchanged plan/source and validated result."""
    plan = copy.deepcopy(plan)
    validate(plan)
    plan_hash = digest(plan)
    source_hash = source_digest()
    events = []
    states = {n: {"state": "pending", "attempts": 0, "value": None, "reused": False} for n in sorted(plan["tasks"])}

    def event(action, node=None, **detail):
        events.append({"step": len(events), "action": action, "task": node, **detail, "state": copy.deepcopy(states)})

    event("created")
    try:
        order = topology(plan)
    except ValueError as error:
        event("rejected", reason=str(error))
        return {"plan": plan, "plan_digest": plan_hash, "source_digest": source_hash,
                "status": "rejected", "reason": str(error), "order": [], "events": events,
                "tasks": states, "invocations": [], "previous_result_digest": None}
    if previous is not None:
        if previous.get("plan_digest") != plan_hash or previous.get("source_digest") != source_hash:
            raise ValueError("resume plan/source mismatch")
        # Validate against the independent mathematical oracle without invoking tasks again.
        reference = independent_oracle(plan)["expected"]
        if previous.get("status") not in ("succeeded", "failed") or set(previous.get("tasks", {})) != set(states):
            raise ValueError("invalid previous result")
        for n, old in previous["tasks"].items():
            ref = reference[n]
            if old.get("state") != ref["state"] or old.get("value") != ref["value"]:
                raise ValueError("previous result does not match current pure task outputs")
            if type(old.get("attempts")) is not int or old["attempts"] != (0 if old.get("reused") else ref["attempts"]):
                raise ValueError("invalid previous attempts")
        for n in order:
            if previous["tasks"][n]["state"] == "succeeded":
                states[n] = {"state": "succeeded", "attempts": 0, "value": previous["tasks"][n]["value"], "reused": True}
                event("reused-success", n, prior_attempts=previous["tasks"][n]["attempts"])
    invocations = []
    for n in order:
        if states[n]["reused"]:
            continue
        deps = plan["tasks"][n]["deps"]
        if any(states[d]["state"] != "succeeded" for d in deps):
            states[n]["state"] = "blocked"
            event("blocked", n, blockers=[d for d in deps if states[d]["state"] != "succeeded"])
            continue
        states[n]["state"] = "ready"
        event("ready", n, dependencies=list(deps))
        for attempt in range(1, plan["retries"] + 2):
            states[n]["state"] = "running"
            states[n]["attempts"] = attempt
            values = [states[d]["value"] for d in deps]
            invocations.append({"task": n, "attempt": attempt, "dependency_values": values})
            event("started", n, attempt=attempt, dependency_values=values)
            try:
                value = invoke(plan["tasks"][n], values, attempt, plan["seed"])
            except ArithmeticError as error:
                exhausted = attempt == plan["retries"] + 1
                states[n]["state"] = "failed" if exhausted else "retrying"
                event("attempt-failed", n, attempt=attempt, error=str(error), budget_exhausted=exhausted)
                if exhausted:
                    break
            else:
                states[n]["state"] = "succeeded"
                states[n]["value"] = value
                event("succeeded", n, attempt=attempt, output=value)
                break
    status = "succeeded" if all(s["state"] == "succeeded" for s in states.values()) else "failed"
    event("finished", status=status)
    return {"plan": plan, "plan_digest": plan_hash, "source_digest": source_hash, "status": status,
            "order": order, "events": events, "tasks": states, "invocations": invocations,
            "previous_result_digest": None if previous is None else digest(previous)}


def observe(case="normal", retries=1, seed=2, previous=None, command=None):
    plan = fixture(case, retries, seed)
    result = run(plan, previous)
    oracle = independent_oracle(plan)
    expected = oracle["expected"]
    matches = result["status"] == "rejected" if oracle["cycle"] else all(
        result["tasks"][n]["state"] == expected[n]["state"] and result["tasks"][n]["value"] == expected[n]["value"]
        and result["tasks"][n]["attempts"] == (0 if result["tasks"][n]["reused"] else expected[n]["attempts"])
        for n in expected)
    return {"input": {"case": case, "retries": retries, "seed": seed, "reuse_successes": previous is not None},
            "previous_result": copy.deepcopy(previous),
            "result": result, "oracle": oracle, "oracle_matches": matches,
            "execution": {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          "python": platform.python_version(), "platform": platform.system() + " " + platform.machine(),
                          "command": command or ["python3", "runner.py"], "simulation": True,
                          "external_side_effects": False, "product_scheduler": False}}


def publish(payload, label="run", root=ROOT / "observations", fail_before_publish=False):
    """New immutable run directory. Failed staging cannot alter any earlier observation."""
    token = uuid.uuid4().hex
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    stage = root / (".staging-" + token)
    target = root / (label + "-" + token)
    stage.mkdir()
    raw = canonical(payload) + b"\n"
    with (stage / "result.json").open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    metadata = {"artifact": "result.json", "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "input_digest": digest(payload["input"]), "plan_digest": payload["result"]["plan_digest"],
                "source_digest": payload["result"]["source_digest"], "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    metadata["source_files"] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                for name in ("runner.py", "test_runner.py", "serve.py", "app.js", "index.html", "style.css")}
    with (stage / "metadata.json").open("xb") as stream:
        stream.write(canonical(metadata) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    if fail_before_publish:
        raise OSError("intentional staging failure; previous observations preserved")
    stage.rename(target)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="normal")
    parser.add_argument("--retries", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--seed", type=int, choices=range(1, 10), default=2)
    parser.add_argument("--reuse", action="store_true", help="run once, then reuse its successes in a second finite run")
    parser.add_argument("--record", action="store_true", help="append an immutable observation directory")
    args = parser.parse_args()
    previous = run(fixture(args.case, args.retries, args.seed)) if args.reuse else None
    payload = observe(args.case, args.retries, args.seed, previous, ["python3", "runner.py", *sys.argv[1:]])
    if args.record:
        location = publish(payload)
        print("record: " + str(location.relative_to(ROOT)), file=sys.stderr)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
