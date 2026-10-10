# WAL reader snapshot と checkpoint

元database-engine-internalsの[学習経路・実験4](../../../subjects/database-engine-internals/LEARNING_PATH.md)を実行する独立continuation。元のquery planでは「同じ16行でもアクセス計画が違う」を観察した。この単元は、writerがCOMMITしてもreaderの可視値がいつ変わるか、WALをDBへ反映できるかを分けて読む。元SubjectとPortalは変更していない。

## 予測 → 操作 → 比較

`python3 preview.py` が表示する専用loopback URLで `index.html` を開く。reader値とcheckpoint完了を予測し、「観測と比較」。6手順を選び、時点を切り替える。SQL、接続、transaction状態、返値、WAL byte数・物理frameをrawで照合する。UIは保存観測を読むだけでDBへ書き込まない。

|手順|reader保持中→終了後|保持中 checkpoint|終了後 checkpoint|
|---|---|---|---|
|PASSIVE|10→20|[0,1,0]|[0,1,1]|
|FULL|10→20|[1,1,0]|[0,1,1]|
|TRUNCATE|10→20|[1,1,0]|[0,0,0]|
|BEGINだけ、最初のSELECTはwriter後|20→20|[0,1,1]|[0,1,1]|
|writer ROLLBACK|10→10|[0,0,0]|[0,0,0]|
|2回 writer COMMIT|10→30|[0,2,0]|[0,2,2]|

返値は `[busy, log, checkpointed]`。PASSIVEの先頭0は全frameの反映を意味しない。保持中の[0,1,0]では1 frameが未反映。終了後のPASSIVE/FULLは全frame反映してもWALサイズ4152 bytesを残した。TRUNCATEは0 bytesへ切り詰めた。物理frame数はファイル構造の観測で、一般に現在のactive log数と同じとは限らない。本fixtureではbaseline TRUNCATE後に1行を更新する固定条件なので独立literal oracleで1／2 frameを照合する。

## 証拠と再現

- [現在のrun](CURRENT)に保存先。各runの`result.json`と`stdout.ndjson`に実SQL全件と返値・UTC、`command.json`にrecord実行、`artifacts.json`にbytes/SHA256。
- 6ケースそれぞれ専用DBを2接続で順次操作。`journal_mode=WAL`、`wal_autocheckpoint=0`、`busy_timeout=50`、`synchronous=FULL`を設定。実SQLite/Python版、source ID、compile optionsを保存。50msは設定値であり経過時間測定ではない。
- 各非空WALをその時点のバイト列として保存。writer操作完了後の逐次読み出しで、復旧可能なbackupやcrash耐性の証拠とはしない。`closed.sqlite`はreader/writer両方を終了した実DB。
- `python3 runner.py` または `python3 checker.py` は保存済み証拠だけをread-only照合。checkerはSQL順序・役割・literal値・checkpoint進捗を独立定義し、記録SQLを再実行しない。最後のDBだけ `mode=ro&immutable=1` とquery_onlyでSELECTする。
- [runner実装](runner.py)と[独立checker実装](checker.py)を閲覧して、rawのSQL／literal契約と比較する。
- **新規観測を明示指定するときだけ** `python3 runner.py --record`。UTCの新規ディレクトリを作り、以前のrawを保つ。CURRENTのみ新runへ更新する。
- `python3 test_negative.py` は原記録のSHA256とmtime_ns不変を確認し、一時コピーでraw/derived/indexを整合させた7種類の誤りを独立oracleが拒否することを確認する。
- [QA実行記録](QA.json)、[到達範囲](COVERAGE.md)、[module Skill](skills/wal-snapshot-checkpoint/SKILL.md)。`python3 route.py inspect|lesson|record`。未知routeはexit 2。

## 前後の学習

[元query plan単元](../../../subjects/database-engine-internals/README.md)から、検索経路と可視値／storage進捗を分ける。[SQL transactionの学習経路](../../../subjects/relational-database-sql/LEARNING_PATH.md)を前提にする。[window frame / peer単元](../../relational-database-sql/window-frames-peers/README.md)は同じSELECT内の論理行集合、今回はtransactionをまたぐsnapshotの集合を扱う。

## 出典と限界

[SQLite WAL §2.1 Checkpointing・§2.2 Concurrency](https://www.sqlite.org/wal.html)のreader end markとcheckpoint制約、[PRAGMA wal_checkpoint](https://www.sqlite.org/pragma.html#pragma_wal_checkpoint)の3列と各mode、[Isolation: WAL snapshot isolation](https://www.sqlite.org/isolation.html)を参照。ここでの実測はmacOSの専用ローカルDB・単一process・2接続・1行に限る。stale readerのwriter昇格、実diagnostic code、crash recovery、NFS、Linux、速度比較、他DBへの一般化は未検証。
