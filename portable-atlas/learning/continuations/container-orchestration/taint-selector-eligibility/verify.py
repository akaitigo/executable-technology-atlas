"""Atlas: literal masks and output tables; producer is neither imported nor rerun."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def strict_equal(actual, wanted):
    if type(actual) is not type(wanted):
        return False
    if type(actual) is dict:
        return (len(actual) == len(wanted) and all(type(k) is str and k in wanted
                and strict_equal(value, wanted[k]) for k, value in actual.items()))
    if type(actual) is list:
        return len(actual) == len(wanted) and all(strict_equal(a, b) for a, b in zip(actual, wanted))
    return actual == wanted


def check(data):
    fixture = json.loads((ROOT / "cases.json").read_text())
    expected = json.loads((ROOT / "expected.json").read_text())
    topology = json.loads((ROOT / "topology.json").read_text())
    checks = 0

    def eq(actual, wanted):
        nonlocal checks
        checks += 1
        if not strict_equal(actual, wanted):
            raise AssertionError("literal mismatch at relation " + str(checks))

    eq(data["kind"], "synthetic_preplacement_model")
    eq([x["id"] for x in data["cases"]], [x["id"] for x in expected["cases"]])
    eq([x["id"] for x in data["refusals"]], [x["id"] for x in expected["refusals"]])
    totals = {"strict": {"BOUND": 0, "PENDING": 0}, "ignore-taint": {"BOUND": 0, "PENDING": 0, "infeasibleSelections": 0}}
    for c, f, e in zip(data["cases"], fixture["cases"], expected["cases"]):
        for side in ("before", "after"):
            eq(c["request_" + side], f["request"])
            eq(c["topology_" + side], topology)
        rows = []
        for name in ("A", "B"):
            row = {"node": name, "available": f["request"]["available"][name], "demand": {"cpu": 2, "memory": 1}}
            row.update({k: v == "1" for k, v in zip(e["gateMaskOrder"], e["nodeMasks"][name])})
            rows.append(row)
        for mode, key in (("strict", "strict"), ("ignore-taint", "fault")):
            wanted = {"kind": "evaluated", "payload": {"nodeChecks": rows, "feasibleNodes": e["feasibleNodes"],
                       "selectionCandidates": e[mode]["selectionCandidates"], "selectionOrder": ["A", "B"],
                       "selectedNode": e[mode]["selectedNode"], "outcome": e[mode]["outcome"]}}
            eq(c[key], wanted)
            payload = c[key]["payload"]
            for row, wanted_row in zip(payload["nodeChecks"], rows):
                for k in wanted_row:
                    eq(row[k], wanted_row[k])
            selected = payload["selectedNode"]
            violation = selected is not None and selected not in e["feasibleNodes"]
            eq(violation, e[mode]["selectionViolatesFeasibility"])
            totals[mode][payload["outcome"]] += 1
            if mode == "ignore-taint":
                totals[mode]["infeasibleSelections"] += int(violation)
        eq(c["strict"]["payload"]["nodeChecks"], c["fault"]["payload"]["nodeChecks"])
        eq(c["strict"]["payload"]["feasibleNodes"], c["fault"]["payload"]["feasibleNodes"])
    for c, f, e in zip(data["refusals"], fixture["refusals"], expected["refusals"]):
        eq(c["result"], e["expected"])
        for side in ("before", "after"):
            eq(c["request_" + side], f["request"])
            eq(c["topology_" + side], topology)
    eq(totals, expected["totals"])
    return checks


def verify(data):
    count = check(data)
    mutations = []
    for name in ("missing-case", "invented-feasible-node", "taint-hidden", "toleration-as-attraction",
                 "capacity-ignored", "refusal-with-payload", "input-mutated", "wrong-node-gate", "nested-bool-as-int"):
        d = copy.deepcopy(data)
        if name == "missing-case": d["cases"].pop()
        elif name == "invented-feasible-node": d["cases"][1]["fault"]["payload"]["feasibleNodes"] = ["B"]
        elif name == "taint-hidden": d["cases"][1]["strict"]["payload"]["nodeChecks"][1]["taintFits"] = True
        elif name == "toleration-as-attraction": d["cases"][2]["strict"]["payload"]["selectedNode"] = "B"
        elif name == "capacity-ignored": d["cases"][5]["strict"]["payload"]["selectionCandidates"] = ["B"]
        elif name == "refusal-with-payload": d["refusals"][0]["result"]["payload"] = {"selectedNode": "A"}
        elif name == "input-mutated": d["cases"][0]["request_after"]["available"]["A"]["cpu"] = 2
        elif name == "wrong-node-gate": d["cases"][3]["strict"]["payload"]["nodeChecks"][0]["selectorFits"] = True
        else: d["refusals"][1]["request_before"]["available"]["B"]["cpu"] = 1
        try:
            check(d)
        except (AssertionError, KeyError, TypeError, IndexError):
            mutations.append({"name": name, "rejected": True})
        else:
            raise AssertionError("mutation was not rejected: " + name)
    return {"Atlas": "Saved values checked against manual tables", "passed": True, "checks": count, "mutations": mutations}
