# orderとlineの粒度を分ける

実SQLite・in-memoryの中立sales/order/line合成データで、指標1単位の重複集計を比較する有限1教材です。実DWH/lake/BI製品を実行した証拠ではありません。

## 指標と結果

**指標**：lineが1件以上あるorderの、既知amountの合計。1行=1 order、amountは合成整数単位（実会計の売上ではない）。NULLは除外して欠損件数を併記し、既知0・全NULL・対象なしを区別します。

order1=100（line2件）、order2=100（line1件）、order3=80（未知customer）、order4=NULL（NULL customer）、order5=50（lineなし・対象外）、order6=0。手集計は100+100+80+0=280、対象5/既知4/欠損1。

| 実SQL方式 | 結果 | 比較の意味 |
| --- | --- | --- |
| naive JOIN | 6入力行 / SUM=380 | order1のamount100をline数だけ複製する意図異常 |
| lineをorder別preaggregate | 5入力行 / SUM=280 | order grainへ戻して集計 |
| EXISTSによるsemi-join | 5入力行 / SUM=280 | lineの有無だけ調べる |
| SUM(DISTINCT amount) | SUM=180 | 同額の別order1/2を値として潰す意図異常 |
| LEFT dimension | north200 / UNKNOWN80 / south0 / NULL bucketのSUM=NULL | 未知keyとNULL keyを残す |
| INNER dimension | north200 / south0 | 未知/NULL keyのorderを黙って落とす意図異常 |
| 全NULL / 空集合 | どちらもSUM=NULL、TOTAL=0.0 | input_rows=1/0、missing_rows=1/0で区別 |

## 学習の道筋

1. **前提**：SELECT/JOIN/SUMとIDの多重度。粒度（grain）は「1行が表す測定」で、単にprimary keyの一覧ではありません。[Fact Tablesの著者原典](https://www.kimballgroup.com/2008/11/fact-tables/)の「Stay True to the Grain」を読む。
2. **仕組み**：order amountがline粒度に複製されることを、画面のorder→line→集計入力で確認。同額100が別orderであることも追う。
3. **実装と正常/異常**：予想→naiveの380→preaggregate/EXISTSの280→DISTINCTの180→dimension/NULL/emptyの順に比較。[全SQL](queries.json)と[runner](experiment.py)、[固定手集計Oracle](verify.py)へ戻る。
4. **実務判断**：指標の対象・grain・欠損規則を先に定める。集計前のID多重度、消えたorder、NULLと既知0を検査する。この指標ではpreaggregate/EXISTSが適合するが、line amountを測る別指標では別grainが必要。結果が同じでも性能の優劣はここから判断できない。
5. **限界→原典**：[SQLite SELECT](https://sqlite.org/lang_select.html)のJOIN処理、[SUM/COUNT/DISTINCT](https://sqlite.org/lang_aggfunc.html)、[EXISTS](https://sqlite.org/lang_expr.html#the_exists_operator)を照合。未知dimensionを保持するのはこの指標の設計で、全用途共通の正解ではない。

### 次の実験と主要未教材（未実施）

| 概念 | 次の有限実験案 / 問い | 公式・著者locator |
| --- | --- | --- |
| dimension履歴 / SCD Type 2 | region変更前後のorderをas-of JOIN。最新属性への単純JOINと当時の属性で合計は変わるか？ | [Slowly Changing Dimensions, Part 2](https://www.kimballgroup.com/2008/09/slowly-changing-dimensions-part-2/)、Type 2履歴 |
| data quality / orphan / NULL | 未知keyを拒否・隔離・保持する3方針で指標対象を照合。NULLと存在しないkeyは同じか？ | [SQLite Foreign Key Support](https://sqlite.org/foreignkeys.html)、有効化とNULL child key |
| incremental ETL / idempotency | 同じbatchを2回投入し、unique key＋UPSERTと単純appendの合計を比較。再実行を安全にできるか？ | [SQLite UPSERT](https://sqlite.org/lang_upsert.html)、uniqueness conflict |
| plan / 性能 / 容量 | 同じ結果のpreaggregate/EXISTSにindexを加え、plan・時間・保存量を別々に測る。少ないSQL記述が速いとは限らない。 | [EXPLAIN QUERY PLAN](https://sqlite.org/eqp.html)、Table and Index Scans |

columnar/partition、分散ETL/ELT・orchestration・streaming、catalog/lineage管理、semantic layer/BI、権限/privacy、性能容量・運用は別途未教材です。上記4本を行っても実DWH/lake/BI製品の導入判断には製品別公式資料と実runtime検証が必要です。分野全体の完成を主張しません。

## 再現と画面

このdirectoryでPython 3.9以降の標準ライブラリだけを使います。通常の2 commandは保存原票を読むだけです。

```sh
python3 -B verify.py
python3 -B observe.py
```

原票更新を意図する時だけ：

```sh
python3 -B observe.py --write-evidence
```

8 SQL方式（relation+metricで16 SELECT）の結果を実SQLiteで取得。検査器はSQLite/runnerをimportせず、固定手集計の行・値・lineageへ照合します。実行＋Oracleが通った候補のみdirectory renameで公開し、swap失敗は直前成功へrollback。

```sh
python3 -B test_contract.py
python3 -m http.server 0 --bind 127.0.0.1
```

表示された自分の動的portを開き、方式→SUMの予想→lineageと答え→order選択で複製/欠落→原典/実装へ戻る。画面は原票再生で新SQLを実行しません。終了は自分のserverでCtrl-C。他担当のlistenerを停止しないでください。

実SQL/rows/metric/grainは`evidence/stdout.json`、時刻/runtime/inputと12 source digestは`evidence/run.json`、Artifact digest/bytesは`evidence/artifacts.json`。一次資料は[locator metadata](sources.json)のみで第三者本文/画像は保存しません。[QA](QA.md)、[coverage](COVERAGE.md)、[専用Skill](skills/atlas-analytics-data-platform/SKILL.md)も参照してください。
