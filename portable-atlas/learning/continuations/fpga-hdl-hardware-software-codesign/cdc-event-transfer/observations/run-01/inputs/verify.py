"""Atlas saved JSON checker: manual columns, no producer import."""
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
    relations = eq(saved["sourceEdges"], expected["sourceTimes"])
    relations += eq(saved["destinationEdges"], expected["destinationTimes"])
    relations += eq(saved["stopTime"], 25)
    relations += eq([r["id"] for r in saved["cases"]], [r["id"] for r in cases["cases"]])
    times = sorted(expected["sourceTimes"] + expected["destinationTimes"])
    for got, req, manual in zip(saved["cases"], cases["cases"], expected["cases"]):
        relations += eq(got["id"], manual["id"])
        relations += eq(got["label"], req["label"])
        relations += eq(got["inputBefore"], req["input"])
        relations += eq(got["inputAfter"], req["input"])
        relations += eq(got["detectedAt"], manual["detectedAt"])
        relations += eq(got["teaching"], {k: manual[k] for k in ("sentCount", "detectedCount", "unobservedByEnd", "eventMatches")})
        relations += eq([r["time"] for r in got["timeline"]], times)
        previous = {"source": 0, "ff1": 0, "ff2": 0, "history": 0}
        for row in got["timeline"]:
            t = row["time"]
            source_index = max((i for i, x in enumerate(expected["sourceTimes"]) if x <= t), default=-1)
            dest_index = max((i for i, x in enumerate(expected["destinationTimes"]) if x <= t), default=-1)
            source_tick = t in expected["sourceTimes"]
            after = {"source": manual["sourceAfter"][source_index] if source_index >= 0 else 0}
            for reg in ("ff1", "ff2", "history"):
                after[reg] = manual[reg + "After"][dest_index] if dest_index >= 0 else 0
            want = {"time": t, "domain": "source" if source_tick else "destination", "before": previous,
                    "sample": None if source_tick else manual["sample"][dest_index], "after": after,
                    "pulseAfter": manual["pulseAfter"][dest_index] if dest_index >= 0 else 0,
                    "detected": t in manual["detectedAt"],
                    "detectedCount": sum(x <= t for x in manual["detectedAt"])}
            relations += eq(row, want, got["id"] + "@" + str(t))
            previous = after
    return {"passed": True, "relations": relations, "cases": 5, "timelineRows": 100, "destinationRows": 35}


def check_mutations(saved, cases, expected):
    def at(data, case, t):
        return next(x for x in data["cases"][case]["timeline"] if x["time"] == t)
    changes = [
        ("missing-row", lambda d: d["cases"][0]["timeline"].pop()),
        ("ff2-updated-from-new-ff1", lambda d: at(d, 1, 5)["after"].update(ff2=1)),
        ("history-updated-from-new-ff2", lambda d: at(d, 1, 9)["after"].update(history=1)),
        ("counted-held-output-at-source", lambda d: at(d, 1, 10).update(detected=True, detectedCount=2)),
        ("invented-close-toggle", lambda d: d["cases"][4]["detectedAt"].append(9)),
        ("null-delay-to-zero", lambda d: d["cases"][0]["teaching"]["eventMatches"][0].update(delay=0)),
        ("integer-to-bool", lambda d: d["cases"][0]["inputAfter"]["eventTimes"].__setitem__(0, True)),
        ("wrong-destination-sample", lambda d: at(d, 3, 17).update(sample=1)),
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
    return {"scope": "saved JSON mutations, not new clock runs", "rejected": rejected, "count": len(rejected)}
