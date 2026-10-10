"""Finite scheduler model. No Docker, Kubernetes API or container execution."""
import copy
import hashlib
import json

CAPACITY = {"node-a": 2, "node-b": 2}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def invalid(request, state):
    if type(request) is not dict or set(request) != {"desired_replicas", "health", "expected_revision"}:
        return "invalid-request-schema"
    if type(request["desired_replicas"]) is not int or not 0 <= request["desired_replicas"] <= 6:
        return "invalid-replicas"
    if type(request["health"]) is not dict or set(request["health"]) != set(CAPACITY) or any(type(v) is not bool for v in request["health"].values()):
        return "invalid-node-health"
    if type(state) is not dict or set(state) != {"revision", "pods"} or type(state["revision"]) is not int or state["revision"] < 0 or type(state["pods"]) is not list:
        return "invalid-state-schema"
    if type(request["expected_revision"]) is not int or request["expected_revision"] != state["revision"]:
        return "stale-revision"
    ids = []
    for pod in state["pods"]:
        if type(pod) is not dict or set(pod) != {"id", "node"} or pod["id"] not in ["pod-" + str(i) for i in range(1, 7)] or pod["node"] not in [None, *CAPACITY]:
            return "invalid-pod"
        ids.append(pod["id"])
    if len(ids) != len(set(ids)):
        return "duplicate-pod"
    if any(sum(p["node"] == n for p in state["pods"]) > c for n, c in CAPACITY.items()):
        return "invalid-input-overcommit"
    return None


def reconcile(request, state, bad_ignore_capacity=False):
    before = copy.deepcopy(state)
    reason = invalid(request, state)
    events = []
    if reason:
        return {"outcome": "blocked", "reason": reason, "state": before, "events": [{"event": "blocked", "reason": reason}],
                "pre_digest": digest(before), "post_digest": digest(before), "changed": False}
    desired_ids = ["pod-" + str(i) for i in range(1, request["desired_replicas"] + 1)]
    pods = {}
    for pod in state["pods"]:
        if pod["id"] not in desired_ids:
            events.append({"event": "delete-model-pod", "id": pod["id"], "previous_node": pod["node"]})
            continue
        pods[pod["id"]] = copy.deepcopy(pod)
        if pod["node"] and not request["health"][pod["node"]]:
            events.append({"event": "unbind-failed-node", "id": pod["id"], "previous_node": pod["node"]})
            pods[pod["id"]]["node"] = None
    for ident in desired_ids:
        if ident not in pods:
            pods[ident] = {"id": ident, "node": None}
            events.append({"event": "create-model-pod", "id": ident})
    used = {n: sum(p["node"] == n for p in pods.values()) for n in CAPACITY}
    for ident in desired_ids:
        if pods[ident]["node"]:
            continue
        eligible = [n for n in CAPACITY if request["health"][n] and (bad_ignore_capacity or used[n] < CAPACITY[n])]
        events.append({"event": "filter", "id": ident, "eligible": eligible, "capacity_enforced": not bad_ignore_capacity})
        if not eligible:
            events.append({"event": "pending", "id": ident, "reason": "no-feasible-slot"})
            continue
        target = min(eligible, key=lambda n: (used[n], n))
        pods[ident]["node"] = target
        used[target] += 1
        events.append({"event": "bind-model-pod", "id": ident, "node": target})
    after_pods = [pods[i] for i in desired_ids]
    changed = after_pods != before["pods"]
    after = {"revision": before["revision"] + int(changed), "pods": after_pods}
    pending = sum(p["node"] is None for p in after_pods)
    return {"outcome": "pending" if pending else "bound", "reason": None, "state": after, "events": events,
            "pre_digest": digest(before), "post_digest": digest(after), "changed": changed}
