---
name: atlas-service-networking-traffic-management
description: このAtlasのvirtual-time circuit breaker/retry教材を既存runner/checker/UIで比較する。実service mesh、TLS、通信設定には使わない。
---

教材rootはこのファイルから `../..`。README.mdの時間モデルと未教材coverageを読む。
正常復帰は `python3 -B run.py`。悪例の有限比較は `run.py --recovery never`。deadline/budget境界は `--deadline 0` / `--budget 1`。独立transition/time oracleは `python3 -B check.py`。
UIは `python3 -B server.py` のloopback URLで予想→操作→状態/traffic→原典→答え。所有serverは終了する。通常checkerはread-only。原票更新の依頼がある場合だけ `check.py --record`。
未対応入力は `run.py --recovery live-service` の拒否で確認できる。実mesh/TLS/network deliveryを要求されたらREADMEのcoverageと区別する。新しいrunnerや外部設定を作らず、既存コマンドへだけrouteする。retry悪例もhard cap24callを外さない。
