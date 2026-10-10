"""Atlas: graphlib の完了通知と、有限仮想時刻の完了を別に観測する。"""
from graphlib import TopologicalSorter

PARENTS = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}


def validate(request):
    if type(request) is not dict or set(request) != {"capacity", "durations", "release"}:
        return "request-invalid"
    if type(request["capacity"]) is not int or request["capacity"] not in (1, 2):
        return "capacity-invalid"
    durations = request["durations"]
    if (type(durations) is not dict or set(durations) != set(PARENTS)
            or any(type(v) is not int or not 1 <= v <= 4 for v in durations.values())):
        return "durations-invalid"
    if request["release"] not in ("on-complete", "on-start"):
        return "release-invalid"
    return None


def simulate(request):
    reason = validate(request)
    if reason:
        return {"accepted": False, "reason": reason, "payload": None}
    sorter = TopologicalSorter(PARENTS)
    sorter.prepare()
    ready, completed, processed = set(), set(), set()
    running, schedule, released_at = {}, {}, {}
    events, snapshots, violations = [], [], []
    time = 0

    def event(kind, task, **extra):
        events.append(dict(time=time, kind=kind, task=task, **extra))

    def notify(task):
        sorter.done(task)
        processed.add(task)
        event("done", task)

    def collect_ready():
        for task in sorted(sorter.get_ready()):
            ready.add(task)
            released_at[task] = time
            event("ready", task)

    # Positive finite durations: at most initial boundary + four completion boundaries.
    for _ in range(5):
        for task in sorted(task for task, end in running.items() if end == time):
            del running[task]
            completed.add(task)
            event("finish", task)
            if request["release"] == "on-complete":
                notify(task)
        collect_ready()
        while ready and len(running) < request["capacity"]:
            task = min(ready)
            ready.remove(task)
            unfinished = [p for p in PARENTS[task] if p not in completed]
            violations.extend([[p, task] for p in unfinished])
            end = time + request["durations"][task]
            schedule[task] = [time, end]
            running[task] = end
            event("start", task, end=end, unfinishedParents=unfinished)
            if request["release"] == "on-start":
                notify(task)
            collect_ready()
        rows = []
        for task in PARENTS:
            state = ("completed" if task in completed else "running" if task in running
                     else "ready-capacity" if task in ready else "dependency-wait")
            unfinished = [p for p in PARENTS[task] if p not in completed]
            rows.append({"task": task, "state": state, "dependenciesComplete": not unfinished,
                         "unfinishedParents": unfinished, "releasedAt": released_at.get(task),
                         "start": schedule[task][0] if task in schedule else None,
                         "end": schedule[task][1] if task in schedule else None})
        snapshots.append({"time": time, "rows": rows, "ready": sorted(ready),
                          "running": sorted(running), "completed": sorted(completed),
                          "schedulerProcessed": sorted(processed), "graphlibActive": sorter.is_active(),
                          "occupied": len(running), "freeSlots": request["capacity"] - len(running)})
        if len(completed) == len(PARENTS):
            break
        if not running:
            raise RuntimeError("fixed DAG cannot progress")
        time = min(running.values())
    else:
        raise RuntimeError("finite event boundary exceeded")
    return {"accepted": True, "reason": None, "payload": {
        "schedule": schedule, "events": events, "snapshots": snapshots,
        "dependencyViolations": violations, "makespan": time,
        "dependenciesRespected": not violations, "allPhysicallyCompleted": len(completed) == 4}}
