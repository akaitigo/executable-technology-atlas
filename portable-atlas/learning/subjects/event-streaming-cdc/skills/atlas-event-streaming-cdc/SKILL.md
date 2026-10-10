---
name: atlas-event-streaming-cdc
description: SQLite source/outbox commit と consumer offset保存前の停止・replayを、この教材の保存SQL原票と独立oracleで案内する。実WAL CDC/Kafka接続や本番操作には使わない。
---

# commit と checkpoint の教材を案内する

教材rootはこのSkill Directoryから `../../`。[README](../../README.md)の道筋・実測境界を読み、[学習UI](../../index.html)を予想→保存実測比較→SQL/timeline→原典/実装→答えの順に使う。今回のrunner/checker/UIだけへrouteする。

- source変更と通知の整合性を知りたい：coupled と separate-source-only / separate-event-only。source残高、outbox行、sink残高を比較。後2条件のhand oracle一致は異常を検出したこと。
- offset保存前の停止でどうなるか：replay-naive / replay-idempotent。実 exit70、別PID再起動、保存offset0、effect2/1、sink14/7を [原票pointer](../../observation-data.js)から読む。
- rollback/schema/空集合を知りたい：rollback / invalid-schema / consumer-invalid-schema / empty / zero-delta。SQL CHECK違反後の明示ROLLBACKと、commit済みpayload拒否を区別する。
- 保存結果を検算したい：教材rootで `PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。[checker](../../checker.py)はread-only。[quick_validate](../../quick_validate.py)は限定routeの構造検査。
- 原票を新しく採取してほしいという明示依頼：`PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`。[runner](../../runner.py)は新runを作り、成功時だけUI pointerを更新。通常閲覧で原票を更新しない。

閲覧は既存previewまたは一時的な `python3 -u -m http.server 0 --bind 127.0.0.1`。表示portで title/条件/row/offset を確認し、owned serverを終了する。bind/capture拒否は記録し、禁止を別経路で回避しない。

「実WAL CDCを読んで」「Kafka本番へ接続」「production exactly-onceを保証」は未対応と答え、今回の保存結果をその証拠にしない。[READMEの次の実験E1–E4](../../README.md)と[公式locator](../../sources.json)へ案内する。実connector、外部service、Core/Graph/Portal/Harness/Goal、global設定へrouteしない。SQLite offsetはlast-applied seqであり、Kafka next-offsetとは異なる。曖昧なら必要な境界を確認し、この教材で分かる範囲を先に示す。
