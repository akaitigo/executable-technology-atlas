---
name: atlas-messaging-event-driven-systems
description: SQLite inbox教材のcommit後ack前crash、再配送、key conflict、有限retry/DLQを保存原票と独立SQL oracleで案内する。実broker接続や本番操作には使わない。
---

# SQLite Inbox教材を案内する

教材rootはこのSkill Directoryから`../../`。まず[README](../../README.md)の実測と境界を確認する。UIは[index.html](../../index.html)、原票pointerは[observation-data.js](../../observation-data.js)。この教材以外のRepository/Harness/GoalにはRouteしない。

## 問いから選ぶ

- 「処理後・ack前crashでどうなる？」：UIのnaive-crashとinbox-crashを比較する。保存DBのeffect 2/1・残高14/7、子process exit70とcommit trace、replay時の別PID・duplicate-no-effectを原票で示す。
- 「同じIDなら処理済み？」：same-id-replayとsame-id-conflict、distinct-idを選ぶ。exact payload一致とkey契約を分け、異なるpayloadを成功扱いしない。
- 「何度retryする？」：poison-3/poison-1、transient-success/transient-exhausted。max_deliveriesは初回込み、model retryは別。DB rollbackとmodel DLQを混同しない。
- 「検算したい」：[checker.py](../../checker.py)を教材rootで`PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。保存DBのread-only SQLとhand expectationを使う。通常checkは原票更新しない。

画面は予想→入力→timeline→DB/oracle→答えの順。閲覧時は`python3 -u -m http.server 0 --bind 127.0.0.1`の表示portを使い、titleとField IDを確認する。一時server/tabは終了する。bind拒否は保持し通常審査を使い、禁止を回避しない。

再生成はユーザーが求めた場合だけ`PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`。新しいtask-owned SQLite runのみを作る。保存旧runを消さず、手書きresultや固定成功fixtureへ置換しない。

## 判断の境界

実処理はSQLite transactionと子process終了だけ。配送/ack/requeue/DLQは有限driverのモデル。end-to-end exactly-once、実broker保証、外部決済・HTTP/email effect、並行consumerや停電耐久性を成功扱いしない。`single-effect` verdictはkey単位で、distinct-idの全effect rowは2。naiveのhand expectation一致は二重effectの検出。

「本番brokerへ接続」「実DLQ redrive」「決済exactly-onceを保証」などはこの教材では未対応と答え、保存結果と未実験を分離する。外部操作を始めず、[READMEの4次実験](../../README.md)と[公式locator](../../sources.json)へ案内する。曖昧な問いは意図する境界を短く確認する。
