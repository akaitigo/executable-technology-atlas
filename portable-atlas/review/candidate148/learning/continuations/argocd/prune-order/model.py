#!/usr/bin/env python3
"""固定教材用の境界模型。Argo CD・Kubernetesへ接続しない。"""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SCOPE = {"phase": "Sync", "kind": "ConfigMap", "prune": True,
         "dry_run": False, "prune_last": False, "confirmation_satisfied": True,
         "hooks": False, "namespace_crd_dependencies": False}
STOP_LABELS = {
    "plan-consumed": "用意した計画を消費した（全資源の消滅・Healthyは未保証）",
    "next-reconciliation-waits-for-deletion": "次のreconciliationで削除待ち。後続waveは未着手",
    "runTasks-prune-failed": "現在waveのpruneが失敗。同waveのapplyと後続waveは未着手",
}
STOP_CHOICES = {"consumed": "plan-consumed", "wait": "next-reconciliation-waits-for-deletion",
                "failed": "runTasks-prune-failed"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(case, scope):
    require(type(scope) is dict and scope.keys() == SCOPE.keys(), "scopeの項目が模型外です")
    for key, expected in SCOPE.items():
        require(type(scope[key]) is type(expected) and scope[key] == expected,
                f"scope.{key} は今回の固定条件と異なります")
    require(type(case) is dict and set(case) == {"id", "title", "question", "tasks"},
            "ケースの項目が不正です")
    for key in ("id", "title", "question"):
        require(type(case[key]) is str and 0 < len(case[key]) <= 200, f"{key} が不正です")
    tasks = case["tasks"]
    require(type(tasks) is list and 1 <= len(tasks) <= 5, "タスク数は1〜5です")
    ids = set()
    prune_waves = set()
    apply_waves = set()
    for task in tasks:
        require(type(task) is dict and set(task) == {"id", "action", "wave", "result", "observation"},
                "タスクの項目が不正です")
        name = task["id"]
        require(type(name) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,39}", name), "IDが不正です")
        require(name not in ids, "IDが重複しています")
        ids.add(name)
        require(type(task["wave"]) is int and -100 <= task["wave"] <= 100, "waveは範囲内の整数です")
        require(task["action"] in ("apply", "prune"), "actionはapply/pruneだけです")
        if task["action"] == "apply":
            require(task["result"] == "Synced", "今回apply失敗は模型外です")
            require(task["observation"] in ("ready", "unobserved"), "apply観測が不正です")
            require(task["wave"] not in apply_waves, "同waveの複数applyは今回の模型外です")
            apply_waves.add(task["wave"])
        else:
            require(task["result"] in ("Pruned", "SyncFailed"), "prune結果が模型外です")
            require(task["observation"] in ("absent", "terminating", "unobserved"), "prune観測が不正です")
            require(task["result"] != "SyncFailed" or task["observation"] == "unobserved",
                    "失敗後のlive状態は今回推定しません")
            require(task["wave"] not in prune_waves, "同waveの複数prune・並行完了順は模型外です")
            prune_waves.add(task["wave"])


def planning(case, scope):
    validate(case, scope)
    tasks = case["tasks"]
    waves = sorted({t["wave"] for t in tasks if t["action"] == "prune"})
    swapped = dict(zip(waves, reversed(waves)))
    effective = {t["id"]: swapped[t["wave"]] if t["action"] == "prune" else t["wave"] for t in tasks}
    batches = []
    for wave in sorted(set(effective.values())):
        selected = sorted((t for t in tasks if effective[t["id"]] == wave), key=lambda t: t["id"])
        batches.append({"wave": wave,
                        "prune": [t["id"] for t in selected if t["action"] == "prune"],
                        "apply": [t["id"] for t in selected if t["action"] == "apply"]})
    final_wave = batches[-1]["wave"]
    for task in tasks:
        if effective[task["id"]] != final_wave and task["result"] != "SyncFailed":
            require(task["observation"] != "unobserved", "後続waveへ進むための観測が不足しています")
    return {"declared_order": [t["id"] for t in sorted(tasks, key=lambda t: (t["wave"], t["id"]))],
            "effective_waves": effective, "batches": batches}


def simulate(case, scope):
    result = planning(case, scope)
    by_id = {t["id"]: t for t in case["tasks"]}
    result.update(started=[], results={}, unstarted=[], stop={})
    planned_ids = [name for b in result["batches"] for lane in ("prune", "apply") for name in b[lane]]

    def finish(reason, wave):
        result["unstarted"] = [name for name in planned_ids if name not in result["started"]]
        result["stop"] = {"reason": reason, "wave": wave}
        return result

    for index, batch in enumerate(result["batches"]):
        # この教材では各laneが最大1資源。並行タスクの逐次実行を装わない。
        for lane in ("prune", "apply"):
            for name in batch[lane]:
                task = by_id[name]
                result["started"].append(name)
                result["results"][name] = {"result": task["result"], "observation": task["observation"]}
                if task["result"] == "SyncFailed":
                    return finish("runTasks-prune-failed", batch["wave"])
        if index < len(result["batches"]) - 1:
            # 非最終wave後に次のreconciliationを考える観測境界。
            # pruneObject/APIを呼ばず、入力のlive観測を読んでいる。
            if any(v == {"result": "Pruned", "observation": "terminating"}
                   for v in result["results"].values()):
                return finish("next-reconciliation-waits-for-deletion", batch["wave"])
    return finish("plan-consumed", result["batches"][-1]["wave"])


def load_cases():
    data = json.loads((ROOT / "fixtures.json").read_text())
    require(type(data) is dict and set(data) == {"schema", "scope", "cases"} and data["schema"] == 1,
            "fixture schemaが不正です")
    require(type(data["cases"]) is list and len(data["cases"]) == 5, "固定5ケースが必要です")
    require(len({c["id"] for c in data["cases"]}) == 5, "ケースIDが重複しています")
    for case in data["cases"]:
        planning(case, data["scope"])
    return data


def main():
    data = load_cases()
    cases = {c["id"]: c for c in data["cases"]}
    parser = argparse.ArgumentParser(description="Argo CD固定版を読む有限模型。LIVEの実測ではありません。")
    parser.add_argument("--case", choices=cases, default="prune-descending")
    parser.add_argument("--view", choices=("input", "compare"), default="compare")
    parser.add_argument("--predict", help="始まる資源を順に入力。例 high,mid,low")
    parser.add_argument("--expect-stop", choices=STOP_CHOICES)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    case = cases[args.case]
    if args.view == "input" and (args.predict is not None or args.expect_stop is not None):
        parser.error("予想の照合には --view compare を使ってください")
    prediction = None if args.predict is None else args.predict.split(",")
    if prediction is not None:
        ids = {t["id"] for t in case["tasks"]}
        if len(set(prediction)) != len(prediction) or not set(prediction) <= ids:
            parser.error("予想は既存資源IDを重複なしで入力してください")
    if args.view == "input":
        if args.json:
            print(json.dumps(case, ensure_ascii=False, indent=2))
        else:
            print(f"予想 | {case['title']}\n{case['question']}")
            print("以下のresult/observationは教材の仮定です。未着手の資源ではまだ観測していません。")
            for t in case["tasks"]:
                print(f"  {t['id']:>5}  {t['action']:5}  元wave {t['wave']:>3}  仮定 {t['result']} / {t['observation']}")
        return
    outcome = simulate(case, data["scope"])
    scores = {}
    if prediction is not None:
        scores["started_matches"] = prediction == outcome["started"]
    if args.expect_stop is not None:
        scores["stop_matches"] = STOP_CHOICES[args.expect_stop] == outcome["stop"]["reason"]
    if args.json:
        print(json.dumps({"case": case["id"], "outcome": outcome, "prediction": scores}, ensure_ascii=False, indent=2))
        return
    print(f"対照 | {case['title']}\n模型入力の比較です。実APIの成功や消滅を測っていません。")
    print("元waveでの整列: " + " → ".join(outcome["declared_order"]))
    for t in sorted(case["tasks"], key=lambda t: t["id"]):
        print(f"  {t['id']:>5}  {t['action']:5}  元wave {t['wave']:>3} → 有効wave {outcome['effective_waves'][t['id']]:>3}")
    print("現在wave内の処理: prune → apply（空の側は飛ばす）")
    for b in outcome["batches"]:
        print(f"  有効wave {b['wave']:>3} | prune {','.join(b['prune']) or 'なし'} | apply {','.join(b['apply']) or 'なし'}")
    print("開始した資源: " + " → ".join(outcome["started"]))
    print("未着手: " + (", ".join(outcome["unstarted"]) or "なし"))
    for name, r in outcome["results"].items():
        print(f"  {name}: 結果 {r['result']} / 別の観測 {r['observation']}")
    print("模型の終端: " + STOP_LABELS[outcome["stop"]["reason"]])
    for key, matched in scores.items():
        print(f"予想照合 {key}: {'一致' if matched else '不一致。上の対照と手計算表を確認してください'}")
    print("原典・答え・実務判断・限界: README.md / hand-oracle.json / COVERAGE.md")


if __name__ == "__main__":
    main()
