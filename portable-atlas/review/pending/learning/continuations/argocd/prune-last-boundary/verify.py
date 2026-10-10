#!/usr/bin/env python3
"""手計算期待値との軽い照合。原票の上書きはしない。"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from model import load_cases, plan

ROOT = Path(__file__).resolve().parent
BOUND = ("fixtures.json", "hand-oracle.json", "hand-oracle-lock.json", "model.py", "verify.py", "source-review.json")


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def check_model():
    data = load_cases()
    oracle = json.loads((ROOT / "hand-oracle.json").read_text())["cases"]
    lock = json.loads((ROOT / "hand-oracle-lock.json").read_text())
    require(lock["model_or_validator_existed"] is False, "手計算の由来が不一致")
    for name, digest in lock["sha256"].items():
        require(sha(name) == digest, "固定入力/手計算が変更された: " + name)
    require(set(oracle) == {c["id"] for c in data["cases"]}, "ケース集合が不一致")
    outcomes = {}
    for case in data["cases"]:
        untouched = deepcopy(case)
        outcomes[case["id"]] = plan(case, data["scope"])
        require(outcomes[case["id"]] == oracle[case["id"]], "手計算と不一致: " + case["id"])
        require(case == untouched, "入力taskを書き換えた")

    refused = []
    def refusal(label, edit_case=None, edit_scope=None):
        case, scope = deepcopy(data["cases"][1]), deepcopy(data["scope"])
        if edit_case:
            edit_case(case)
        if edit_scope:
            edit_scope(scope)
        try:
            plan(case, scope)
        except ValueError:
            refused.append(label)
        else:
            raise AssertionError("期待した拒否なし: " + label)

    refusal("global-option-string", lambda c: c.update(global_prune_last="true"))
    refusal("resource-option-string", lambda c: c["tasks"][0].update(prune_last="true"))
    refusal("wave-bool", lambda c: c["tasks"][0].update(wave=True))
    refusal("duplicate-id", lambda c: c["tasks"][1].update(id="app-a"))
    refusal("unsupported-phase", lambda c: c["tasks"][0].update(phase="PostSync"))
    refusal("prune-non-sync", lambda c: c["tasks"][2].update(phase="PreSync"))
    refusal("unknown-action", lambda c: c["tasks"][0].update(action="delete"))
    refusal("empty-tasks", lambda c: c.update(tasks=[]))
    refusal("live-execution", edit_scope=lambda s: s.update(live_execution=True))
    refusal("dependency-adjustments", edit_scope=lambda s: s.update(dependency_adjustments=True))

    mutations = []
    def changed(label, case_id, edit):
        wrong = deepcopy(outcomes[case_id])
        edit(wrong)
        require(wrong != oracle[case_id], "改変出力を検出できない: " + label)
        mutations.append(label)

    changed("max-excludes-prune", "global", lambda r: r.update(sync_max=5, last_wave_candidate=6))
    changed("resource-option-applied-globally", "resource-only", lambda r: r["final_waves"].update({"old-high": 9}))
    changed("negative-max-without-zero-seed", "all-negative", lambda r: r.update(sync_max=-2, last_wave_candidate=-1))
    changed("presync-included-in-sync-max", "presync-excluded", lambda r: r.update(sync_max=20, last_wave_candidate=21))
    changed("phase-overwritten", "presync-excluded", lambda r: r["phases"].update({"old": "PostSync"}))
    return outcomes, refused, mutations


def check_cli():
    cases = [
        ("input", ["--case", "global", "--view", "input"], 0),
        ("correct-negative", ["--case", "all-negative", "--predict-wave", "1", "--predict-selected", "old-high,old-low", "--json"], 0),
        ("wrong-resource-scope", ["--case", "resource-only", "--predict-wave", "6", "--predict-selected", "old-high,old-low", "--json"], 0),
        ("unknown-id", ["--predict-selected", "ghost"], 2),
        ("readable-phase-contrast", ["--case", "presync-excluded"], 0),
    ]
    records = []
    for label, args, exit_code in cases:
        run = subprocess.run([sys.executable, "-B", str(ROOT / "model.py"), *args], capture_output=True, text=True, timeout=5)
        require(run.returncode == exit_code, "CLI exit不一致: " + label)
        if label == "input":
            require("予想 |" in run.stdout and "指定後の計画" not in run.stdout, "予想段階で答えを表示した")
        elif label in ("correct-negative", "wrong-resource-scope"):
            correct = label == "correct-negative"
            require(json.loads(run.stdout)["prediction"] == {"wave_matches": correct, "selection_matches": correct}, "予想照合不一致")
        elif label == "unknown-id":
            require("対象IDが不正" in run.stderr, "拒否理由なし")
        else:
            require("PreSync wave  20" in run.stdout and "Sync    wave   1" in run.stdout, "phase対照表示が不正")
            require("phaseは保持" in run.stdout, "phase保持の説明なし")
        records.append({"label": label, "arguments": args, "exit_code": run.returncode, "pass": True,
                        "stdout": run.stdout, "stderr": run.stderr})
    return records


def main():
    parser = argparse.ArgumentParser(description="固定5ケースの計画模型。通常は書込みなし。")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args()
    destination = ROOT / "observations/model-check.json"
    if args.record and destination.exists():
        parser.error("原票が既にあります。上書きしません")
    hashes = {name: sha(name) for name in BOUND}
    if destination.exists():
        require(json.loads(destination.read_text())["artifact_sha256"] == hashes, "実行原票と現在の実装hashが不一致")
    start = time.perf_counter()
    report = {"schema": 1, "kind": "finite-prune-last-plan-model", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "artifact_sha256": hashes, "python": platform.python_version(), "machine": platform.machine(),
              "attempt": 1, "retry": 0, "upstream_executed": False, "live_executed": False,
              "browser_executed": False, "image_qa_executed": False, "health_observed": False}
    try:
        model_start = time.perf_counter()
        outcomes, refused, mutations = check_model()
        report["model_check_seconds"] = round(time.perf_counter() - model_start, 6)
        report.update(status="pass", cases=5, task_inputs=18, outcomes=outcomes,
                      expected_refusals=refused, altered_output_detections=mutations, cli_checks=check_cli())
    except Exception as exc:
        report.update(status="fail", error=f"{type(exc).__name__}: {exc}")
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["total_seconds"] = round(time.perf_counter() - start, 6)
    if args.record:
        with destination.open("x") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if report["status"] == "pass":
        print(f"PASS: 5ケース/18入力、拒否{len(refused)}、出力改変検出{len(mutations)}、CLI{len(report['cli_checks'])}")
        print(f"模型 {report['model_check_seconds']:.6f}秒、CLI込み {report['total_seconds']:.6f}秒。Health/LIVE/GUIは未観測。")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
