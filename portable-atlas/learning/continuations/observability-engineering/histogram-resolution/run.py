"""Atlas single child CLI. Root runner owns priority, deadline and reaping."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parent
INPUTS = ("CONTRACT.md", "cases.json", "expected.json", "histogram.py", "verify.py", "run.py", "SOURCES.md", "reuse-and-scope.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="observations/run-01")
    args = parser.parse_args()
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority < 10:
        raise SystemExit("Atlas target not imported: actual nice must be >=10")
    output = (ROOT / args.output).resolve()
    if ROOT not in output.parents or output.exists():
        raise SystemExit("Atlas output must be new and inside this lesson")
    from copy import deepcopy
    from fractions import Fraction
    from histogram import aggregate, estimate_from_counts, raw_nearest_rank
    from verify import check_results, check_mutations
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    inputs = {name: (ROOT / name).read_bytes() for name in INPUTS}
    cases = json.loads(inputs["cases.json"])
    expected = json.loads(inputs["expected.json"])
    saved = {"title": "Atlas ヒストグラムの有限計算", "mode": "finite_synthetic_calculation",
             "quantiles": cases["quantiles"], "cases": [],
             "toolchain": {"python": platform.python_version(), "executable": os.sys.executable},
             "execution": {"pid": os.getpid(), "actualNice": priority, "startedUTC": started},
             "inputs": {name: hashlib.sha256(data).hexdigest() for name, data in inputs.items()}}
    for request in cases["cases"]:
        before = deepcopy(request)
        histogram = aggregate(request["values"], request["edges"])
        rows = []
        for q in cases["quantiles"]:
            aggregate_input = {"edges": list(histogram["edges"]), "counts": list(histogram["counts"]), "q": q}
            estimated = estimate_from_counts(**aggregate_input)
            raw = raw_nearest_rank(request["values"], q)
            error = None if raw is None else Fraction(estimated["estimate"]) - Fraction(raw)
            rows.append({"q": q, "aggregateInput": aggregate_input, "aggregateOutput": estimated,
                         "rawNearestRank": raw, "signedError": None if error is None else str(error),
                         "comparison": "empty" if error is None else "equal" if error == 0 else "above" if error > 0 else "below"})
        saved["cases"].append({"id": request["id"], "label": request["label"], "inputBefore": before,
                               "inputAfter": deepcopy(request), "histogram": histogram, "results": rows})
    saved["execution"].update(endedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsedSeconds=time.monotonic() - clock)
    (output / "inputs").mkdir(parents=True)
    for name, data in inputs.items():
        (output / "inputs" / name).write_bytes(data)
    def write(name, data):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write("results.json", saved)
    readback = json.loads((output / "results.json").read_text(encoding="utf-8"))
    checked = check_results(readback, cases, expected)
    mutations = check_mutations(readback, cases, expected)
    write("saved-result-check.json", {**checked, "mutations": mutations, "resultSha256": hashlib.sha256((output / "results.json").read_bytes()).hexdigest()})
    print(json.dumps({"title": "Atlas finite run", "passed": True, "output": str(output), "pid": os.getpid(), "actualNice": priority, **checked}))


if __name__ == "__main__":
    main()
