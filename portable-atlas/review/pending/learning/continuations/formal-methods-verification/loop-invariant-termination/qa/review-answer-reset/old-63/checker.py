"""Independent closed-form oracle plus literal pre-implementation hand traces."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def oracle(data):
    n, budget, body = data["n"], data["budget"], data["body"]
    s = 1 if body == "normal" else 2
    m = min(n, budget)
    rows = [(0, "initial", n, 0, True)]
    for j in range(1, m+1):
        rows += [(j, "after_x", n-j, s*(j-1), False),
                 (j, "boundary", n-j, s*j, True)]
    trace = [{"k": k, "phase": phase, "x": x, "y": y, "sum": x+y,
              "boundary": boundary, "equals_n": x+y == n}
             for k, phase, x, y, boundary in rows]
    bad = s == 2 and m > 0
    return {"category": "invariant_violation" if bad else
            "budget_exhausted" if m < n else "observed_correct",
            "completion": "guard_exit" if m == n else "budget_exhausted",
            "iterations": m, "boundary_invariant_all": not bad,
            "postcondition": s*n == n if m == n else None,
            "variant_decreases": True, "trace": trace}


def execute(data):
    p = subprocess.run([sys.executable, "-B", str(ROOT/"calculate.py")],
                       input=json.dumps(data), text=True, capture_output=True)
    assert p.returncode == 0 and not p.stderr, (p.returncode, p.stderr)
    return json.loads(p.stdout)


def main():
    hand = json.loads((ROOT/"hand-table.json").read_text())
    for key, n, body in [("zero", 0, "normal"), ("normal3", 3, "normal"),
                         ("double3", 3, "double-y"), ("normal1", 1, "normal"),
                         ("double1", 1, "double-y")]:
        got = oracle({"n": n, "budget": n, "body": body})
        assert [[r["k"], r["phase"], r["x"], r["y"]] for r in got["trace"]] == hand[key]
    for n in range(9):
        for budget in range(9):
            for body in ("normal", "double-y"):
                data = {"n": n, "budget": budget, "body": body}
                assert execute(data) == oracle(data), data
    expected = json.loads((ROOT/"expected.json").read_text())
    for case in expected:
        got = execute(case["input"])
        assert all(got[k] == v for k, v in case.items() if k not in ("id", "input")), case
    # Output mutants represent mistakes in phase, guard/budget, arithmetic and inference.
    basis = [oracle(c["input"]) for c in expected[:6]]
    mutants = []
    for field, value, index in [("completion", "budget_exhausted", 0),
                              ("postcondition", False, 3),
                              ("boundary_invariant_all", True, 2),
                              ("category", "observed_correct", 4),
                              ("variant_decreases", False, 2),
                              ("iterations", 2, 1)]:
        v = copy.deepcopy(basis[index]); v[field] = value
        mutants.append((index, v))
    for field, value, row in [("boundary", True, 1), ("x", 3, 1), ("y", 2, 2),
                             ("sum", 3, 1), ("equals_n", True, 1), ("phase", "boundary", 1)]:
        v = copy.deepcopy(basis[1]); v["trace"][row][field] = value
        mutants.append((1, v))
    assert all(v != basis[i] for i, v in mutants)
    # Missing/ill-typed schema and malformed JSON are separate refusal checks.
    for value in [None, [], {}, {"n":0,"budget":False,"body":"normal"},
                  {"n":8,"budget":-1,"body":"normal"}, {"n":9,"budget":8,"body":"normal"}]:
        assert execute(value)["category"] == "input_refused"
    print(json.dumps({"status":"PASS", "closed_form_domain":162, "hand_traces":5,
                      "fixed_cases":12, "refusal_extras":6, "output_mutants_rejected":len(mutants)},
                     sort_keys=True))


if __name__ == "__main__":
    main()
