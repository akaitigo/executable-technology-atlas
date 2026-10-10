"""Deterministic finite preemptive EDF. Time is abstract ticks, not OS wall time."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import datetime
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid

ROOT = Path(__file__).resolve().parent
CASES = ("normal", "boundary", "overload")


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def fixture(case="normal", horizon=12):
    if case not in CASES:
        raise ValueError("unknown case")
    plan = {"horizon": horizon, "tasks": {
        "A": {"period": 4, "execution": {"normal": 1, "boundary": 2, "overload": 3}[case]},
        "B": {"period": 6, "execution": 3},
    }}
    validate(plan)
    return plan


def validate(plan):
    if not isinstance(plan, dict) or set(plan) != {"horizon", "tasks"}:
        raise ValueError("expected horizon and tasks")
    if type(plan["horizon"]) is not int or not 1 <= plan["horizon"] <= 36:
        raise ValueError("horizon must be integer 1..36")
    tasks = plan["tasks"]
    if not isinstance(tasks, dict) or set(tasks) != {"A", "B"}:
        raise ValueError("exactly two tasks A/B required")
    for spec in tasks.values():
        if not isinstance(spec, dict) or set(spec) != {"period", "execution"}:
            raise ValueError("invalid task fields")
        if type(spec["period"]) is not int or not 2 <= spec["period"] <= 12:
            raise ValueError("period must be integer 2..12")
        if type(spec["execution"]) is not int or not 1 <= spec["execution"] <= spec["period"]:
            raise ValueError("execution must be integer 1..period")


def simulate(plan):
    """Jump to release/deadline/finish boundaries; execute one CPU segment at a time."""
    validate(plan)
    plan = copy.deepcopy(plan)
    horizon = plan["horizon"]
    jobs = {}
    next_release = {n: 0 for n in plan["tasks"]}
    counters = {n: 0 for n in plan["tasks"]}
    events, segments = [], []
    safe_state, safe_since = False, None

    def event(action, time, job=None, **fields):
        events.append({"seq": len(events), "time": time, "action": action, "job": job,
                       **fields, "safe_state": safe_state, "safe_since": safe_since,
                       "jobs": copy.deepcopy(jobs)})

    event("created", 0)
    time = 0
    active = None
    while time <= horizon:
        # Previous segment finish was committed before deadline checks at this boundary.
        for jid in sorted(jobs):
            item = jobs[jid]
            if item["deadline"] <= time and not item["deadline_checked"]:
                item["deadline_checked"] = True
                missed = item["finish"] is None or item["finish"] > item["deadline"]
                item["missed"] = missed
                event("deadline-miss" if missed else "deadline-met", time, jid,
                      deadline=item["deadline"], remaining=item["remaining"])
                if missed and not safe_state:
                    safe_state, safe_since = True, time
                    event("safe-state-latched", time, jid, reason="deadline miss; model flag only")
        if time == horizon:
            break
        for name in sorted(plan["tasks"]):
            if next_release[name] == time:
                index = counters[name]
                counters[name] += 1
                spec = plan["tasks"][name]
                jid = name + str(index)
                jobs[jid] = {"id": jid, "task": name, "index": index, "release": time,
                             "deadline": time + spec["period"], "execution": spec["execution"],
                             "remaining": spec["execution"], "finish": None,
                             "lateness": None, "tardiness": None, "missed": False, "deadline_checked": False}
                next_release[name] += spec["period"]
                event("released", time, jid, deadline=jobs[jid]["deadline"])
        ready = [j for j in jobs.values() if j["remaining"] > 0]
        selected = min(ready, key=lambda j: (j["deadline"], j["task"], j["index"])) if ready else None
        jid = None if selected is None else selected["id"]
        if active is not None and jobs[active]["remaining"] > 0 and active != jid:
            event("preempted", time, active, next_job=jid)
        active = jid
        future = [horizon, *[t for t in next_release.values() if t > time],
                  *[j["deadline"] for j in jobs.values() if j["deadline"] > time and not j["deadline_checked"]]]
        if selected:
            future.append(time + selected["remaining"])
        end = min(future)
        if end <= time:
            raise AssertionError("time must advance")
        if selected:
            selected["remaining"] -= end - time
        segments.append({"start": time, "end": end, "job": jid})
        event("executed" if selected else "idle", end, jid, start=time, end=end)
        time = end
        if selected and selected["remaining"] == 0:
            selected["finish"] = time
            selected["lateness"] = time - selected["deadline"]
            selected["tardiness"] = max(0, selected["lateness"])
            event("finished", time, jid, lateness=selected["lateness"], tardiness=selected["tardiness"])
    event("horizon-reached", time, reason="no further releases or CPU execution beyond finite horizon")
    utilization = sum(Fraction(t["execution"], t["period"]) for t in plan["tasks"].values())
    return {"plan": plan, "input_digest": digest(plan), "events": events, "segments": segments,
            "jobs": jobs, "summary": {"utilization_fraction": str(utilization), "utilization": float(utilization),
                                      "misses": sum(j["missed"] for j in jobs.values()),
                                      "unfinished": sum(j["finish"] is None for j in jobs.values()),
                                      "safe_state": safe_state, "safe_since": safe_since,
                                      "max_completed_tardiness": max([j["tardiness"] for j in jobs.values() if j["tardiness"] is not None] or [0]),
                                      "released_jobs": len(jobs), "trace_events": len(events)}}


def observe(case="normal", horizon=12, command=None):
    # Oracle is a separate module and does not call simulate or share its job update logic.
    from oracle import check
    plan = fixture(case, horizon)
    result = simulate(plan)
    expected = check(plan, result)
    return {"input": {"case": case, "horizon": horizon}, "result": result, "oracle": expected,
            "execution": {"observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          "python": platform.python_version(), "platform": platform.system() + " " + platform.machine(),
                          "command": command or ["python3", "-B", "runner.py"],
                          "source_digest": hashlib.sha256((ROOT / "runner.py").read_bytes()).hexdigest(),
                          "time_unit": "abstract-integer-tick", "real_os_realtime": False,
                          "safety_device": False, "simulation": True}}


def publish(payload, label="run", root=ROOT / "observations", fail_before_publish=False):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    stage = root / (".staging-" + token)
    target = root / (label + "-" + token)
    stage.mkdir()
    raw = canonical(payload) + b"\n"
    for name, content in (("result.json", raw),):
        with (stage / name).open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    metadata = {"artifact": "result.json", "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "input_digest": digest(payload["input"]), "plan_digest": payload["result"]["input_digest"],
                "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "source_files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                 for name in ("runner.py", "oracle.py", "test_runner.py", "serve.py", "app.js", "index.html", "style.css")}}
    with (stage / "metadata.json").open("xb") as stream:
        stream.write(canonical(metadata) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    if fail_before_publish:
        raise OSError("intentional staging failure; prior records remain unchanged")
    stage.rename(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, default="normal")
    parser.add_argument("--horizon", type=int, choices=(12, 24, 36), default=12)
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    result = observe(args.case, args.horizon, ["python3", "-B", "runner.py", *sys.argv[1:]])
    if args.record:
        where = publish(result)
        print("record: " + str(where.relative_to(ROOT)), file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
