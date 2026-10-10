#!/usr/bin/env python3
"""独立手追跡との照合。書込みは初回--recordだけ。"""
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
from model import evaluate, load_cases

ROOT = Path(__file__).resolve().parent
BOUND = ("fixtures.json", "hand-oracle.json", "hand-oracle-lock.json", "model.py", "verify.py", "source-review.json")


def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def model_check():
    data = load_cases()
    oracle = json.loads((ROOT / "hand-oracle.json").read_text())["cases"]
    lock = json.loads((ROOT / "hand-oracle-lock.json").read_text())
    require(lock["model_or_validator_existed"] is False, "手追跡の固定時点が不一致")
    for name, digest in lock["sha256"].items():
        require(sha(name) == digest, "固定入力/期待値の変更: " + name)
    require(set(oracle) == {c["id"] for c in data["cases"]}, "ケース集合不一致")
    outcomes = {}
    for case in data["cases"]:
        before = deepcopy(case)
        outcomes[case["id"]] = evaluate(case, data["scope"])
        require(outcomes[case["id"]] == oracle[case["id"]], "手追跡と不一致: " + case["id"])
        require(case == before, "入力変更あり")
    refused = []
    def refusal(label, mutate_case=None, mutate_scope=None):
        case, scope = deepcopy(data["cases"][1]), deepcopy(data["scope"])
        if mutate_case:
            mutate_case(case)
        if mutate_scope:
            mutate_scope(scope)
        try:
            evaluate(case, scope)
        except ValueError:
            refused.append(label)
        else:
            raise AssertionError("拒否なし: " + label)
    refusal("confirmed-string", lambda c: c.update(prune_confirmed="true"))
    refusal("predicate-string", lambda c: c["current_prunes"][0].update(requires_confirmation="false"))
    refusal("current-wave-bool", lambda c: c.update(current_wave=True))
    refusal("later-wave-not-later", lambda c: c["later_prunes"][0].update(wave=0))
    refusal("duplicate-resource-id", lambda c: c["later_prunes"][0].update(id="old-a"))
    refusal("empty-current-prunes", lambda c: c.update(current_prunes=[]))
    refusal("api-execution", mutate_scope=lambda s: s.update(api_execution=True))
    refusal("unresolved-predicate", mutate_scope=lambda s: s.update(confirmation_helper_pre_evaluated=False))
    refusal("unsupported-phase", mutate_scope=lambda s: s.update(phase="PreSync"))
    refusal("prune-disabled", mutate_scope=lambda s: s.update(prune_enabled=False))
    changed = []
    def tamper(label, case_id, mutate):
        wrong = deepcopy(outcomes[case_id]); mutate(wrong)
        require(wrong != oracle[case_id], "改変出力の見逃し: " + label)
        changed.append(label)
    tamper("wrong-blocker", "needs-confirmation", lambda r: r.update(first_blocker="old-a"))
    tamper("later-wave-blocks-current", "later-wave-only", lambda r: r.update(gate="pending", first_blocker="old-later"))
    tamper("confirmed-still-scanned", "already-confirmed", lambda r: r.update(checked_current_ids=["old-a", "old-b"]))
    tamper("partially-prune-before-confirmation", "needs-confirmation", lambda r: r.update(current_prunes_started=["old-a"]))
    tamper("gate-pass-claimed-operation-success", "no-confirmation-needed", lambda r: r.update(operation_phase="Succeeded"))
    return outcomes, refused, changed


def cli_check():
    entries = [
        ("input", ["--case", "needs-confirmation", "--view", "input"], 0),
        ("pending-readable", ["--case", "needs-confirmation", "--predict", "pending", "--predict-blocker", "old-b"], 0),
        ("later-wave-pass", ["--case", "later-wave-only", "--predict", "pass", "--predict-blocker", "none", "--json"], 0),
        ("confirmed-wrong-prediction", ["--case", "already-confirmed", "--predict", "pending", "--predict-blocker", "old-b", "--json"], 0),
        ("invalid-id", ["--predict-blocker", "ghost"], 2),
    ]
    checks = []
    for label, args, expected in entries:
        proc = subprocess.run([sys.executable, "-B", str(ROOT / "model.py"), *args], capture_output=True, text=True, timeout=5)
        require(proc.returncode == expected, "CLI exit不一致: " + label)
        if label == "input":
            require("予想 |" in proc.stdout and "ゲート: " not in proc.stdout, "予想前に答えを表示した")
        elif label == "pending-readable":
            require("最初の確認待ち: old-b" in proc.stdout and "ゲート: pending" in proc.stdout, "pending対照不一致")
            require(proc.stdout.count(": 一致") == 2, "予想一致の表示不一致")
        elif label in ("later-wave-pass", "confirmed-wrong-prediction"):
            expected_score = label == "later-wave-pass"
            require(json.loads(proc.stdout)["prediction"] == {"gate_matches": expected_score, "blocker_matches": expected_score}, "予想判定不一致")
        else:
            require("資源IDがありません" in proc.stderr, "拒否理由なし")
        checks.append({"label": label, "arguments": args, "exit_code": proc.returncode, "pass": True,
                       "stdout": proc.stdout, "stderr": proc.stderr})
    return checks


def main():
    parser = argparse.ArgumentParser(description="現在waveの確認ゲート模型。通常は書込みなし。")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(); dest = ROOT / "observations/model-check.json"
    if args.record and dest.exists():
        parser.error("原票が既にあります。上書きしません")
    hashes = {name: sha(name) for name in BOUND}
    if dest.exists():
        require(json.loads(dest.read_text())["artifact_sha256"] == hashes, "現在の実装hashと原票が不一致")
    start = time.perf_counter()
    report = {"schema": 1, "kind": "finite-current-wave-confirmation-gate", "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "artifact_sha256": hashes, "python": platform.python_version(), "machine": platform.machine(), "attempt": 1, "retry": 0,
              "upstream_executed": False, "live_executed": False, "predicate_helper_executed": False,
              "browser_executed": False, "image_qa_executed": False, "api_calls": 0}
    try:
        t = time.perf_counter(); outcomes, refused, changed = model_check()
        report["model_check_seconds"] = round(time.perf_counter() - t, 6)
        report.update(status="pass", cases=4, input_resources=16, gate_scan_visits=6, outcomes=outcomes,
                      expected_refusals=refused, altered_output_detections=changed, cli_checks=cli_check())
    except Exception as error:
        report.update(status="fail", error=f"{type(error).__name__}: {error}")
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat(); report["total_seconds"] = round(time.perf_counter() - start, 6)
    if args.record:
        with dest.open("x") as f:
            json.dump(report, f, ensure_ascii=False, indent=2); f.write("\n")
    if report["status"] == "pass":
        print(f"PASS: 4ケース/16入力資源/走査6、拒否{len(refused)}、出力改変検出{len(changed)}、CLI{len(report['cli_checks'])}")
        print(f"模型 {report['model_check_seconds']:.6f}秒、CLI込み {report['total_seconds']:.6f}秒。LIVE/helper/GUI/API実行なし。")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(1)


if __name__ == "__main__":
    main()
