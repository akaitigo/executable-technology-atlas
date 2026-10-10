#!/usr/bin/env python3
"""準備済みtaskのPruneLast計画だけを読む有限模型。LIVE処理なし。"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SCOPE = {"prepared_tasks": True, "plan_only": True, "dependency_adjustments": False, "live_execution": False}
PHASES = {"PreSync": 0, "Sync": 1}


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(case, scope):
    require(type(scope) is dict and scope.keys() == SCOPE.keys(), "scopeの項目が不正です")
    for key, expected in SCOPE.items():
        require(type(scope[key]) is bool and scope[key] is expected, f"scope.{key} は模型外です")
    require(type(case) is dict and set(case) == {"id", "title", "global_prune_last", "tasks"}, "ケース項目が不正です")
    require(type(case["global_prune_last"]) is bool, "全体指定はboolです")
    for key in ("id", "title"):
        require(type(case[key]) is str and 0 < len(case[key]) < 200, f"{key} が不正です")
    tasks = case["tasks"]
    require(type(tasks) is list and 1 <= len(tasks) <= 5, "タスク数は1〜5です")
    ids = set()
    for task in tasks:
        require(type(task) is dict and set(task) == {"id", "phase", "kind", "action", "wave", "prune_last"}, "タスク項目が不正です")
        require(type(task["id"]) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,39}", task["id"]), "IDが不正です")
        require(task["id"] not in ids, "ID重複です")
        ids.add(task["id"])
        require(type(task["phase"]) is str and task["phase"] in PHASES, "今回はPreSync/Syncだけです")
        require(type(task["wave"]) is int and -100 <= task["wave"] <= 100, "waveは範囲内の整数です")
        require(type(task["kind"]) is str and task["kind"] in ("Job", "ConfigMap"), "kindが模型外です")
        require(type(task["action"]) is str and task["action"] in ("apply", "prune"), "actionが不正です")
        require(type(task["prune_last"]) is bool, "資源単位指定はboolです")
        require(task["action"] != "prune" or task["phase"] == "Sync", "今回はSyncのpruneだけです")


def groups(tasks, waves):
    # 同phase/wave内のidsは集合の表示用。完了順を表さない。
    result = []
    for phase, wave in sorted({(t["phase"], waves[t["id"]]) for t in tasks}, key=lambda v: (PHASES[v[0]], v[1])):
        result.append({"phase": phase, "wave": wave,
                       "ids": sorted(t["id"] for t in tasks if t["phase"] == phase and waves[t["id"]] == wave)})
    return result


def plan(case, scope):
    validate(case, scope)
    tasks = case["tasks"]
    prune_waves = sorted({t["wave"] for t in tasks if t["action"] == "prune"})
    swapped = dict(zip(prune_waves, reversed(prune_waves)))
    ordinary = {t["id"]: swapped[t["wave"]] if t["action"] == "prune" else t["wave"] for t in tasks}
    # syncPhaseLastWave := 0 を保持。applyだけでなくpruneも含める。
    sync_max = max([0] + [ordinary[t["id"]] for t in tasks if t["phase"] == "Sync"])
    candidate = sync_max + 1
    selected = sorted(t["id"] for t in tasks if t["action"] == "prune" and (case["global_prune_last"] or t["prune_last"]))
    final = {name: candidate if name in selected else wave for name, wave in ordinary.items()}
    return {"ordinary_waves": ordinary, "sync_max": sync_max, "last_wave_candidate": candidate,
            "selected": selected, "final_waves": final, "phases": {t["id"]: t["phase"] for t in tasks},
            "before_groups": groups(tasks, ordinary), "after_groups": groups(tasks, final)}


def load_cases():
    data = json.loads((ROOT / "fixtures.json").read_text())
    require(type(data) is dict and set(data) == {"schema", "scope", "cases"} and data["schema"] == 1, "schemaが不正です")
    require(type(data["cases"]) is list and len(data["cases"]) == 5, "固定5ケースが必要です")
    require(len({c["id"] for c in data["cases"]}) == 5, "ケースIDが重複しています")
    for case in data["cases"]:
        validate(case, data["scope"])
    return data


def main():
    data = load_cases()
    cases = {c["id"]: c for c in data["cases"]}
    parser = argparse.ArgumentParser(description="PruneLastの有限計画。適用・削除・Healthは実行しません。")
    parser.add_argument("--case", choices=cases, default="global")
    parser.add_argument("--view", choices=("input", "compare"), default="compare")
    parser.add_argument("--predict-wave", type=int, help="上書き先の候補waveを予想")
    parser.add_argument("--predict-selected", help="上書き対象IDをカンマ区切りで予想。空なら対象なし")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    case = cases[args.case]
    if args.view == "input" and (args.predict_wave is not None or args.predict_selected is not None):
        parser.error("予想照合には --view compare を使ってください")
    selection = None if args.predict_selected is None else (args.predict_selected.split(",") if args.predict_selected else [])
    if selection is not None:
        if len(set(selection)) != len(selection) or not set(selection) <= {t["id"] for t in case["tasks"]}:
            parser.error("予想の対象IDが不正です")
    if args.view == "input":
        if args.json:
            print(json.dumps(case, ensure_ascii=False, indent=2))
        else:
            print(f"予想 | {case['title']}\n全体PruneLast: {case['global_prune_last']}")
            for t in case["tasks"]:
                print(f"  {t['id']:>9} {t['phase']:7} {t['action']:5} 元wave {t['wave']:>3} 資源PruneLast {t['prune_last']}")
            print("対象pruneの上書き先は？ 指定のない資源やphaseも変わる？")
        return
    outcome = plan(case, data["scope"])
    score = {}
    if args.predict_wave is not None:
        score["wave_matches"] = args.predict_wave == outcome["last_wave_candidate"]
    if selection is not None:
        score["selection_matches"] = sorted(selection) == outcome["selected"]
    if args.json:
        print(json.dumps({"case": case["id"], "outcome": outcome, "prediction": score}, ensure_ascii=False, indent=2))
        return
    print(f"対照 | {case['title']}\n固定task集合の計画だけです。実行結果・Health・削除完了は未観測です。")
    print(f"Sync最大値（初期値0）: {outcome['sync_max']} / 上書き候補wave: {outcome['last_wave_candidate']}")
    print("上書き対象: " + (", ".join(outcome["selected"]) or "なし。候補値は使わない"))
    for t in case["tasks"]:
        name = t["id"]
        print(f"  {name:>9} {t['phase']:7} 元 {t['wave']:>3} → 通常 {outcome['ordinary_waves'][name]:>3} → 指定後 {outcome['final_waves'][name]:>3}")
    for title, key in (("通常の計画", "before_groups"), ("指定後の計画", "after_groups")):
        print(title + "（同じ組の資源は完了順を表さない）")
        for group in outcome[key]:
            print(f"  {group['phase']:7} wave {group['wave']:>3}: {{{', '.join(group['ids'])}}}")
    for key, matches in score.items():
        print(f"予想照合 {key}: {'一致' if matches else '不一致。手計算表と原典を確認してください'}")
    print("phaseは保持。原典・答え・Healthの前提と限界はREADME.mdへ。")


if __name__ == "__main__":
    main()
