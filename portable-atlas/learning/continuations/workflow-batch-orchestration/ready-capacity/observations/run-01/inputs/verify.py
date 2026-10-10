"""Atlas: producerをimportせず、手区間表と整数時刻の占有から保存値を照合する。"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENTS = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}


def check(result):
    cases = json.loads((ROOT / "cases.json").read_text())
    expected = json.loads((ROOT / "expected.json").read_text())
    count = 0

    def eq(a, b, locator):
        nonlocal count
        count += 1
        if a != b:
            raise AssertionError(locator + ": " + repr(a) + " != " + repr(b))

    eq([r["id"] for r in result["cases"]], [c["id"] for c in cases["cases"]], "case ids")
    eq([r["id"] for r in result["refusals"]], [c["id"] for c in cases["refusals"]], "refusal ids")
    for observed, case in zip(result["cases"], cases["cases"]):
        label = case["id"]
        plan = expected["cases"][label]
        schedule = plan["schedule"]
        request = case["request"]
        eq(observed["requestBefore"], request, label + "/request before")
        eq(observed["requestAfter"], request, label + "/request after")
        response = observed["response"]
        eq(response["accepted"], True, label + "/accepted")
        eq(response["reason"], None, label + "/reason")
        payload = response["payload"]
        for key in ("schedule", "makespan", "dependencyViolations"):
            eq(payload[key], plan[key], label + "/" + key)
        eq(payload["dependenciesRespected"], not plan["dependencyViolations"], label + "/dependency valid")
        eq(payload["allPhysicallyCompleted"], True, label + "/completed")
        release = {task: max([schedule[p][1 if request["release"] == "on-complete" else 0]
                             for p in PARENTS[task]], default=0) for task in PARENTS}
        eq(len(payload["snapshots"]), len(plan["snapshots"]), label + "/boundaries")
        for row, predicted in zip(payload["snapshots"], plan["snapshots"]):
            t = predicted["time"]
            eq(row["time"], t, label + "/time")
            complete = [task for task, (_, end) in schedule.items() if end <= t]
            running = [task for task, (start, end) in schedule.items() if start <= t < end]
            ready = [task for task, (start, _) in schedule.items() if release[task] <= t < start]
            processed = (complete if request["release"] == "on-complete" else
                         [task for task, (start, _) in schedule.items() if start <= t])
            for key, value in [("completed", complete), ("running", running), ("ready", ready),
                               ("schedulerProcessed", processed), ("occupied", len(running)),
                               ("freeSlots", request["capacity"] - len(running)),
                               ("graphlibActive", len(processed) < 4)]:
                eq(row[key], value, label + "/" + str(t) + "/" + key)
            eq([r["task"] for r in row["rows"]], list(PARENTS), label + "/tasks")
            for r, state in zip(row["rows"], predicted["states"]):
                task = r["task"]
                unfinished = [p for p in PARENTS[task] if schedule[p][1] > t]
                expected_row = dict(task=task, state=state, dependenciesComplete=not unfinished,
                                    unfinishedParents=unfinished,
                                    releasedAt=release[task] if release[task] <= t else None,
                                    start=schedule[task][0] if schedule[task][0] <= t else None,
                                    end=schedule[task][1] if schedule[task][0] <= t else None)
                for key in expected_row:
                    eq(r[key], expected_row[key], label + "/" + str(t) + "/" + task + "/" + key)
        # All integer ticks, separately from the event-driven producer's boundary snapshots.
        for t in range(plan["makespan"] + 1):
            selected = max((s for s in payload["snapshots"] if s["time"] <= t), key=lambda s: s["time"])
            running = [task for task, (start, end) in schedule.items() if start <= t < end]
            eq(selected["running"], running, label + "/tick occupancy " + str(t))
            eq(len(running) <= request["capacity"], True, label + "/capacity " + str(t))
        events = payload["events"]
        for task, (start, end) in schedule.items():
            eq([e["time"] for e in events if e["task"] == task and e["kind"] == "start"], [start], label + "/start")
            eq([e["time"] for e in events if e["task"] == task and e["kind"] == "finish"], [end], label + "/finish")
            eq([e["time"] for e in events if e["task"] == task and e["kind"] == "ready"], [release[task]], label + "/release")
            eq([e["time"] for e in events if e["task"] == task and e["kind"] == "done"],
               [end if request["release"] == "on-complete" else start], label + "/done")
            eq(next(e["unfinishedParents"] for e in events if e["task"] == task and e["kind"] == "start"),
               [p for p in PARENTS[task] if schedule[p][1] > start], label + "/start parents")
        for t in sorted(set(e["time"] for e in events)):
            finishes = [i for i, e in enumerate(events) if e["time"] == t and e["kind"] == "finish"]
            starts = [i for i, e in enumerate(events) if e["time"] == t and e["kind"] == "start"]
            eq([events[i]["task"] for i in finishes], sorted(events[i]["task"] for i in finishes), label + "/finish ties")
            eq(not finishes or not starts or max(finishes) < min(starts), True, label + "/finish before start")
    for observed, case in zip(result["refusals"], cases["refusals"]):
        eq(observed["requestBefore"], case["request"], case["id"] + "/before")
        eq(observed["requestAfter"], case["request"], case["id"] + "/after")
        eq(observed["response"], expected["refusals"][case["id"]], case["id"] + "/response")
    return count


def mutations(result):
    variants = []
    r = copy.deepcopy(result); r["cases"].pop(); variants.append(("missing-case", r))
    r = copy.deepcopy(result); r["cases"][0]["response"]["payload"]["schedule"]["C"][0] = 1; variants.append(("start-time", r))
    r = copy.deepcopy(result); r["cases"][0]["response"]["payload"]["snapshots"][1]["rows"][2]["state"] = "dependency-wait"; variants.append(("wait-state", r))
    r = copy.deepcopy(result); r["cases"][2]["response"]["payload"]["snapshots"][2]["schedulerProcessed"] = ["A", "C"]; variants.append(("done-set", r))
    r = copy.deepcopy(result); r["cases"][2]["response"]["payload"]["dependencyViolations"] = []; variants.append(("lost-violation", r))
    r = copy.deepcopy(result); r["refusals"][0]["response"]["payload"] = {}; variants.append(("refusal-payload", r))
    results = []
    for name, changed in variants:
        try:
            check(changed)
        except (AssertionError, KeyError, ValueError):
            results.append({"name": name, "rejected": True})
        else:
            raise AssertionError("mutation accepted: " + name)
    return results


if __name__ == "__main__":
    path = ROOT / "observations/run-01/results.json"
    result = json.loads(path.read_text())
    print(json.dumps({"Atlas": "保存値の照合", "checks": check(result), "mutations": mutations(result),
                      "resultsSha256": hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))
