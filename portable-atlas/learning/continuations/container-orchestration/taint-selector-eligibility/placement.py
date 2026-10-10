"""Atlas: finite pre-placement filters; no Kubernetes execution or reservation."""
import copy


def invalid(request, topology):
    if type(request) is not dict or set(request) != {"available", "nodeSelector", "tolerations"}:
        return "invalid-request-schema"
    available = request["available"]
    if type(available) is not dict or set(available) != {"A", "B"}:
        return "invalid-available"
    for name in ("A", "B"):
        free = available[name]
        if type(free) is not dict or set(free) != {"cpu", "memory"}:
            return "invalid-available"
        if any(type(free[k]) is not int or not 0 <= free[k] <= topology["nodes"][name]["capacity"][k]
               for k in ("cpu", "memory")):
            return "invalid-available"
    selector = request["nodeSelector"]
    if type(selector) is not dict or set(selector) not in (set(), {"pool"}):
        return "invalid-selector"
    if selector and selector["pool"] not in ("general", "special"):
        return "invalid-selector"
    tolerations = request["tolerations"]
    if type(tolerations) is not list or len(tolerations) > 1:
        return "invalid-toleration"
    for t in tolerations:
        if type(t) is not dict or set(t) != {"key", "operator", "value", "effect"}:
            return "invalid-toleration"
        if (t["key"] != "reserved" or t["operator"] != "Equal"
                or t["value"] not in ("team-a", "team-b") or t["effect"] != "NoSchedule"):
            return "invalid-toleration"
    return None


def evaluate(request, topology, mode):
    if mode not in ("strict", "ignore-taint"):
        raise ValueError("unknown internal mode")
    reason = invalid(request, topology)
    if reason:
        return {"kind": "input-refused", "reason": reason, "payload": None}
    rows, feasible, candidates = [], [], []
    demand = topology["podDemand"]
    for name in topology["selectionOrder"]:
        node, free = topology["nodes"][name], request["available"][name]
        cpu = free["cpu"] >= demand["cpu"]
        memory = free["memory"] >= demand["memory"]
        selector = all(node["labels"].get(k) == v for k, v in request["nodeSelector"].items())
        taint = all(any(t["key"] == item["key"] and t["value"] == item["value"]
                        and t["effect"] == item["effect"] for t in request["tolerations"])
                    for item in node["taints"])
        rows.append({"node": name, "available": copy.deepcopy(free), "demand": copy.deepcopy(demand),
                     "cpuFits": cpu, "memoryFits": memory, "selectorFits": selector, "taintFits": taint})
        if cpu and memory and selector and taint:
            feasible.append(name)
        if cpu and memory and selector and (taint or mode == "ignore-taint"):
            candidates.append(name)
    selected = candidates[0] if candidates else None
    return {"kind": "evaluated", "payload": {"nodeChecks": rows, "feasibleNodes": feasible,
            "selectionCandidates": candidates, "selectionOrder": list(topology["selectionOrder"]),
            "selectedNode": selected, "outcome": "BOUND" if selected is not None else "PENDING"}}
