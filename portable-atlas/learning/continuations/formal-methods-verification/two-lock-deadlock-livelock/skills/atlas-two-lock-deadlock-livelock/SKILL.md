---
name: atlas-two-lock-deadlock-livelock
description: 独自有限2lockモデルのdeadlock最短traceとretry noncompletion cycleを既存runnerとUIで比較する。
---

# 案内

deadlock、retry、cycle、safety、termination、two-lockの問いは[README](../../README.md)、[UI](../../index.html)、[route](../../route.py)へ案内し、単元で`python3 verify.py`を実行する。旧rawを上書きしない。完了sinkと未完了deadlockを分け、cycle存在を公平性付き必然のstarvationと説明しない。

[原典](../../sources.json)と[coverage](../../coverage.json)へ接続する。TLC/OS lock/一般証明は未対応。依存追加/課金/global Skill/旧単元変更を行わない。
