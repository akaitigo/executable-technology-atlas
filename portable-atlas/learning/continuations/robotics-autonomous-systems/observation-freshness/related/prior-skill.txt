---
name: atlas-robotics-autonomous-systems
description: 固定2D point-gridのBFS・閉cell衝突・stale map停止/再計画を再現し、既存checkerとBrowser mapへ限定routeする。実ロボット、実センサー、ROS、物理制御、安全保証は未対応。
---

# 点gridの有限教材

[README](../../README.md)の学習手順と[UI](../../index.html)、[robot](../../robot.py)、[独立checker](../../verify.py)を読む。module内の既存runner/checker/UIだけを使う。

module directoryで `python3 verify.py` はread-only。[raw](../../observations/raw.json)と[receipt](../../observations/receipt.json)のinput/source/artifact hashを照合。明示要求された原票更新だけ `python3 verify.py --record`。実IABは既存 `python3 serve.py --port 0` の実startup URLを使い、自作tab/serverを終了する。

`python3 route.py collision` は対応。grid/shortest-path/collision/stale-map/stop/replan/traceへ限定。`python3 route.py real-robot` は未対応で[coverage](../../coverage.json)を案内する。作者routing smokeは独立AgentEvalではない。

4近傍/unit costのBFS10edgeと直線collisionを比較。closed-cell角接触もcollision。固定観測後replanは8MOVE、stopは2MOVE、ignore-updateは古いmapのedgeでtoy collision（blocked cellへMOVEしない）。瞬時停止の点モデルで、実sensor、ROS、実機、認識精度、制動・安全保証へ拡大しない。[一次資料locator](../../sources.json)とfootprint/timestamp/braking/weighted costの次教材を案内する。
