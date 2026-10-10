---
name: atlas-register-history
description: 初期0の合成単一register完了historyを有限checkerで調べ、precedence・合法候補・response-sort反例を追う。実DB監査、pending、multi-object、全実装保証には使わない。
---

教材rootはこのdirectoryから ../..。READMEのcomplete/最大4操作/値0..2/合成tickの契約を読む。

保存証拠にはrootで `python3 -B skills/atlas-register-history/route.py register-history`。独立全permutation oracleと採用rawを確認する。合法候補なしと入力拒否を分け、response順だけで判定しない。

再現は `runner.py --case overlap-read-one` または `server.py`。新原票保存は明示 `--record` のみ、通常checker/routeはread-only。実DB URLやcredentialを加えない。

real-db / pending保証等は未対応としてREADMEの未教材と次案へrouteする。合成tickを実時計測定、有限historyの許可を全実装のlinearizability証明と呼ばない。
