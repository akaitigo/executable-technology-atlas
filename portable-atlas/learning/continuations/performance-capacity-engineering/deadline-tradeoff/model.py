#!/usr/bin/env python3
"""Atlas：固定3仕事の累積時刻模型。通常CLIは保存した記録を変更しない。"""
import argparse
from fractions import Fraction
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = json.loads((ROOT / "fixtures.json").read_text())


def schedule(order):
    if not isinstance(order, str) or order not in FIXTURE["orders"]:
        raise ValueError("REFUSED_ORDER")
    jobs = {j["id"]: j for j in FIXTURE["jobs"]}
    clock, starts, finishes = 0, {}, {}
    for name in order:
        starts[name] = clock
        clock += jobs[name]["service"]
        finishes[name] = clock
    ids = [j["id"] for j in FIXTURE["jobs"]]
    start = [starts[name] for name in ids]
    finish = [finishes[name] for name in ids]
    lateness = [finishes[name] - jobs[name]["deadline"] for name in ids]
    tardiness = [max(0, n) for n in lateness]
    return {"order": order, "slots": "".join(name * jobs[name]["service"] for name in order),
            "start": start, "finish": finish, "lateness": lateness, "tardiness": tardiness,
            "on_time": [n <= 0 for n in lateness],
            "missed": [name for name, late in zip(ids, lateness) if late > 0],
            "equal_deadline": [name for name, late in zip(ids, lateness) if late == 0],
            "sum_wait": sum(start), "mean_wait": str(Fraction(sum(start), 3)),
            "mean_completion": str(Fraction(sum(finish), 3)),
            "max_tardiness": max(tardiness), "makespan": clock}


def policy_order(policy):
    jobs = FIXTURE["jobs"]
    if policy == "fifo":
        return "".join(j["id"] for j in jobs)
    if policy not in ("shortest", "deadline"):
        raise ValueError("REFUSED_POLICY")
    key = "service" if policy == "shortest" else "deadline"
    return "".join(j["id"] for j in sorted(jobs, key=lambda job: job[key]))


def frame(order, tick):
    if type(tick) is not int or not 0 <= tick <= 7:
        raise ValueError("REFUSED_TICK")
    result = schedule(order)
    return {name: "待ち" if tick < a else "実行中" if tick < b else "完了"
            for name, a, b in zip("ABC", result["start"], result["finish"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--order", choices=FIXTURE["orders"])
    group.add_argument("--policy", choices=["fifo", "shortest", "deadline"])
    parser.add_argument("--view", choices=["input", "compare"], default="compare")
    parser.add_argument("--predict-all-on-time", choices=["yes", "no"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    order = args.order or policy_order(args.policy or "shortest")
    if args.view == "input":
        print("予想 | 全到着0、1台、非割込み。期限ちょうどは成功。")
        for j in FIXTURE["jobs"]:
            print("{}: 長さ{} / 絶対期限{}".format(j["id"], j["service"], j["deadline"]))
        print("順序:", " → ".join(order), "平均待ちが短ければ全期限も守れる？")
        return
    result = schedule(order)
    matched = None if args.predict_all_on_time is None else (
        (args.predict_all_on_time == "yes") == (not result["missed"]))
    if args.json:
        print(json.dumps({"result": result, "prediction_matches": matched}, ensure_ascii=False, indent=2))
        return
    print("対照 |", " → ".join(order), "平均待ち", result["mean_wait"], "tick")
    for i, j in enumerate(FIXTURE["jobs"]):
        print("{}: 開始{} 完了{} / 期限{} → {}、超過{}".format(j["id"], result["start"][i],
              result["finish"][i], j["deadline"], "期限内" if result["on_time"][i] else "期限違反", result["tardiness"][i]))
    print("期限ちょうど:", ", ".join(result["equal_deadline"]) or "なし")
    if matched is not None:
        print("予想:", "一致" if matched else "不一致")
    print("模型tick。期限後も処理する有限比較で、実CPU性能・取消し・一般EDF保証ではありません。")


if __name__ == "__main__":
    main()
