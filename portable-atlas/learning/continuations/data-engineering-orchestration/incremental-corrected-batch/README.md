# Incremental corrected batch — 差分の更新・削除

[元data-engineering教材のcoverage.next_experiments](../../../subjects/data-engineering-orchestration/coverage.json)にあるincremental corrected batchを実SQLiteで追加する独立単元。前教材の固定batch replace／appendから、差分update/deleteの意味へ進む。元教材とPortalを変更しない。

## 前提 → 予測 → 操作 → 比較

前提はrow key、整数price、差分event、transaction。初期a100,b200,c300、訂正batchはe1:a110 upsert、e2:b delete、e3:d400 upsert。事前に[手書き期待値](expectations.json)を固定した。価格はこのfixtureの整数で、通貨換算をしない。

python3 preview.py の専用動的loopback URLを開く。caseと試行を選び、合計とexitを予測して比較する。before/after、適用順、event IDとsourceVersion、SQL/params/command/rawを照合。UIは保存済み観測を読むだけ。

|処理・条件|最終行|件数／合計|exit|
|---|---|---|---|
|差分をsnapshot replace|a110,d400（未変更c喪失）|2／510|0|
|差分をappend|a100,a110,b200,c300,d400（a重複、b残留）|5／1110|0|
|keyed upsert＋delete|a110,c300,d400|3／810|0|
|同batch再適用|同じrow、event ledger、DB bytes|3／810|0|
|途中a更新後、未知z delete|全batch rollback、初期行|3／600|2|
|batch内重複e1|全batch拒否、初期行|3／600|2|
|適用済みe1を価格999へ変更|payload衝突拒否、前回行|3／810|2|
|a110→a120（異なるID）|a120,c300,d400|3／820|0|
|a120→a110へ順序入替|a110,c300,d400|3／810|0|

8ケース・10試行。処理exit0は7、契約拒否exit2は3。replace/appendは意図的な誤比較で、exit0を差分処理の正しさと混同しない。unexpected failureはexit1で別記録。

## 契約と実務判断

row keyは対象行、event IDはevent identityと同一payload再適用の識別。sourceVersionは記録用metadataで**鮮度guardではない**。同key更新は入力list順で最後が勝つ。このため再適用idempotenceと順序入替の可換性は別。同version/different IDのdedupやlate-event freshnessは今回保証しない。

keyed modeはUNIQUE(key)を対象とするSQLite ON CONFLICT DO UPDATE、明示DELETE、applied(event_id,payload_sha)を同じtransactionに保存する。既適用IDかつ同payloadはskip。未知delete／異payload再利用では全transaction rollback。batch内のID重複はtransaction前に拒否。未知deleteのno-op方針は採用していない。既適用deleteの再送はledger skipなので未知delete拒否より前に判定する。

実務では、入力がsnapshotか差分か、delete方針、順序と鮮度、event identityの保存期間を先に定義する。ここでのローカルledgerはproduction exactly-once、CDC source、distributed frameworkの証拠ではない。

## 証拠と再現

- [CURRENT](CURRENT)のrunにinitial.json、batch-N.json、expectations.json、実worker copy、各stdout/stderr、閉じたbefore/after-N/data.sqliteを保存。result/stdout.jsonにactual command/UTC/exit/SQLとparams/order/rows、artifacts.jsonにbytes/SHA256。SQLite/Python/source ID/compile optionsも保持。
- [worker実装](worker.py)、[runner](runner.py)、[独立checker](checker.py)。checkerはproducerをimportせず手書きliteralの行・合計・件数・拒否・順序と閉じたDBを照合。保存DBはmode=ro&immutable=1/query_onlyでSELECTする。副作用SQLを再実行しない。
- python3 runner.py / checker.py / route.py inspect はread-only。新規観測を明示した場合だけ python3 runner.py --record / route.py record。UTC別runへ追記し旧rawを保つ。
- python3 test_negative.py は一時copyで7改変のraw/derived/hashを整合させたうえで独立拒否。通常経路の全ファイルSHA256/mtime_ns不変を確認する。
- [QA](QA.json)、[coverage](COVERAGE.md)、[module Skill](skills/incremental-corrected-batch/SKILL.md)。route lessonはUI位置、未知routeはexit2。個人絶対pathを記録せずsubprocess runtime pathだけ名前へ正規化する。

## 原典locatorと増分

[SQLite UPSERT §2](https://www.sqlite.org/lang_upsert.html)のconflict target / excluded値と、[Transaction §2](https://www.sqlite.org/lang_transaction.html)のBEGIN/COMMIT/ROLLBACKを確認した。[Beam Programming Guide: Event time and processing time](https://beam.apache.org/documentation/programming-guide/#event-time-and-processing-time)は次の遅着・時刻概念へのlocatorで、Beamを実行した証拠ではない。

[元batch replace/append教材](../../../subjects/data-engineering-orchestration/README.md)のbatch内dedup／snapshot置換から、訂正eventとdelete／再適用ledgerへ進む。未網羅はCDC、source connector、event time/watermark、version guard、tombstone、並列writer、ack喪失、実scheduler、大規模データ、電源断／durability。本単元もSubject/Atlas全体のcompleteではない。
