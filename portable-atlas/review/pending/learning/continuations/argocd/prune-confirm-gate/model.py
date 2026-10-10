#!/usr/bin/env python3
"""現在waveの確認ゲートだけ。判定helper・API・後続処理を実行しない。"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SCOPE = {"phase": "Sync", "prepared_current_wave": True, "prune_enabled": True,
         "confirmation_helper_pre_evaluated": True, "api_execution": False}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(case, scope):
    require(type(scope) is dict and scope.keys() == SCOPE.keys(), "scope項目が不正です")
    for key, expected in SCOPE.items():
        require(type(scope[key]) is type(expected) and scope[key] == expected, f"scope.{key} は模型外です")
    require(type(case) is dict and set(case) == {"id", "title", "current_wave", "prune_confirmed", "current_prunes", "current_apply_ids", "later_prunes"}, "ケース項目が不正です")
    for key in ("id", "title"):
        require(type(case[key]) is str and 0 < len(case[key]) < 200, f"{key} が不正です")
    require(type(case["prune_confirmed"]) is bool, "確認済みflagはboolです")
    require(type(case["current_wave"]) is int and -100 <= case["current_wave"] <= 100, "現在waveは範囲内の整数です")
    require(type(case["current_prunes"]) is list and 1 <= len(case["current_prunes"]) <= 4, "今回のcurrent prune数は1〜4です")
    require(type(case["current_apply_ids"]) is list and len(case["current_apply_ids"]) <= 4, "apply集合が不正です")
    require(type(case["later_prunes"]) is list and len(case["later_prunes"]) <= 4, "後続集合が不正です")
    ids = set()
    def identity(name):
        require(type(name) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name), "資源IDが不正です")
        require(name not in ids, "資源IDが重複しています")
        ids.add(name)
    for res in case["current_prunes"]:
        require(type(res) is dict and set(res) == {"id", "requires_confirmation"}, "current prune項目が不正です")
        identity(res["id"])
        require(type(res["requires_confirmation"]) is bool, "確認必要判定はboolです")
    for name in case["current_apply_ids"]:
        identity(name)
    for res in case["later_prunes"]:
        require(type(res) is dict and set(res) == {"id", "wave", "requires_confirmation"}, "後続prune項目が不正です")
        identity(res["id"])
        require(type(res["wave"]) is int and case["current_wave"] < res["wave"] <= 100, "後続waveの条件が不正です")
        require(type(res["requires_confirmation"]) is bool, "後続の確認必要判定はboolです")


def evaluate(case, scope):
    validate(case, scope)
    checked, blocker = [], None
    if not case["prune_confirmed"]:
        for resource in case["current_prunes"]:
            checked.append(resource["id"])
            if resource["requires_confirmation"]:
                blocker = resource["id"]
                break
    # この模型はゲート直後で終了。passも実行成功を表さない。
    return {"gate": "pending" if blocker else "pass", "checked_current_ids": checked,
            "first_blocker": blocker, "continue_to_prune_loop": blocker is None,
            "later_prunes_checked": [], "current_prunes_started": [], "current_apply_started": [], "api_calls": 0}


def load_cases():
    data = json.loads((ROOT / "fixtures.json").read_text())
    require(type(data) is dict and set(data) == {"schema", "scope", "cases"} and data["schema"] == 1, "schemaが不正です")
    require(type(data["cases"]) is list and len(data["cases"]) == 4, "固定4ケースが必要です")
    require(len({c["id"] for c in data["cases"]}) == 4, "ケースID重複です")
    for case in data["cases"]:
        validate(case, data["scope"])
    return data


def main():
    data = load_cases()
    cases = {case["id"]: case for case in data["cases"]}
    parser = argparse.ArgumentParser(description="現在waveの削除確認ゲート。LIVE/API操作なし。")
    parser.add_argument("--case", choices=cases, default="needs-confirmation")
    parser.add_argument("--view", choices=("input", "compare"), default="compare")
    parser.add_argument("--predict", choices=("pass", "pending"))
    parser.add_argument("--predict-blocker", help="最初の確認待ちIDを予想。なしはnone")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    case = cases[args.case]
    if args.view == "input" and (args.predict is not None or args.predict_blocker is not None):
        parser.error("予想照合には --view compare を使ってください")
    if args.predict_blocker is not None and args.predict_blocker not in {"none", *(r["id"] for r in case["current_prunes"]), *(r["id"] for r in case["later_prunes"])}:
        parser.error("予想した資源IDがありません")
    if args.view == "input":
        if args.json:
            print(json.dumps(case, ensure_ascii=False, indent=2))
        else:
            print(f"予想 | {case['title']}\n現在wave: {case['current_wave']} / 確認済みflag: {case['prune_confirmed']}")
            for res in case["current_prunes"]:
                print(f"  現在prune {res['id']}: 確認必要 {res['requires_confirmation']}")
            print("  同wave apply: " + ", ".join(case["current_apply_ids"]))
            for res in case["later_prunes"]:
                print(f"  後続wave {res['wave']} の {res['id']}: 確認必要 {res['requires_confirmation']}")
            print("ゲートは通る？ どの資源でpendingを返す？")
        return
    outcome = evaluate(case, data["scope"])
    score = {}
    if args.predict is not None:
        score["gate_matches"] = args.predict == outcome["gate"]
    if args.predict_blocker is not None:
        score["blocker_matches"] = args.predict_blocker == (outcome["first_blocker"] or "none")
    if args.json:
        print(json.dumps({"case": case["id"], "outcome": outcome, "prediction": score}, ensure_ascii=False, indent=2))
        return
    print(f"対照 | {case['title']}\nhelperの判定結果は仮定入力。API・Health・実削除は未実行です。")
    print("ゲート判定で走査した現在prune: " + (" → ".join(outcome["checked_current_ids"]) or "なし（確認済みで走査を省略）"))
    print("最初の確認待ち: " + (outcome["first_blocker"] or "なし"))
    print("ゲート: " + ("pending。prune処理の手前で戻る" if outcome["gate"] == "pending" else "pass。続きのprune処理へ進める境界"))
    print("後続waveの確認判定: 今回のゲートでは調べない")
    print("模型はゲートで終了。prune/apply/API呼出しは0、成功・失敗・消滅は未観測。")
    for key, value in score.items():
        print(f"予想照合 {key}: {'一致' if value else '不一致。現在waveと後続waveを分けて確認してください'}")
    print("原典・答え・確認と権限の違い・限界: README.mdへ")


if __name__ == "__main__":
    main()
