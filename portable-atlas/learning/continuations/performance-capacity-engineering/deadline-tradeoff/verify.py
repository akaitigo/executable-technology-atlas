#!/usr/bin/env python3
"""Atlas：事前の手書き時間列から別方式で照合する。--recordは既存の記録の上書きを拒否。"""
import argparse
import copy
import datetime
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from model import schedule, frame, policy_order

ROOT = Path(__file__).resolve().parent
BOUND = ["fixtures.json", "hand-oracle.json", "hand-oracle-lock.json", "model.py", "verify.py", "sources.json"]


def slot_expectation(row):
    # 模型の開始/完了値を使わず、事前手書きの1tick列から最初/最後と待ちslot数を数える。
    slots = row["slots"]
    deadlines = {"A": 6, "B": 3, "C": 7}
    first = [slots.index(n) for n in "ABC"]
    finish = [max(i + 1 for i, v in enumerate(slots) if v == n) for n in "ABC"]
    wait = [sum(n not in slots[:t+1] for t in range(7)) for n in "ABC"]
    assert wait == first
    assert [slots.count(n) for n in "ABC"] == [4, 2, 1]
    assert "".join(k for k, _ in itertools.groupby(slots)) == row["order"]
    late = [end - deadlines[n] for n, end in zip("ABC", finish)]
    return {"order": row["order"], "slots": slots, "start": first, "finish": finish,
            "lateness": late, "tardiness": [max(0, t) for t in late],
            "on_time": [end <= deadlines[n] for n, end in zip("ABC", finish)],
            "missed": [n for n, end in zip("ABC", finish) if end > deadlines[n]],
            "equal_deadline": [n for n, end in zip("ABC", finish) if end == deadlines[n]],
            "sum_wait": sum(wait), "mean_wait": str(Fraction(sum(wait), 3)),
            "mean_completion": str(Fraction(sum(finish), 3)),
            "max_tardiness": max(0, *late), "makespan": len(slots)}


def slot_frame(slots, tick):
    # 時刻までの処理回数で判定。模型の累積start/finish比較を再利用しない。
    return {n: "完了" if slots[:tick].count(n) == slots.count(n) else
            "実行中" if tick < 7 and slots[tick] == n else "待ち" for n in "ABC"}


def check_output(actual, row):
    assert actual == row, (actual, row)


def check():
    began = time.perf_counter()
    oracle = json.loads((ROOT / "hand-oracle.json").read_text())
    lock = json.loads((ROOT / "hand-oracle-lock.json").read_text())
    assert hashlib.sha256((ROOT / "hand-oracle.json").read_bytes()).hexdigest() == lock["sha256"]
    assert hashlib.sha256((ROOT / "fixtures.json").read_bytes()).hexdigest() == lock["fixture_sha256"]
    assert all(v is False for v in lock["implementation_files_exist"].values())
    assert sorted(r["order"] for r in oracle["cases"]) == sorted("".join(p) for p in itertools.permutations("ABC"))
    outcomes, frames = {}, []
    for row in oracle["cases"]:
        check_output(slot_expectation(row), row)
        result = schedule(row["order"])
        check_output(result, row)
        outcomes[row["order"]] = result
        for tick in range(8):
            actual = frame(row["order"], tick)
            assert actual == slot_frame(row["slots"], tick)
            frames.append({"order": row["order"], "tick": tick, "jobs": actual})
    assert {k: policy_order(k) for k in ("fifo", "shortest", "deadline")} == {"fifo": "ABC", "shortest": "CBA", "deadline": "BAC"}
    conclusions = {"minimum_mean_wait_orders": [k for k, r in outcomes.items() if Fraction(r["mean_wait"]) == min(Fraction(s["mean_wait"]) for s in outcomes.values())],
                   "all_on_time_orders": [k for k, r in outcomes.items() if not r["missed"]],
                   "minimum_mean_wait": "4/3", "all_on_time_order_mean_wait": "8/3", "general_optimality_claim": False}
    assert conclusions == oracle["finite_conclusions"]
    refused = []
    for invalid in (None, False, 0, [], {}, "", "AB", "ABA", "ABCD", "abc"):
        try: schedule(invalid)
        except ValueError: refused.append({"kind": "order", "input": invalid})
        else: raise AssertionError("unrefused order")
    for invalid in (-1, 8, 1.5, True, "1"):
        try: frame("ABC", invalid)
        except ValueError: refused.append({"kind": "tick", "input": invalid})
        else: raise AssertionError("unrefused tick")
    try: policy_order("edf-general")
    except ValueError: refused.append({"kind": "policy", "input": "edf-general"})
    else: raise AssertionError("unrefused policy")
    alterations = []
    changes = [
        ("equality-marked-missed", "BAC", lambda r: r["on_time"].__setitem__(0, False)),
        ("shortest-claims-all-deadlines", "CBA", lambda r: r.update(missed=[])),
        ("mean-wait-confused-with-completion", "ABC", lambda r: r.update(mean_wait="17/3")),
        ("tardy-job-dropped-from-average", "CBA", lambda r: r.update(mean_wait="1/2")),
        ("negative-lateness-treated-as-tardiness", "BAC", lambda r: r["tardiness"].__setitem__(1, -1)),
        ("deadline-order-claims-less-work", "BAC", lambda r: r.update(makespan=6))]
    for label, order, change in changes:
        bad = copy.deepcopy(outcomes[order]); change(bad)
        try: check_output(bad, next(r for r in oracle["cases"] if r["order"] == order))
        except AssertionError: alterations.append(label)
        else: raise AssertionError("undetected alteration")
    return {"outcomes": outcomes, "frames": frames, "finite_conclusions": conclusions,
            "expected_refusals": refused, "altered_output_detections": alterations,
            "model_seconds": round(time.perf_counter()-began, 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument("--record", action="store_true");args = parser.parse_args()
    path = ROOT / "observations/model-check.json"
    if args.record and path.exists():
        parser.error("保存した記録が既存です。上書きしません。")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = check()
    cli = []
    for name, arguments, code, expected in [
        ("input", ["--policy", "shortest", "--view", "input"], 0, "予想"),
        ("deadline-success", ["--policy", "deadline", "--predict-all-on-time", "yes"], 0, "予想: 一致"),
        ("shortest-wrong-prediction", ["--policy", "shortest", "--predict-all-on-time", "yes"], 0, "予想: 不一致"),
        ("fifo", ["--order", "ABC", "--json"], 0, '"mean_wait": "10/3"'),
        ("invalid-order", ["--order", "ABA"], 2, "invalid choice")]:
        r = subprocess.run([sys.executable, "-B", "model.py", *arguments], cwd=ROOT, capture_output=True, text=True, timeout=5)
        assert r.returncode == code and expected in r.stdout+r.stderr
        cli.append({"name": name, "arguments": arguments, "exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr, "pass": True})
    hashes = {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in BOUND}
    record = {"kind": "finite-three-job-deadline-tradeoff", "started_at_utc": started,
              "finished_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "python": platform.python_version(), "machine": platform.machine(), "status": "pass",
              "attempt": 2, "retry": 1, "previous_failed_attempt": "observations/attempt-01-failure.json", "cases": 6, "frame_count": 48,
              "input_jobs": 18, "hand_slot_cells": 42, "source_sha256": hashes,
              "results": result, "cli_checks": cli, "browser_executed": False, "live_executed": False,
              "wall_clock_is_performance_benchmark": False, "general_edf_optimality_proven": False}
    if args.record:
        with path.open("x") as stream:json.dump(record, stream, ensure_ascii=False, indent=2);stream.write("\n")
    elif path.exists():
        saved = json.loads(path.read_text());assert saved["source_sha256"] == hashes
        for key in result:
            if key != "model_seconds":assert saved["results"][key] == result[key]
    print(json.dumps({"status": "pass", "cases": 6, "frames": 48, "refusals": len(result["expected_refusals"]),
                      "alteration_detections": len(result["altered_output_detections"]), "cli_checks": len(cli),
                      "model_seconds": result["model_seconds"], "recorded": args.record}, ensure_ascii=False))


if __name__ == "__main__":main()
