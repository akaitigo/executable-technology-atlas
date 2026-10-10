#!/usr/bin/env python3
"""Verify stored observations against the independent pre-execution oracle. Never execute Kotlin."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    expected = json.loads((HERE / "expected.json").read_text())
    checks = []

    def require(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    require(report["schema"] == "atlas.kotlin-captured-local-var.observation.v1", "observation schema")
    require(report["collection_complete"] and not report["errors"], "collection complete")
    require(report["resource_gate"]["allowed"] is True, "resource gate before execution")
    require(report["resource_gate_after_representative"]["allowed"] is True, "resource gate after representative")
    require(report["representative_passed"] is True, "representative preserved without rerun")
    require(report["source_unchanged"] is True, "sources unchanged during execution")
    for name, digest in report["source_sha256"].items():
        require(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, "source: " + name)
    for key in ("archive_sha256", "launcher_sha256"):
        require(report["toolchain"][key] == expected["compiler_" + key], "fixed toolchain: " + key)
    require(report["toolchain"]["tree_matches_archive"] is True, "compiler tree matches fixed archive")
    require("kotlinc-jvm 2.4.10" in report["compiler_probe"]["stdout"] + report["compiler_probe"]["stderr"], "compiler version")
    require('version "17.0.17"' in report["java_probe"]["stdout"] + report["java_probe"]["stderr"], "JDK version")
    compiles = {row["id"]: row for row in report["compiles"]}
    require(len(compiles) == len(report["compiles"]) == 2, "exactly two compile cases")
    require(set(compiles) == {row["id"] for row in expected["compiles"]}, "compile case identities")
    for fixed in expected["compiles"]:
        actual = compiles[fixed["id"]]
        require(actual["exit_code"] == fixed["exit_code"], fixed["id"] + ": exit")
        require(actual["artifact_created"] is fixed["artifact_created"], fixed["id"] + ": artifact presence")
        artifact = HERE / actual["artifact"]
        if fixed["diagnostic"]:
            require("[" + fixed["diagnostic"] + "]" in actual["stderr"], "expected compile diagnostic")
            require(not artifact.exists(), "rejected compile has no artifact")
        else:
            require(hashlib.sha256(artifact.read_bytes()).hexdigest() == actual["artifact_sha256"], "executed artifact hash")
    runs = {(r["mode"], r["input"]): r for r in report["runs"]}
    require(len(runs) == len(report["runs"]) == 4, "exactly four runtime cases")
    require(set(runs) == {(r["mode"], r["input"]) for r in expected["runs"]}, "runtime case identities")
    for fixed in expected["runs"]:
        key = (fixed["mode"], fixed["input"])
        actual = runs[key]
        require(actual["exit_code"] == fixed["exit_code"] == 0, "/".join(key) + ": normal exit")
        require(actual["stdout"] == fixed["stdout"], "/".join(key) + ": full stdout")
        require(actual["stderr"] == "", "/".join(key) + ": empty stderr")
    require(len(report["commands"]) == 8, "two version probes plus two compiles plus four runtime commands")
    require(all(r["attempt"] == 1 and r["retry"] == 0 for r in report["commands"]), "no retries")
    require(all(r["priority_observation"]["after"] >= 10 and r["priority_observation"]["verified_before_exec"] for r in report["commands"]), "mandatory nice priority confirmed before exec")
    require(all(not r["timed_out"] and not r["owned_process_group_remaining_after_exit"] for r in report["commands"]), "no timeouts or remaining owned process groups")
    require(report["global_concurrency_guarantee"] is False and report["all_capture_cases_covered"] is False, "finite scope only")
    print(json.dumps({"passed": True, "checks": checks, "report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
                      "normal_runtime": 4, "expected_runtime_failure": 0, "compile_rejections": 1,
                      "fresh_compiler_execution": False}, indent=2))


if __name__ == "__main__":
    main()
