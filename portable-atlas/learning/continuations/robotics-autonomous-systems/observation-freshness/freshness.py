"""Atlas finite map-knowledge policy. No world state, robot or ROS."""
from copy import deepcopy

TTL = 4
INITIAL = {"state": "unknown", "observedAt": None, "arrivedAt": None, "adoptedVersion": 0, "mapRevision": 0}
POLICIES = ("guarded", "arrival-only")


def validate(steps, policy):
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("policy")
    if type(steps) is not list or not steps:
        raise ValueError("steps")
    previous = -1
    for step in steps:
        if type(step) is not dict or set(step) != {"now", "arrival"}:
            raise ValueError("step keys")
        now, arrival = step["now"], step["arrival"]
        if type(now) is not int or now < 0 or now <= previous:
            raise ValueError("now")
        previous = now
        if arrival is None:
            continue
        if type(arrival) is not dict or set(arrival) != {"version", "observedAt", "arrivedAt", "state"}:
            raise ValueError("arrival keys")
        for key in ("version", "observedAt", "arrivedAt"):
            if type(arrival[key]) is not int or arrival[key] < (1 if key == "version" else 0):
                raise ValueError(key)
        if arrival["arrivedAt"] != now:
            raise ValueError("arrival/query convention")
        if type(arrival["state"]) is not str or arrival["state"] not in ("free", "occupied", "unknown"):
            raise ValueError("state")


def update_observation(current, arrival, now, policy):
    if arrival is None:
        return deepcopy(current), {"action": "none", "reason": "no-arrival", "incomingAge": None}
    incoming_age = now - arrival["observedAt"]
    reason = None
    if policy == "guarded":
        if incoming_age < 0:
            reason = "future-observation"
        elif arrival["version"] <= current["adoptedVersion"]:
            reason = "stale-version"
        elif current["observedAt"] is not None and arrival["observedAt"] < current["observedAt"]:
            reason = "time-regression"
        elif incoming_age > TTL:
            reason = "expired-at-arrival"
    if reason is not None:
        return deepcopy(current), {"action": "reject", "reason": reason, "incomingAge": incoming_age}
    after = {"state": arrival["state"], "observedAt": arrival["observedAt"], "arrivedAt": arrival["arrivedAt"],
             "adoptedVersion": arrival["version"], "mapRevision": current["mapRevision"] + 1}
    return after, {"action": "accept", "reason": "accepted" if policy == "guarded" else "arrival-overwrite", "incomingAge": incoming_age}


def inspect_knowledge(current, now, policy):
    age = None if current["observedAt"] is None else now - current["observedAt"]
    fresh = None if age is None else 0 <= age <= TTL
    effective = current["state"] if policy == "arrival-only" or fresh is True else "unknown"
    return {"age": age, "fresh": fresh, "effectiveState": effective}


def simulate(steps, policy):
    validate(steps, policy)
    current, rows = deepcopy(INITIAL), []
    for step in steps:
        before = deepcopy(current)
        current, update = update_observation(current, step["arrival"], step["now"], policy)
        knowledge = inspect_knowledge(current, step["now"], policy)
        decision = {"free": "MOVE_ALLOWED", "occupied": "STOP_OCCUPIED", "unknown": "STOP_UNKNOWN"}[knowledge["effectiveState"]]
        rows.append({"now": step["now"], "arrival": deepcopy(step["arrival"]), "before": before, "update": update,
                     "after": deepcopy(current), "knowledge": knowledge,
                     "nextEdge": {"from": [0, 0], "to": [1, 0], "decision": decision,
                                  "actualMovement": False, "worldState": "not-observed"}})
    return rows
