---
name: atlas-iot-device-connectivity
description: このAtlas合成IoT教材の切断queue、再送、device別dedup/単調性、overflowを既存runner/checker/UIで比較する。実deviceやbroker操作には使わない。
---

教材rootはこのファイルから `../..`。README.mdの比較表と未教材coverageを読む。
正常/順不同は `python3 -B run.py --capacity 6 --policy drop-oldest --order reverse --copies 2`。raw異常は `--sensor invalid-sensor`。独立timeline oracleは `python3 -B check.py`。
UIは `python3 -B server.py` のloopback URLで予想→操作→connection diagram/trace→原典→答え。所有serverは終了する。通常checkerはread-only。原票更新の依頼がある場合だけ `check.py --record`。
未対応policyは `run.py --policy persist-all` の拒否で確認する。実device/MQTT broker/firmware更新を要求されたら本教材の限界と区別しREADMEのcoverageを案内する。新たなrunnerや外部設定を作らず、既存コマンドへだけrouteする。
