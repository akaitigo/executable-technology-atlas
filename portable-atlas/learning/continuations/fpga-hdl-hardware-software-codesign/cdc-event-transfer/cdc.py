"""Atlas ideal binary clock model; no physical metastability model."""
from copy import deepcopy

SOURCE_EDGES = tuple(range(0, 25, 2))
DESTINATION_EDGES = (1, 5, 9, 13, 17, 21, 25)


def validate(request):
    if type(request) is not dict or set(request) != {"mode", "eventTimes", "releaseTime"}:
        raise ValueError("request keys")
    mode, events, release = request["mode"], request["eventTimes"], request["releaseTime"]
    if type(mode) is not str or mode not in ("pulse", "level", "toggle"):
        raise ValueError("mode")
    if type(events) is not list or not 1 <= len(events) <= 2:
        raise ValueError("events")
    if any(type(t) is not int or t not in SOURCE_EDGES for t in events) or events != sorted(set(events)):
        raise ValueError("event times")
    if mode == "toggle":
        if release is not None:
            raise ValueError("toggle release")
    elif len(events) != 1 or type(release) is not int or release not in SOURCE_EDGES or release <= events[0]:
        raise ValueError("pulse/level release")


def destination_step(source_bit, old_registers, detector):
    """Receiver sees one bit, its old registers and detector kind only."""
    new = {"ff1": source_bit, "ff2": old_registers["ff1"], "history": old_registers["ff2"]}
    pulse = new["ff2"] ^ new["history"] if detector == "toggle" else new["ff2"] & (1 - new["history"])
    return new, pulse


def simulate(request):
    validate(request)
    state = {"source": 0, "ff1": 0, "ff2": 0, "history": 0}
    pulse, detected_at, timeline = 0, [], []
    for t in sorted(set(SOURCE_EDGES + DESTINATION_EDGES)):
        before = dict(state)
        is_source = t in SOURCE_EDGES
        sample, detected = None, False
        if is_source:
            if t in request["eventTimes"]:
                state["source"] = 1 - state["source"] if request["mode"] == "toggle" else 1
            elif t == request["releaseTime"]:
                state["source"] = 0
        else:
            sample = before["source"]
            registers, pulse = destination_step(sample, before, request["mode"])
            state.update(registers)
            detected = pulse == 1
            if detected:
                detected_at.append(t)
        timeline.append({"time": t, "domain": "source" if is_source else "destination",
                         "before": before, "sample": sample, "after": dict(state),
                         "pulseAfter": pulse, "detected": detected, "detectedCount": len(detected_at)})
    return {"timeline": timeline, "detectedAt": detected_at}


def teaching_observation(request, receiver_result):
    """Fixed all-or-none cases only; event correspondence is not receiver state."""
    events, received = request["eventTimes"], receiver_result["detectedAt"]
    if len(received) not in (0, len(events)):
        raise ValueError("partial correspondence outside these fixed examples")
    matches = []
    for i, t in enumerate(events):
        destination = received[i] if received else None
        matches.append({"sourceTime": t, "destinationTime": destination,
                        "delay": None if destination is None else destination - t})
    return {"sentCount": len(events), "detectedCount": len(received),
            "unobservedByEnd": len(events) - len(received), "eventMatches": matches}
