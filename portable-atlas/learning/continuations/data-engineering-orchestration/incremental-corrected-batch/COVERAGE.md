# 増分と次の実験

実行済み：固定差分upsert/delete、snapshot replaceのc喪失、appendのa重複/b残留、keyed最終3件/810、同batch再適用bytes不変、未知deleteのtransaction rollback、batch内重複ID拒否、既適用ID異payload拒否、同key複数更新のlist順と非可換性。

未網羅：sourceVersion freshness guard、event time/watermark、tombstone retention／再作成、CDC connector、source offsets、ack喪失、ledger GC、複数writer、実scheduler/framework、分散exactly-once、スキーマ進化、large data、power loss。

次の有限実験（未実施）：

1. sourceVersionを比較する明示guardを追加した別fixtureで遅着更新・同version衝突と入力順を分ける。[SQLite UPSERT §2.1 validDate例](https://www.sqlite.org/lang_upsert.html)
2. delete tombstone→再作成→古いupsertを順次投入し、削除とkey再利用の世代契約を手書きで比較する。[SQLite transaction §2](https://www.sqlite.org/lang_transaction.html)
3. owned processで「DB commit後にackが失われた」を有限注入し、再送時のledger照合を比較する。production exactly-onceは別検証。[Beam event/processing time](https://beam.apache.org/documentation/programming-guide/#event-time-and-processing-time)

元coverageはread-onlyで保持。この単元はincremental corrected batch候補の有限消化であり、Core/fullGateや他Subject全体は評価しない。
