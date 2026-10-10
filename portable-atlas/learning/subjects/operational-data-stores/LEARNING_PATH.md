# Operational data storesを学ぶ道筋

この文書は[version付きKVの既存教材](README.md)から、競合、keyの寿命、cacheとtransactionへ進むための補足です。有限教材の補足であり、KV/cache/document/graph全体の学習完了を示しません。次実験は全て未実行です。

## 1. 前提と主要概念

key/value、SQLのWHERE、更新行数、connection、autocommit、状態遷移を理解します。学ぶ順序は **読取りと更新 → lost update → version付き条件更新 → 競合時の再計算 → key lifetime → TTL/cache → transaction・durability → replicationと製品固有model** です。

valueの一致とversionの一致は違います。CASは「読んだ状態がまだ期待どおりなら更新する」条件で、拒否後に古い計算結果をそのまま再送するだけでは安全な再試行になりません。versionもkeyの削除・再作成で再利用されれば同一性を失います。

一つのUPDATE、複数statementの業務transaction、clientの再試行、分散のlinearizabilityは別に検証します。SQLite tableで作った有限KVをRedis製品や分散KVの実証へ置き換えません。

## 2. 予想から既存実測へ

[UI](index.html)、[KV API](kv.py)、[操作列](experiment.py)、[SQL原票](evidence/stdout.json)、[環境・source binding](evidence/run.json)、[artifact一覧](evidence/artifacts.json)、[QA](QA.md)を読みます。今回はSQL・checker・UIを実行していません。

| 条件 | 保存済み結果 | 学ぶ境界 |
|---|---|---|
| blind read/read/write/write | 成功2回でも最終1/version3 | 読取値0からの上書きで増分を失う |
| version CAS | A成功、Bのv1は0行、再読取り・再計算後2/v3 | 競合拒否と再試行の役割 |
| 型不正6入力 | API拒否、更新SQLなし、0/v1保持 | bool等を黙って整数化しない |
| unknown/stale | UPDATE 0行、0/v1保持 | 未存在・古いversionは作成や更新をしない |
| ABA | 0→5→0、v1→v2→v3、古いv1拒否 | valueが戻ってもversionで区別 |
| delete/recreate ABA | version1再利用、古いCAS成功、1/v2 | key lifetimeは未保護 |

「2回成功だから2になる」「valueが同じなら変更なし」「versionがあるから再作成にも安全」という予想がどのtraceで外れるかを説明します。SELECTのrowcount=-1は読取件数ではなく、rowsを読みます。UPDATEの0行はSQL構文エラーとは別です。

SQLite 3.51.0、2独立connectionのnamed shared in-memory DBで、固定順の逐次autocommitを実行した記録です。parallel thread、lock待ち、性能、disk復旧の測定ではありません。UIは保存原票の再生です。shared-cacheは教材fixtureのためで、運用推奨ではありません。

## 3. 実務で何を判断するか

更新の不変条件、keyを再利用できるか、競合時の再計算、再試行上限、業務副作用の重複を先に定めます。version不一致とbusy/timeoutは原因が違うため、同じ無条件retryへまとめません。

cacheはauthoritative storeと区別し、鮮度、TTL境界、miss時の再取得、eviction、更新順を決めます。複数keyの不変条件には単一key CASだけでは足りない場合があります。document/graphの問い合わせ、secondary index、replication、failover、durabilityは各backendで別の検証が必要です。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [SQLite UPDATE](https://sqlite.org/lang_update.html)、§2 Details | WHEREによる条件更新と0行更新 |
| [Python 3.9 sqlite3](https://docs.python.org/3.9/library/sqlite3.html)、connect / Cursor.rowcount / Controlling Transactions | connection、autocommit、行数の契約 |
| [SQLite In-Memory Databases](https://sqlite.org/inmemorydb.html)、In-memory Databases And Shared Cache | 接続共有とDB寿命 |
| [SQLite Shared-Cache Mode](https://sqlite.org/sharedcache.html)、§1.1 / §6 | fixtureと運用推奨の区別 |
| [Isolation In SQLite](https://sqlite.org/isolation.html)、Isolation And Concurrency | transaction、snapshot、busyと更新競合を分ける |

既存bindingは[sources.json](sources.json)、未教材一覧は[COVERAGE.md](COVERAGE.md)にあります。以下のgeneration/TTL/cache契約は独自の次教材案で、SQLite公式のKV製品保証ではありません。

## 5. 未教材の問い

| 未教材 | 問いと次の入口 |
|---|---|
| key再作成・世代識別 | versionの再利用をどう区別するか。実験1 |
| retry・重複業務処理 | 拒否・応答消失で何を再計算するか。実験2 |
| TTL・cache・eviction | 期限と原本の更新で古い値を返さないか。実験3、evictionは別途未実装 |
| transaction・複数key・実locking | 単一UPDATEと複数更新の不変条件はどう違うか。実験4 |
| document・graph・index | query modelと制約をどう選ぶか。別backend教材が必要 |
| replication・failover・durability・分散CAS | process/node障害時の保証は何か。現in-memory記録では未評価 |
| Redis等の製品・parallel性能 | 指定版・設定・負荷でどの契約を満たすか。製品実行なし |

## 6. 次の実験案（4本、全て未実行）

1. **key generationを条件に足す。** 独立fixtureでkey作成ごとに別の合成generation tokenを割り当て、versionだけとgeneration+versionのWHEREを比較します。delete/recreate後の古い要求を手書き状態表へ照合します。予想はversion1が同じでも世代違いを拒否することです。原典はUPDATE §2で、generationの発行・非再利用は独自契約です。分散token生成、backup復旧後の重複、永続性は未実証です。

2. **競合再試行と応答消失を比較する。** 架空increment要求を固定scheduleで競合させ、拒否後の再読取り・再計算と、古いvalue再送を比べます。別条件で成功応答を失ったclientが同じ業務要求を再送し、request IDなし/保存ありの結果を比較します。予想はCASだけでは業務重複を防げないことです。SQL trace、成功更新数、論理要求数、手書き期待値を照合します。原典の条件UPDATEとtransactionを入口にする独自modelで、exactly-once配信の保証ではありません。

3. **fake clockでTTLとcache鮮度を比べる。** 原本とcacheを独立の合成状態にし、t<expires_atのみhitと明示します。期限直前・同時・直後、原本更新、失効通知欠落、miss後の再取得を手書きtimelineへ照合します。予想はTTL内でも原本更新後のstale値があり、TTLだけで即時一致は得られないことです。SQLite UPDATEは原本更新の入口で、cache policyは独自仕様です。実clock、Redis expiration、負荷・stampede・eviction性能は測らない案です。

4. **2keyの業務不変条件をtransactionで比較する。** 独立SQLite fixtureの架空残高2行で総和一定を定め、2つのautocommit更新の途中失敗と、明示transactionのrollbackを比較します。各時点の読取結果、commit/rollback、最終総和を手書き表へ照合します。予想は単一key CASの成功だけでは複数更新を一括完了できないことです。原典はPythonのControlling TransactionsとSQLite Isolationです。busy等をversion拒否から分け、実並列locking・power loss・分散transactionへは拡張しません。

## 7. 資料取得と検証状況

2026-10-05に上記SQLite 4ページとPython sqlite3 HTML本文を取得しました。Python表示版3.9.25は既存実行版と区別します。今回取得不能のURLはありません。第三者本文、実業務データ、Credentialは保存していません。

追加はこの文書だけです。DB・checker・server・UI・global gateを実行せず、旧原票・QA・digestを更新していません。次実験の予想は新しいSQL実測ではありません。
