# DBエンジン内部を学ぶ道筋

この文書は[既存教材](README.md)を入口に、検索計画から格納・並行実行・回復へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

まずSQLのSELECT、WHERE、ORDER BY、主キー、NULL、結果の重複を説明できるようにします。集合として同じ行が返っても、重複数や順序が違えば契約を満たさない場合があります。実装を読むときはPythonのlistと`sqlite3`の接続・cursorの基本が役立ちます。

学ぶ順序は **結果の意味 → 検索計画 → indexのキー順序 → 統計と費用推定 → ページとキャッシュ → transaction・WAL・回復** です。

- 論理的に欲しい結果と、その結果を得る物理的な経路を分けます。indexの追加は答えの変更を目的にしません。
- indexの存在、条件式との適合、plannerによる採用、実行時の費用は別々の問いです。
- SCANにはindex全体の走査も含まれます。SEARCHという語だけから実時間や訪問ページ数を決められません。
- 原子性、分離性、永続性を区別します。読者に新しい値が見えることと、障害後に値が残ることは同じ検査ではありません。

## 2. 予想から既存実測へ

[UI](index.html)で3条件の計画を予想し、[実装](experiment.py)、[実行原票](evidence/stdout.json)、[環境・入力digest](evidence/run.json)を読みます。この文書作成ではSQLを再実行していません。

| 条件 | 考えておく予想 | 保存済み実測 |
|---|---|---|
| indexなし、`bucket = 7` | 絞り込みを助けるindexがない | `SCAN samples` |
| 通常indexあり、`bucket = 7` | indexを使う経路が候補になる | `SEARCH samples USING INDEX samples_bucket_idx (bucket=?)` |
| 同じindexあり、`bucket + 0 = 7` | 数学的な同値だけで同じ経路になるか | `SCAN samples` |

SQLite 3.51.0 / Python 3.9.6の256合成行で、全条件ともidが7から247まで16ずつ増える16行を返しています。正常系では計画が変わっても結果multisetと`ORDER BY id`が一致します。「式でも必ずSEARCHになる」という予想は、この原票では外れています。式のSCANはSQLエラーや結果誤りを意味しません。

READMEと[QA](QA.md)には結果欠落・重複、plan偽装、別index、版変更など9負例の拒否が記録されています。これは保存された受入記録の読解であり、今回の再検査結果ではありません。UIは原票の再生で、模式図は物理B-treeのcaptureではありません。INTEGER固定fixtureでの同値を文字列・NULL・全型へ拡張せず、性能勝利・時間倍率・WAL回復も主張しません。

## 3. 実務で何を判断するか

遅い問い合わせを調べるときは、まず正しい結果と安定した順序を確保し、実際のSQL・bind値・schema・DB版を揃えて計画を比較します。indexを増やす前に、式、複合キーの先頭列、出力列、選択度を確認します。検索に有利でも、書込みや容量の費用は増え得ます。

計画改善を性能改善として採用するには、代表的なデータ量・偏り、キャッシュ条件、同時実行、測定のばらつきを含む別の測定が必要です。永続化が要件なら、in-memory教材から判断せず、journal設定、checkpoint、バックアップ、障害条件を別途確かめます。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [SQLite EXPLAIN QUERY PLAN](https://sqlite.org/eqp.html)、§1と§1.1 Table and Index Scans | raw planの構造、SCAN/SEARCH、出力形式の版依存 |
| [SQLite Query Planning](https://sqlite.org/queryplanner.html)、§1.3、§1.5〜1.7、§2 | index検索、統計、複合・covering index、sort |
| [SQLite Indexes On Expressions](https://sqlite.org/expridx.html)、How To Use Indexes On Expressions / Restrictions | plannerが式の代数的同値を一般に解かない境界 |
| [SQLite Write-Ahead Logging](https://sqlite.org/wal.html)、§2、§2.1 Checkpointing、§2.2 Concurrency | WALのcommit、読者のsnapshot、checkpointの関係 |

既存の資料対応は[sources.json](sources.json)にもあります。資料の説明図と、保存した実SQLiteの結果を往復して読むと、原典の一般的説明をこのfixtureの測定値と混同しにくくなります。

## 5. 具体的な未教材coverage

[既存Coverage](COVERAGE.md)に加え、次の問いを残します。

| 未教材 | まだ答えられない問い |
|---|---|
| 式・複合・covering・partial index | どの条件・出力・順序を満たすindexが採用されるか |
| 統計、偏り、join順序、sort | データ分布や複数表で費用推定がどう変わるか |
| B-treeページ、buffer、I/O、圧縮 | 何ページを読み書きし、splitやcache missがいつ起きるか |
| transaction、WAL、checkpoint、障害回復 | snapshot、競合、commit境界、電源断時の保証は何か |
| 実時間・書込み費用・容量 | 改善の再現性とindex維持費をどう評価するか |
| 他エンジン・他版 | MVCCやstorage方式の違いが結果と運用へどう影響するか |

## 6. 次の実験案（4本、すべて未実行）

1. **式indexと式の一致を比較する。** 同じ256行の独立fixtureに`bucket + 0`の式indexを作り、`bucket + 0 = 7`と`0 + bucket = 7`を比較します。予想は前者がindex候補になり、交換した式は同じ扱いにならないことです。schema、raw plan、全結果を保存し、手で列挙した16件のmultisetと順序に照合します。どの計画を実際に選ぶかは版とplannerに依存するため、結果が同じでも予想と違うplanを失敗の隠蔽で処理しません。原典はIndexes On Expressionsです。

2. **出力列を増やしてcoveringの境界を見る。** 新しい作業用DBで`(bucket, label)`の複合indexを用意し、同じ条件で`SELECT bucket, label`と、indexに含まれない追加列`payload`も返す問い合わせを比較します。結果Oracleを先に固定し、raw planのcovering表示と表lookupの違いを予想します。出力列の変更に伴う答えの違いも記録し、速度や物理訪問数をplanから算出しません。原典はQuery Planning §1.6〜1.7です。

3. **偏った分布と統計の有無を比較する。** 作業用DBに2つの検索列と各単一列indexを作り、一方だけが強く絞り込む合成分布を固定します。同一SQL・bind値についてANALYZE前後のschema、統計表、plan、結果を保存します。予想は統計が候補選択に影響し得ることです。変更されない結果も受け入れ、特定index採用を成功条件にしません。全行の独立filterで答えを照合し、DB版・compile設定・分布を記録します。原典はQuery Planning §1.5です。

4. **WALの読者snapshotとcheckpointを分けて観測する。** この実験専用の使い捨てfile DBと2接続を用意し、読者がtransaction内で旧値を読んだ後に書手が更新・commitする順序を固定します。同じ読者transactionの値と、終了後の新しい読取りを比較します。読者が開いている間と閉じた後でcheckpointの返却値・WALの状態を記録し、busyや未完了も保存します。これはsnapshotとcheckpointの観測案です。process kill、電源断、媒体故障は加えず、crash recoveryや永続性の保証は未教材として残します。原典はWAL §2.1〜2.2です。

## 7. 資料の取得・検証状況

2026-10-05に上記4つのSQLite公式HTML本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。公開中のDocsであり、観測SQLite 3.51.0の凍結されたsource releaseではありません。第三者本文・図・コードは教材へ保存していません。

追加したのはこの文書だけです。runtime、checker、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
