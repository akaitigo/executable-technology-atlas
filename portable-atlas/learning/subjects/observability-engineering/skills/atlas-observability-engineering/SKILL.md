---
name: atlas-observability-engineering
description: この有限教材の実ローカルrequestを実行してlogs・親child spans・counterと伝播欠落を比較する。分散backend、OTel適合、実運用監視は対象外。
---

rootはこのファイルから`../..`。README.mdとfixture.jsonを読み、予想→操作→比較→原典/実装→答えへ案内する。

- runner：rootで`python3 -B runner.py --case missing-propagation`。caseはsuccess、error、missing-propagation、error-orphan、batch、upper-bound、zero-units、unexpected-key、unexpected-value。
- checker：`python3 -B checker.py`がread-only。原票更新を明示されたときだけ`--record`。
- UI：`python3 -B server.py`の専用動的loopback URL。実traceとrawのbindingを見て専用serverを終了する。
- 分散backend導入、OTel SDKインストール、外部export、実incident、SLO全体評価は未対応。READMEの未教材coverageとsources.jsonへ案内する。他Subject・旧repo・harnessへrouteしない。

scenario oracle PASSとbindingCompleteを区別する。orphanは意図した欠落でありresponse成功から観測完全性を主張しない。実duration値を固定期待値や製品performance評価にしない。
