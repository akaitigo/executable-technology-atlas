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
    env = records[0]
    ck("fixed runtime", env["kind"] == "environment" and env["java_version"] == "17.0.17" and env["kotlin_version"] == "2.4.10")
    ck("CPU and heap cap", env["available_processors"] == 1 and env["max_heap_bytes"] <= 64 * 1024 * 1024)
    ck("compiler caps", run["explicit_environment"]["JAVA_OPTS"] == "-Xms32m -Xmx256m -XX:ActiveProcessorCount=1")
    cases = [r for r in records if r["kind"] == "case"]
    ck("six fixed cases", [c["id"] for c in cases] == expected["case_order"])
    ck("known record kinds only", all(r["kind"] in ["environment", "event", "phase", "case", "batch-complete"] for r in records))
    ck("single environment and terminator", sum(r["kind"] == "environment" for r in records) == sum(r["kind"] == "batch-complete" for r in records) == 1)
    ck("batch terminator", records[-1] == {"kind": "batch-complete", "case_count": 6, "retry_count": 0, "worker_count": 0})
    def token_ok(t, ident):
        return t is None if ident is None else t == {"id": ident, "marker": 7}
    cursor = 1
    for c in cases:
        label = c["id"]
        family = c["family"]
        mode = c["mode"]
        w = expected[family]
        ck(label + " identity", label == family + "-" + mode.lower() and mode in ["SYNCHRONIZED", "PUBLICATION", "NONE"])
        ck(label + " successful finite fixture", c["collection_complete"] and not c["failures"] and c["worker_count"] == 0 and c["calls_total"] == 2 and c["final_depth"] == 0)
        phases, events = c["phases"], c["events"]
        ck(label + " phase ids", [p["id"] for p in phases] == w["phase_ids"])
        ck(label + " phase counts", [p["calls"] for p in phases] == w["calls"])
        ck(label + " initialization state", [p["initialized"] for p in phases] == w["initialized"])
        ck(label + " events sequenced", [e["sequence"] for e in events] == list(range(1, len(events) + 1)))
        ck(label + " single main thread", all(e["thread"] == env["thread"] for e in events))
        ck(label + " initializer attempts", [e["attempt_id"] for e in events if e["kind"] == "initializer-enter"] == [1, 2])
        ck(label + " generated order", c["created_ids"] == w["created_ids"] and [e["token"]["id"] for e in events if e["kind"] == "token-created"] == w["created_ids"])
        ck(label + " token markers", all(e["token"] is None or e["token"]["marker"] == 7 for e in events))
        segment = []
        while cursor < len(records) and records[cursor]["kind"] != "case":
            segment.append(records[cursor]); cursor += 1
        ck(label + " stream case order", records[cursor] == c)
        cursor += 1
        ck(label + " stream identity", all(r["case_id"] == label for r in segment))
        ck(label + " complete streamed events", [r["event"] for r in segment if r["kind"] == "event"] == events)
        ck(label + " complete streamed phases", [r["phase"] for r in segment if r["kind"] == "phase"] == phases)
        def sequence(kind):
            return next(e["sequence"] for e in events if e["kind"] == kind)
        if family == "failure":
            ck(label + " planned exception only", len(c["planned_exceptions"]) == 1 and c["max_depth"] == 1)
            e = c["planned_exceptions"][0]
            ck(label + " exception details", e["type"] == w["exception_type"] and e["message"] == w["exception_message"] and e["stack"].startswith(w["exception_type"] + ": " + w["exception_message"]) and "LazyFailureReentry.kt:" in e["stack"])
            ck(label + " current values", all(token_ok(p["current"], ident) for p, ident in zip(phases, w["returned_ids"])))
            ck(label + " outcomes", [p["outcome"] for p in phases] == ["not-read", "expected-initializer-exception", "normal", "normal"])
            ck(label + " reads", c["reads"] == {"retry-getter": {"id": 2, "marker": 7}, "later-getter": {"id": 2, "marker": 7}})
            ck(label + " identity after success", c["comparisons"] == {"successful_reads_same_reference": True})
            ck(label + " exception before retry", sequence("planned-throw") < sequence("expected-exception-caught") < sequence("retry-read-start") < sequence("retry-read-return") < sequence("later-read-start") < sequence("later-read-return"))
            ck(label + " failed attempt returned no token", [e["attempt_id"] for e in events if e["kind"] == "initializer-return"] == [2])
            expected_refs = [{}, {}, {"retry-getter": {"id": 2, "marker": 7}}, c["reads"]]
            expected_created = [[], [], [2], [2]]
            expected_depth = [0, 0, 0, 0]
            ck(label + " exception history at true boundary", [p["planned_exceptions_so_far"] for p in phases] == [[], c["planned_exceptions"], c["planned_exceptions"], c["planned_exceptions"]])
        else:
            m = w[mode]
            ck(label + " bounded reentry", c["max_depth"] == 2 and not c["planned_exceptions"])
            ck(label + " current values", all(token_ok(p["current"], ident) for p, ident in zip(phases, [None, 2, m["first_id"], m["later_id"]])))
            ck(label + " outcomes", [p["outcome"] for p in phases] == ["not-read", "normal", "normal", "normal"])
            refs = {"inner-getter": {"id": 2, "marker": 7}, "outer-created": {"id": 1, "marker": 7}, "outer-initializer-return": {"id": 1, "marker": 7}, "outer-getter": {"id": m["first_id"], "marker": 7}, "later-getter": {"id": m["later_id"], "marker": 7}}
            ck(label + " distinct reference roles", c["reads"] == refs)
            ck(label + " actual identity comparisons", c["comparisons"] == {"inner_same_as_outer_created": False, "first_same_as_inner": m["first_same_as_inner"], "first_same_as_outer_created": m["first_same_as_outer_created"], "later_same_as_first": True, "outer_initializer_return_same_as_outer_created": True})
            ck(label + " nested returns before outer", [e["attempt_id"] for e in events if e["kind"] == "initializer-return"] == [2, 1] and sequence("nested-read-start") < sequence("nested-read-return") < sequence("outer-read-return") < sequence("later-read-return"))
            ck(label + " finally unwinds", [(e["attempt_id"], e["depth"]) for e in events if e["kind"] == "initializer-exit"] == [(2, 1), (1, 0)])
            expected_refs = [{}, {"inner-getter": refs["inner-getter"]}, {k: v for k, v in refs.items() if k != "later-getter"}, refs]
            expected_created = [[], [2], [2, 1], [2, 1]]
            expected_depth = [0, 1, 0, 0]
            ck(label + " no exception history", all(p["planned_exceptions_so_far"] == [] for p in phases))
        ck(label + " only known references at each phase", [p["known_references"] for p in phases] == expected_refs)
        ck(label + " creation at each phase", [p["created_ids"] for p in phases] == expected_created)
        ck(label + " depth at each phase", [p["depth"] for p in phases] == expected_depth)
    ck("all stream consumed before terminator", cursor == len(records) - 1)
    return checks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    run = json.loads(args.run.read_text())
    try:
        checks = verify(run)
        mutations = []
        if args.mutations:
            def cases(r): return [x for x in r["records"] if x["kind"] == "case"]
            changes = [
                ("incorrect-exception-initialized", lambda r: cases(r)[0]["phases"][1].update(initialized=True)),
                ("lost-expected-exception", lambda r: cases(r)[1].update(planned_exceptions=[])),
                ("wrong-retry-identity", lambda r: cases(r)[2]["comparisons"].update(successful_reads_same_reference=False)),
                ("publication-outer-candidate-as-result", lambda r: cases(r)[4]["reads"]["outer-getter"].update(id=1)),
                ("call-order-as-creation-order", lambda r: cases(r)[3].update(created_ids=[1, 2])),
                ("reentry-reference-conflation", lambda r: cases(r)[5]["comparisons"].update(inner_same_as_outer_created=True)),
                ("future-reference-leaked", lambda r: cases(r)[4]["phases"][0]["known_references"].update(cases(r)[4]["reads"])),
                ("missing-partial-stream", lambda r: r["records"].pop(2)),
                ("priority-unverified", lambda r: r["commands"][0]["priority"]["priority"].update(verified_before_exec=False)),
                ("cleanup-incomplete", lambda r: r["commands"][1].update(owned_group_after="present")),
            ]
            for name, change in changes:
                bad = copy.deepcopy(run); change(bad)
                try: verify(bad, bind_files=False)
                except (ValueError, KeyError, TypeError, IndexError, StopIteration) as e:
                    mutations.append({"name": name, "rejected": True, "reason": str(e)})
                else: raise ValueError("mutation accepted: " + name)
        print(json.dumps({"project": "Atlas", "passed": True, "check_count": len(checks), "checks": checks, "mutations": mutations, "new_kotlin_execution": False}, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"project": "Atlas", "passed": False, "error_type": type(e).__name__, "error": str(e)}, indent=2))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
