# 原典 / 2026-10-06

[SQLite EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html) §1.1 Table and Index Scans。raw planはnode/parent/aux/detailの4列で、SCAN/SEARCHとindex・covering・条件の情報を表示する。冒頭の注意は出力形式がreleaseで変わり得ること。本教材の有限text matcherの非一致をDB結果不正とは扱わない。

[SQLite Query Planning](https://www.sqlite.org/queryplanner.html) §1.6 Multi-Column Indices、§1.7 Covering Indexes。複合キー順と、必要な出力列もindexにあれば表への追加lookupを省ける仕組みを読む。ここではpayloadをindexへ足さず、投影列を増やす反例を観測する。原典の性能説明を、本実験の実時間/訪問pageの測定値に読み替えない。

両公式HTML本文を現在取得できた。取得不能URLなし。公開Docsは実行SQLite版の凍結source releaseではない。本文/図を複製保存しない。native本文locatorと実SQLite environmentは別証拠。

[既存LEARNING_PATH](../../../subjects/database-engine-internals/LEARNING_PATH.md) §6実験2から派生。既存wal/snapshot/upgradeや単一index式比較の原票は流用しない。
