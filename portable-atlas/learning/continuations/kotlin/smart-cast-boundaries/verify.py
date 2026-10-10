#!/usr/bin/env python3
"""将来保存される実観測だけを検証する。固定期待値を観測へ変換しない。"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="保存したKotlin実観測の独立検証")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    expected = json.loads((HERE / "expected.json").read_text())
    checks = []
    def require(ok, label):
        if not ok:
            raise AssertionError(label)
        checks.append(label)
    require(report["schema"] == "atlas.kotlin-smart-cast-boundaries.observation.v1", "実観測形式")
    require(report["collection_complete"] and not report["errors"], "収集完了")
    require(report["resource_gate"]["allowed"] is True, "実行前の負荷条件")
    require(report["source_unchanged"], "実行中のsource不変")
    for name, digest in report["source_sha256"].items():
        require(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, "source: " + name)
    for key in ("archive_sha256", "launcher_sha256"):
        require(report["toolchain"][key] == expected["compiler_" + key], "固定toolchain: " + key)
    require(report["toolchain"]["tree_matches_archive"] is True, "固定配布tree")
    require("kotlinc-jvm 2.4.10" in report["compiler_probe"]["stdout"] + report["compiler_probe"]["stderr"], "compiler実version")
    require('version "17.0.17"' in report["java_probe"]["stdout"] + report["java_probe"]["stderr"], "JDK実version")
    actual_compiles = {row["id"]: row for row in report["compiles"]}
    require(len(actual_compiles) == len(report["compiles"]) == 3, "compile3ケース")
    for fixed in expected["compiles"]:
        actual = actual_compiles[fixed["id"]]
        require(actual["exit_code"] == fixed["exit_code"], fixed["id"] + ": exit")
        require(actual["artifact_created"] is fixed["artifact_created"], fixed["id"] + ": JAR有無")
        if fixed["diagnostic"]:
            require("[" + fixed["diagnostic"] + "]" in actual["stderr"], fixed["id"] + ": diagnostic")
            require(not (HERE / actual["artifact"]).exists(), fixed["id"] + ": 拒否後JARなし")
        else:
            require(hashlib.sha256((HERE / actual["artifact"]).read_bytes()).hexdigest() == actual["artifact_sha256"], "実行JAR")
    actual_runs = {(r["mode"], r["input"]): r for r in report["runs"]}
    require(len(actual_runs) == len(report["runs"]) == 6, "runtime6ケース")
    for fixed in expected["runs"]:
        key = (fixed["mode"], fixed["input"]); actual = actual_runs[key]
        require(actual["exit_code"] == fixed["exit_code"], "/".join(key) + ": exit")
        require(actual["stdout"] == fixed["stdout"], "/".join(key) + ": 全stdout")
        if fixed["stderr_contains"] is None:
            require(actual["stderr"] == "", "/".join(key) + ": stderrなし")
        else:
            require(fixed["stderr_contains"] in actual["stderr"], "/".join(key) + ": runtime NPE")
    require(all(row["attempt"] == 1 and row["retry"] == 0 for row in report["commands"]), "再試行なし")
    require(report["global_concurrency_guarantee"] is False and report["all_properties_covered"] is False, "範囲の限界")
    print(json.dumps({"passed": True, "checks": checks, "report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
                      "fresh_compiler_execution": False, "normal_runtime": 5, "expected_runtime_failure": 1,
                      "compile_rejections": 2}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
