#!/usr/bin/env python3
"""Atlas: check saved JVM observations against the handwritten finite contract."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def verify(run, bind_files=True):
    expected = json.loads((ROOT / "expected.json").read_text())
    checks = []
    def ck(label, value):
        checks.append({"label": label, "passed": bool(value)})
        if not value:
            raise ValueError(label)
    def digest(file):
        return hashlib.sha256(file.read_bytes()).hexdigest()
    ck("complete run without errors", run["collection_complete"] and not run["errors"])
    ck("one compile / one JVM / no retry", run["compile_count"] == run["jvm_count"] == 1 and run["retry_count"] == 0)
    ck("fixed inputs unchanged", run["input_unchanged"])
    if bind_files:
        for name, sha in run["input_sha256"].items():
            ck("source bytes " + name, digest(ROOT / name) == sha)
    ck("command sequence", [c["label"] for c in run["commands"]] == ["compile", "runtime"])
    for command in run["commands"]:
        label = command["label"]
        ck(label + " process completed", command["success"] and command["exit_code"] == 0 and not command["timed_out"])
        ck(label + " priority confirmed before exec", command["priority"]["priority"]["verified_before_exec"] and command["priority"]["priority"]["after"] >= 10)
        ck(label + " owned process identity", command["priority"]["pid"] == command["priority"]["pgid"] == command["owned_pid"] == command["owned_pgid"])
        ck(label + " target reached and cleanup", command["target_start_confirmed"] and command["target_not_started"] is not True and command["owned_process_reaped"] and command["owned_group_after"] == "absent")
        if bind_files:
            for stream in ["stdout", "stderr"]:
                ck(label + " " + stream + " bytes", digest(ROOT / command[stream]["path"]) == command[stream]["sha256"])
    if bind_files:
        raw = (ROOT / run["commands"][1]["stdout"]["path"]).read_text()
        ck("full stdout equals parsed records", [json.loads(line) for line in raw.splitlines()] == run["records"])
        ck("compiled artifact retained", digest(ROOT / run["artifact"]["path"]) == run["artifact"]["sha256"])
    records = run["records"]
    ck("seven records", len(records) == 7)
    environment = records[0]
    ck("fixed runtime", environment["kind"] == "environment" and environment["java_version"] == "17.0.17" and environment["kotlin_version"] == "2.4.10")
    ck("CPU and heap cap", environment["available_processors"] == 1 and environment["max_heap_bytes"] <= 64 * 1024 * 1024)
    ck("compiler caps recorded", run["explicit_environment"]["JAVA_OPTS"] == "-Xms32m -Xmx256m -XX:ActiveProcessorCount=1")
    cases = records[1:-1]
    ck("fixed case order", [c["id"] for c in cases] == [c["id"] for c in expected["cases"]])
    for case, wanted in zip(cases, expected["cases"]):
        label = case["id"]
        ck(label + " identity", case["kind"] == "case" and case["mode"] == wanted["mode"] and case["workers"] == wanted["workers"])
        ck(label + " initial", case["initial_count"] == 0 and case["initial_initialized"] is False)
        ck(label + " complete", case["collection_complete"] is True and not case["failures"])
        ck(label + " allowed initializer count", case["count_after"] in wanted["allowed_counts"])
        ck(label + " initialized", case["initialized_after"] is True)
        reads = case["reads"]
        ck(label + " read count", len(reads) == wanted["read_count"])
        readers = ["main-1", "main-2"] if not case["workers"] else ["worker-1", "worker-2", "main-after-workers"]
        ck(label + " reader order", [r["reader"] for r in reads] == readers)
        ck(label + " identical references", all(r["same_reference_as_first"] is True for r in reads))
        ids = {r["id"] for r in reads}
        ck(label + " shared selected id", len(ids) == 1 and all(type(i) is int and 1 <= i <= case["count_after"] for i in ids))
        ck(label + " marker", all(r["marker"] == expected["marker"] for r in reads))
        events = case["events"]
        ck(label + " event sequence", [e["sequence"] for e in events] == list(range(1, len(events) + 1)))
        enters = [e for e in events if e["kind"] == "initializer-enter"]
        returns = [e for e in events if e["kind"] == "initializer-return"]
        ck(label + " recorded initializer attempts", sorted(e["attempt_id"] for e in enters) == list(range(1, case["count_after"] + 1)))
        ck(label + " recorded initializer returns", sorted(e["attempt_id"] for e in returns) == list(range(1, case["count_after"] + 1)))
        ck(label + " initializer token fields", all(e["token_id"] == e["attempt_id"] and e["marker"] == 7 for e in returns))
        for read in reads:
            start = [e for e in events if e["kind"] == "read-start" and e["reader"] == read["reader"]]
            finish = [e for e in events if e["kind"] == "read-return" and e["reader"] == read["reader"]]
            ck(label + " read events " + read["reader"], len(start) == len(finish) == 1 and start[0]["sequence"] < finish[0]["sequence"] and finish[0]["token_id"] == read["id"] and finish[0]["marker"] == read["marker"])
        if case["workers"]:
            ready = [e for e in events if e["kind"] == "worker-ready"]
            release = [e for e in events if e["kind"] == "start-release"]
            returned = [e for e in events if e["kind"] == "workers-returned"]
            ck(label + " real two-worker start", case["created_workers"] == 2 and len(set(case["worker_names"])) == 2 and len(ready) == 2 and len(release) == len(returned) == 1 and case["start_released_after_ready"] is True)
            ck(label + " ready before release", all(e["sequence"] < release[0]["sequence"] for e in ready))
            starts = [e for e in events if e["kind"] == "read-start" and e["reader"].startswith("worker-")]
            ck(label + " read after release", all(e["sequence"] > release[0]["sequence"] for e in starts))
            finishes = [e for e in events if e["kind"] == "read-return" and e["reader"].startswith("worker-")]
            main_start = next(e for e in events if e["kind"] == "read-start" and e["reader"] == "main-after-workers")
            ck(label + " main after worker results", all(e["sequence"] < returned[0]["sequence"] < main_start["sequence"] for e in finishes))
            ck(label + " finite executor cleanup", case["futures_done"] == [True, True] and case["executor_terminated"] is True)
        else:
            ck(label + " sequential only", case["created_workers"] == 0 and case["worker_names"] == [] and case["futures_done"] == [] and case["executor_terminated"] is None and not case["start_released_after_ready"])
    ck("batch terminator", records[-1] == {"kind": "batch-complete", "case_count": 5, "retry_count": 0})
    return checks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    run = json.loads(args.run.read_text())
    try:
        checks = verify(run)
        mutations = []
        if args.mutations:
            changes = [
                ("wrong-count", lambda r: r["records"][1].update(count_after=2)),
                ("wrong-reference", lambda r: r["records"][5]["reads"][1].update(same_reference_as_first=False)),
                ("wrong-marker", lambda r: r["records"][2]["reads"][0].update(marker=8)),
                ("no-priority", lambda r: r["commands"][0]["priority"]["priority"].update(verified_before_exec=False)),
                ("unreaped-workers", lambda r: r["records"][4].update(executor_terminated=False)),
                ("fake-recorded-attempt", lambda r: r["records"][5]["events"].append(r["records"][5]["events"][-1])),
            ]
            for name, change in changes:
                bad = copy.deepcopy(run)
                change(bad)
                try:
                    verify(bad, bind_files=False)
                except (ValueError, KeyError, TypeError, StopIteration, IndexError) as error:
                    mutations.append({"name": name, "rejected": True, "reason": str(error)})
                else:
                    raise ValueError("mutation was accepted: " + name)
        print(json.dumps({"project": "Atlas", "passed": True, "check_count": len(checks), "checks": checks, "mutations": mutations, "new_kotlin_execution": False}, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"project": "Atlas", "passed": False, "error_type": type(error).__name__, "error": str(error)}, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
