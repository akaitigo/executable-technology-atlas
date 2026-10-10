"""Atlas literal saved-result comparison. Does not import producer."""
from copy import deepcopy


def eq(actual, expected, path="value"):
    if type(actual) is not type(expected):
        raise AssertionError(path + ": type")
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise AssertionError(path + ": keys")
        return 1 + sum(eq(actual[k], v, path + "." + k) for k, v in expected.items())
    if isinstance(expected, list):
        if len(actual) != len(expected):
            raise AssertionError(path + ": length")
        return 1 + sum(eq(a, e, path + "[]") for a, e in zip(actual, expected))
    if actual != expected:
        raise AssertionError(path + ": value")
    return 1


def check_results(saved, cases, expected):
    count = eq(saved["ttl"], 4)
    count += eq(saved["position"], [0, 0]) + eq(saved["targetCell"], [1, 0])
    count += eq(saved["initial"], cases["initial"])
    count += eq([c["id"] for c in saved["cases"]], [c["id"] for c in cases["cases"]])
    for got, req, manual in zip(saved["cases"], cases["cases"], expected["cases"]):
        count += eq(got["id"], manual["id"]) + eq(got["label"], req["label"])
        count += eq(got["inputBefore"], req["steps"]) + eq(got["inputAfter"], req["steps"])
        count += eq(sorted(got["policies"]), ["arrival-only", "guarded"])
        for policy in ("guarded", "arrival-only"):
            rows = got["policies"][policy]
            count += eq(len(rows), len(req["steps"]))
            previous = deepcopy(cases["initial"])
            for row, step, values in zip(rows, req["steps"], manual[policy]):
                d = dict(zip(expected["columns"], values))
                after = {"state": d["storedState"], "observedAt": d["observedAt"], "arrivedAt": d["arrivedAt"],
                         "adoptedVersion": d["adoptedVersion"], "mapRevision": d["mapRevision"]}
                want = {"now": d["now"], "arrival": step["arrival"], "before": previous,
                        "update": {"action": d["action"], "reason": d["reason"], "incomingAge": d["incomingAge"]},
                        "after": after, "knowledge": {"age": d["age"], "fresh": d["fresh"], "effectiveState": d["effectiveState"]},
                        "nextEdge": {"from": [0, 0], "to": [1, 0], "decision": d["decision"], "actualMovement": False, "worldState": "not-observed"}}
                count += eq(row, want, got["id"] + ":" + policy + "@" + str(step["now"]))
                previous = after
    return {"passed": True, "relations": count, "cases": 5, "steps": 15, "responses": 30}


def check_mutations(saved, cases, expected):
    def row(d, case, policy, index):
        return d["cases"][case]["policies"][policy][index]
    changes = [
        ("missing-row", lambda d: d["cases"][0]["policies"]["guarded"].pop()),
        ("arrival-time-as-observation-time", lambda d: row(d, 1, "arrival-only", 1)["after"].update(observedAt=7)),
        ("reject-mutated-map", lambda d: row(d, 1, "guarded", 1)["after"].update(state="free")),
        ("rejected-event-renews-expiry", lambda d: row(d, 1, "guarded", 2)["knowledge"].update(age=3)),
        ("boundary-exclusive", lambda d: row(d, 2, "guarded", 1)["knowledge"].update(fresh=False)),
        ("unknown-to-free", lambda d: row(d, 4, "guarded", 1)["knowledge"].update(effectiveState="free")),
        ("version-as-revision", lambda d: row(d, 1, "guarded", 0)["after"].update(mapRevision=2)),
        ("null-age-to-zero", lambda d: row(d, 3, "guarded", 0)["knowledge"].update(age=0)),
        ("boolean-for-integer-input", lambda d: d["cases"][4]["inputAfter"][1]["arrival"].update(version=True)),
    ]
    rejected = []
    for name, change in changes:
        altered = deepcopy(saved)
        change(altered)
        try:
            check_results(altered, cases, expected)
        except (AssertionError, KeyError, IndexError):
            rejected.append(name)
        else:
            raise AssertionError("mutation passed: " + name)
    return {"scope": "saved copies only, no new observation executions", "rejected": rejected, "count": len(rejected)}
