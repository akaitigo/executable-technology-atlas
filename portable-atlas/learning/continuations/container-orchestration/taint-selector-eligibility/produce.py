"""Atlas: one finite batch, fixed fixtures only, unchanged inputs recorded."""
import copy
import json
from pathlib import Path
from placement import evaluate

ROOT = Path(__file__).resolve().parent


def produce():
    topology = json.loads((ROOT / "topology.json").read_text())
    fixture = json.loads((ROOT / "cases.json").read_text())
    cases, refusals = [], []
    for item in fixture["cases"]:
        request, top = copy.deepcopy(item["request"]), copy.deepcopy(topology)
        record = {"id": item["id"], "request_before": copy.deepcopy(request), "topology_before": copy.deepcopy(top)}
        record["strict"] = evaluate(request, top, "strict")
        record["fault"] = evaluate(request, top, "ignore-taint")
        record.update(request_after=copy.deepcopy(request), topology_after=copy.deepcopy(top))
        cases.append(record)
    for item in fixture["refusals"]:
        request, top = copy.deepcopy(item["request"]), copy.deepcopy(topology)
        before_request, before_topology = copy.deepcopy(request), copy.deepcopy(top)
        result = evaluate(request, top, "strict")
        refusals.append({"id": item["id"], "request_before": before_request, "topology_before": before_topology,
                         "result": result, "request_after": copy.deepcopy(request), "topology_after": copy.deepcopy(top)})
    return {"Atlas": "Finite node eligibility and selection", "kind": "synthetic_preplacement_model",
            "cases": cases, "refusals": refusals}
