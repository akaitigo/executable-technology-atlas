"""Bounded operational simulation; no proof assistant or external dependency."""
import json
import sys


def calculate(data):
    if not isinstance(data, dict) or set(data) != {"n", "budget", "body"}:
        return {"category": "input_refused", "error": "exactly n,budget,body required"}
    if any(type(data[v]) is not int or not 0 <= data[v] <= 8 for v in ("n", "budget")):
        return {"category": "input_refused", "error": "n,budget must be exact integers 0..8"}
    if data["body"] not in ("normal", "double-y"):
        return {"category": "input_refused", "error": "body must be normal or double-y"}
    n, budget = data["n"], data["budget"]
    x, y, k = n, 0, 0
    trace = []

    def snapshot(phase, boundary):
        trace.append({"k": k, "phase": phase, "x": x, "y": y,
                      "sum": x+y, "boundary": boundary, "equals_n": x+y == n})

    snapshot("initial", True)
    while x > 0 and k < budget:
        x -= 1
        k += 1
        snapshot("after_x", False)
        y += 1 if data["body"] == "normal" else 2
        snapshot("boundary", True)
    completion = "guard_exit" if x == 0 else "budget_exhausted"
    invariant = all(row["equals_n"] for row in trace if row["boundary"])
    category = ("invariant_violation" if not invariant else
                "budget_exhausted" if completion == "budget_exhausted" else "observed_correct")
    return {"category": category, "completion": completion, "iterations": k,
            "boundary_invariant_all": invariant,
            "postcondition": y == n if completion == "guard_exit" else None,
            "variant_decreases": all(trace[i]["x"] < trace[i-2]["x"]
                                     for i in range(2, len(trace), 2)),
            "trace": trace}


def main():
    try:
        data = json.loads(sys.stdin.read())
        result = calculate(data)
    except (ValueError, TypeError):
        result = {"category": "input_refused", "error": "invalid JSON"}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
