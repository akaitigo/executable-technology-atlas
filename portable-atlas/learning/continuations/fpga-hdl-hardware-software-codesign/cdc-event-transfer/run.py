"""Atlas one finite child. Root wrapper owns resource gate/deadline/reaping."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import time

ROOT = Path(__file__).resolve().parent
INPUTS = ("CONTRACT.md", "cases.json", "expected.json", "cdc.py", "verify.py", "run.py", "SOURCES.md", "reuse-and-scope.md")


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
    from cdc import simulate, teaching_observation
    from verify import check_results, check_mutations
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    clock = time.monotonic()
    inputs = {name: (ROOT / name).read_bytes() for name in INPUTS}
    cases, expected = json.loads(inputs["cases.json"]), json.loads(inputs["expected.json"])
    saved = {"title": "Atlas 理想2クロックの有限計算", "mode": "ideal_binary_model",
             "sourceEdges": cases["sourceEdges"], "destinationEdges": cases["destinationEdges"], "stopTime": cases["stopTime"],
             "cases": [], "toolchain": {"python": platform.python_version(), "executable": os.sys.executable},
             "execution": {"pid": os.getpid(), "actualNice": priority, "startedUTC": start},
             "inputs": {name: hashlib.sha256(data).hexdigest() for name, data in inputs.items()}}
    for case in cases["cases"]:
        before = deepcopy(case["input"])
        observed = simulate(case["input"])
        saved["cases"].append({"id": case["id"], "label": case["label"], "inputBefore": before,
                               "inputAfter": deepcopy(case["input"]), **observed,
                               "teaching": teaching_observation(before, observed)})
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
    print(json.dumps({"title": "Atlas finite CDC run", "passed": True, "output": str(output), "pid": os.getpid(), "actualNice": priority, **checked}))


if __name__ == "__main__":
    main()
