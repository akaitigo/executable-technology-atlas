"""Independent unit-slot model and bounded exhaustive feasibility oracle."""
import sys
sys.dont_write_bytecode = True
from functools import lru_cache


def unit_timeline(plan):
    # Prebuild immutable releases. Service count is independent of runner.remaining.
    jobs = []
    for name, spec in sorted(plan["tasks"].items()):
        for index, release in enumerate(range(0, plan["horizon"], spec["period"])):
            jobs.append({"id": name + str(index), "task": name, "index": index, "release": release,
                         "deadline": release + spec["period"], "execution": spec["execution"]})
    served = {j["id"]: 0 for j in jobs}
    finish = {j["id"]: None for j in jobs}
    timeline = []
    for time in range(plan["horizon"]):
        eligible = [j for j in jobs if j["release"] <= time and served[j["id"]] < j["execution"]]
        eligible.sort(key=lambda j: (j["deadline"], j["task"], j["index"]))
        chosen = eligible[0] if eligible else None
        timeline.append(None if chosen is None else chosen["id"])
        if chosen:
            jid = chosen["id"]
            served[jid] += 1
            if served[jid] == chosen["execution"]:
                finish[jid] = time + 1
    expected = {}
    for j in jobs:
        jid = j["id"]
        end = finish[jid]
        expected[jid] = {"release": j["release"], "deadline": j["deadline"], "execution": j["execution"],
                         "remaining": j["execution"] - served[jid], "finish": end,
                         "missed": j["deadline"] <= plan["horizon"] and (end is None or end > j["deadline"]),
                         "lateness": None if end is None else end - j["deadline"],
                         "tardiness": None if end is None else max(0, end - j["deadline"])}
    return {"timeline": timeline, "jobs": expected,
            "first_miss": min((j["deadline"] for j in expected.values() if j["missed"]), default=None)}


def small_feasibility(plan):
    """Search all eligible CPU choices incl idle; first <=12 ticks only. Not EDF logic."""
    horizon = min(plan["horizon"], 12)
    jobs = []
    for spec in plan["tasks"].values():
        for release in range(0, horizon, spec["period"]):
            if release + spec["period"] <= horizon:
                jobs.append((release, release + spec["period"], spec["execution"]))
    visited = 0

    @lru_cache(None)
    def search(time, remaining):
        nonlocal visited
        visited += 1
        if any(rem > 0 and deadline <= time for rem, (_, deadline, _) in zip(remaining, jobs)):
            return False
        if time == horizon:
            return True
        choices = [i for i, (release, _, _) in enumerate(jobs) if release <= time and remaining[i] > 0]
        for i in choices:
            following = list(remaining)
            following[i] -= 1
            if search(time + 1, tuple(following)):
                return True
        return search(time + 1, remaining)

    feasible = search(0, tuple(job[2] for job in jobs))
    return {"horizon": horizon, "demand_jobs": len(jobs), "states_visited": visited, "feasible_schedule_exists": feasible,
            "scope": "jobs released and due within first <=12 ticks; not whole-system proof"}


def check(plan, result):
    expected = unit_timeline(plan)
    actual = []
    for segment in result["segments"]:
        actual.extend([segment["job"]] * (segment["end"] - segment["start"]))
    jobs_match = set(result["jobs"]) == set(expected["jobs"]) and all(
        all(result["jobs"][jid][key] == value for key, value in spec.items()) for jid, spec in expected["jobs"].items())
    flag_match = result["summary"]["safe_since"] == expected["first_miss"] and result["summary"]["safe_state"] == (expected["first_miss"] is not None)
    return {"timeline": expected["timeline"], "expected_jobs": expected["jobs"], "first_miss": expected["first_miss"],
            "timeline_matches": actual == expected["timeline"], "jobs_match": jobs_match, "safe_flag_matches": flag_match,
            "all_match": actual == expected["timeline"] and jobs_match and flag_match,
            "small_feasibility": small_feasibility(plan)}
