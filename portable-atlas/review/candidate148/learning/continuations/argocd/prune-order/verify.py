#!/usr/bin/env python3
"""手計算との照合。保存原票の更新や上書きはしない。"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import subprocess
import sys
import time

from model import load_cases, simulate

ROOT = Path(__file__).resolve().parent
BOUND = ("fixtures.json", "hand-oracle.json", "hand-oracle-lock.json", "model.py", "verify.py", "source-review.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def equal_result(actual, expected):
    require(actual == expected, "手計算oracleと結果が異なります")


def check():
    data = load_cases()
    oracle = json.loads((ROOT / "hand-oracle.json").read_text())["cases"]
    lock = json.loads((ROOT / "hand-oracle-lock.json").read_text())
    require(lock["model_and_validator_existed"] is False, "手計算固定の由来が不一致です")
    for name, digest in lock["sha256"].items():
        require(sha(ROOT / name) == digest, "手計算固定後の入力/期待値変更: " + name)
    require({c["id"] for c in data["cases"]} == set(oracle), "ケース集合が不一致です")
    outcomes = {c["id"]: simulate(c, data["scope"]) for c in data["cases"]}
    for key, outcome in outcomes.items():
        equal_result(outcome, oracle[key])

    # 想定外の条件を、成功のように処理しないことを確認する。
    refused = []
    base = data["cases"][1]
    def refusal(label, change_case=None, change_scope=None):
        case, scope = deepcopy(base), deepcopy(data["scope"])
        if change_case:
            change_case(case)
        if change_scope:
            change_scope(scope)
        try:
            simulate(case, scope)
        except ValueError:
            refused.append(label)
        else:
            raise AssertionError("期待した拒否が発生しない: " + label)

    for key, value in (("prune_last", True), ("dry_run", True), ("prune", False), ("hooks", True)):
        refusal(key, change_scope=lambda s, k=key, v=value: s.update({k: v}))
    refusal("unknown-scope-field", change_scope=lambda s: s.update(extra=False))
    refusal("boolean-wave", lambda c: c["tasks"][0].update(wave=True))
    refusal("duplicate-id", lambda c: c["tasks"][1].update(id="high"))
    refusal("unknown-action", lambda c: c["tasks"][0].update(action="delete"))
    refusal("missing-observation-before-later-wave", lambda c: c["tasks"][0].update(observation="unobserved"))
    refusal("multiple-prunes-same-wave", lambda c: c["tasks"][1].update(wave=8))
    refusal("failure-with-inferred-absence", lambda c: c["tasks"][0].update(result="SyncFailed"))
    refusal("empty-tasks", lambda c: c.update(tasks=[]))

    # これは出力改変の検出。upstreamや模型コードへのmutation testとは区別する。
    changed = []
    def tamper(label, case_id, mutate):
        wrong = deepcopy(outcomes[case_id])
        mutate(wrong)
        try:
            equal_result(wrong, oracle[case_id])
        except AssertionError:
            changed.append(label)
        else:
            raise AssertionError("誤った出力を見逃した: " + label)

    tamper("wave-sign-negation", "prune-descending", lambda r: r.update(effective_waves={"low": 3, "mid": -1, "high": -8}))
    tamper("prune-ascending", "prune-descending", lambda r: r.update(started=["low", "mid", "high"]))
    tamper("pruned-assumed-absent", "prune-waiting", lambda r: r["results"]["high"].update(observation="absent"))
    tamper("continue-after-failure", "prune-failed", lambda r: r["started"].append("low"))
    tamper("same-wave-apply-after-prune-failure", "mixed-same-wave-failed", lambda r: r["started"].append("new"))
    return outcomes, refused, changed


def check_cli():
    checks = []
    commands = [
        ("input-before-answer", ["--case", "prune-waiting", "--view", "input"], 0),
        ("correct-prediction", ["--case", "prune-waiting", "--predict", "high", "--expect-stop", "wait", "--json"], 0),
        ("wrong-prediction", ["--case", "mixed-same-wave-failed", "--predict", "old,new", "--expect-stop", "consumed", "--json"], 0),
        ("unknown-prediction-id", ["--case", "prune-waiting", "--predict", "ghost"], 2),
    ]
    for name, args, exit_code in commands:
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "model.py"), *args],
                              capture_output=True, text=True, timeout=5)
        require(proc.returncode == exit_code, "CLI終了コード不一致: " + name)
        if name == "input-before-answer":
            require("予想 |" in proc.stdout and "模型の終端:" not in proc.stdout, "先に答えを表示した")
        elif name.endswith("prediction"):
            actual = json.loads(proc.stdout)["prediction"]
            wanted = name == "correct-prediction"
            require(actual == {"started_matches": wanted, "stop_matches": wanted}, "予想照合が不正")
        else:
            require("既存資源ID" in proc.stderr, "拒否理由なし")
        checks.append({"name": name, "arguments": args, "expected_exit": exit_code,
                       "actual_exit": proc.returncode, "pass": True,
                       "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest()})
    return checks


def main():
    parser = argparse.ArgumentParser(description="固定5ケースの軽い模型検証。通常は書込なし。")
    parser.add_argument("--record", action="store_true", help="初回だけ実行原票を新規保存。上書き禁止")
    args = parser.parse_args()
    destination = ROOT / "observations/model-check.json"
    if args.record and destination.exists():
        parser.error("実行原票が既にあります。上書きしません")
    hashes = {name: sha(ROOT / name) for name in BOUND}
    if destination.exists():
        previous = json.loads(destination.read_text())
        require(previous["artifact_sha256"] == hashes, "現在の実装と保存原票のhashが異なります。原票は変更しません")
    start = time.perf_counter()
    report = {"schema": 1, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "kind": "finite-python-model-validation", "python": platform.python_version(),
              "machine": platform.machine(), "platform": platform.system(),
              "artifact_sha256": hashes, "upstream_code_executed": False,
              "live_executed": False, "browser_executed": False, "image_qa_executed": False,
              "compiler_executed": False, "attempt": 1, "retry": 0}
    try:
        model_start = time.perf_counter()
        outcomes, refused, changed = check()
        report["model_check_seconds"] = round(time.perf_counter() - model_start, 6)
        report.update(status="pass", cases=len(outcomes), task_inputs=15,
                      outcomes=outcomes, expected_refusals=refused, altered_output_detections=changed,
                      cli_checks=check_cli())
    except Exception as exc:
        report.update(status="fail", error=f"{type(exc).__name__}: {exc}")
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["total_seconds"] = round(time.perf_counter() - start, 6)
    if args.record:
        with destination.open("x") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if report["status"] != "pass":
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    print(f"PASS: {report['cases']}ケース / 拒否{len(refused)}件 / 出力改変検出{len(changed)}件 / CLI{len(report['cli_checks'])}件")
    print(f"模型検査 {report['model_check_seconds']:.6f}秒、CLI込み {report['total_seconds']:.6f}秒。LIVE・Go・browser・画像は未実施。")
    if args.record:
        print("原票を新規保存: observations/model-check.json")


if __name__ == "__main__":
    main()
