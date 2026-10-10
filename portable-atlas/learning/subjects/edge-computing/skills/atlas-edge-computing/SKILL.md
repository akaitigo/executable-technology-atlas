---
name: atlas-edge-computing
description: 2node offline outbox同期とwall-clock/logical競合保持・buffer/duplicate境界を保存model原票と独立oracleで案内する。実edge端末や実network latencyの測定には使わない。
---

# offline更新の同期を案内する

教材rootはこのSkill Directoryから `../../`。[README](../../README.md)の道筋・実測限界を読み、[UI](../../index.html)で予想→保存model比較→全配送順/raw snapshot→原典/実装→答えを案内する。今回の既存runner/checker/UIだけへrouteする。

- 切断中の値は再接続でどうなるか：offline-logical / offline-wallclock。A1=20→A2=21、壁時計100→90、B1=30を全6配送順で比較。headの21/30と20、vector clock/outboxを [原票pointer](../../observation-data.js)から示す。
- 容量・重複・入力境界：buffer-one / duplicates / conflicting-duplicate / invalid-value / invalid-limit-zero / invalid-limit-bool / zero-value。write拒否とacceptedの境界、exact duplicateと同ID別payload拒否を分ける。
- 配置のcostを理解する：connected / central-connected / central-offline。cost_modelの2ms/80ms/5msは入力仮定。総直列cost174/340を実latencyや実edge性能と呼ばない。
- 保存結果を検算：教材rootで `PYTHONDONTWRITEBYTECODE=1 python3 checker.py`。[checker](../../checker.py)はread-onlyで全指定配送順・raw・source bindingを検査。[quick_validate](../../quick_validate.py)はskillの限定routeの構造検査で実モデルrouting評価ではない。
- 新原票の採取を明示依頼された場合だけ `PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record`。[runner](../../runner.py)は新runを作り成功時だけpointer更新。通常閲覧では原票更新しない。

UI閲覧は一時 `python3 -u -m http.server 0 --bind 127.0.0.1` または既存preview。title/条件/配送順/raw snapshotとcapture保存可否を確認し、owned serverを終了。bind/capture拒否は保持し通常審査を使い、禁止を別経路で回避しない。

「実edge端末へdeploy」「実network latencyを測定」「production offline耐久性を保証」はこの教材では未対応と答え、[README 次の実験E1–E4](../../README.md)と[公式locator](../../sources.json)へ案内する。外部service、新権限/設定、Core/Graph/Portal/Harness/Goalにrouteしない。in-memory model成功をdisk復旧/実同期保証へ一般化しない。曖昧な問いは必要な境界を確認し、今回から判断できることを先に示す。
