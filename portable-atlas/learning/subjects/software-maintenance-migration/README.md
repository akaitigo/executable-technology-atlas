# Software maintenance / migration — 戻せる変更と戻せない変更

このSubjectでは、旧挙動を理解し、変更の互換性と情報保存を検査し、失敗時の復旧経路まで考えます。今回の有限1教材は **実SQLiteのstandalone table schema v1→v2 staged migration**。小さな固定dataを保つ正常経路、端数損失の悪例、未知値の拒否、copy/DROP後のrollback、commit後の逆移行を比較します。全分野の完成ではありません。

## 前提 → 主要概念・仕組み

Pythonの例外・JSONとSQLのCREATE/INSERT/SELECT/transactionが前提です。Python 3.9以上と標準`sqlite3`/`decimal`のみを使用。pip、Docker、外部サービスは不要です。

v1は`id / amount_text / state`。v2は`id / amount_cents / state_code`です。固定hand mappingは`12.30/new→1230/10`、`0.00/paid→0/20`、`1.05/new→105/10`。金額の単位とstateの意味を変換します。正常系ではcanonicalな小数2桁の文字列だけを受け、int64の非負centへ正確に写します。逆移行はcentを小数2桁へ戻し、10/20をnew/paidへ戻します。

**transaction rollback**は未commitの変更を取消します。**逆移行**はcommit済みのv2を新たなtransactionでv1へ変換します。前者が動いても後者で失われた情報を復元できるとは限りません。`1.005→100cent→1.00`は原値へ戻らない具体例です。[Python Decimal](https://docs.python.org/3/library/decimal.html)の表現/丸めと対応させてください。

移行は事前検査→`BEGIN IMMEDIATE`→新表作成→変換copy→旧表DROP→rename→user_version更新→integrity check→COMMIT。`user_version`はアプリが管理する整数で、実schemaの証明ではないため両方を検査します。[SQLite ALTER TABLE §8](https://www.sqlite.org/lang_altertable.html#otheralter)、[user_version](https://www.sqlite.org/pragma.html#pragma_user_version)が原典です。

## 今回実装 → 正常・境界・意図異常

このREADMEのあるディレクトリで実行します。

```sh
python3 runner.py                    # 保存済み原票をread-only検査
python3 runner.py --record           # 明示的に13ケース・16stepを実行、新規原票を保存
python3 checker.py                  # migratorをimportせずhand mapping + 直接SQL
python3 test_negative.py            # 使い捨てcopyで改変4種検出とread-only検査
python3 preview.py                  # dynamic 127.0.0.1 URL; 終了はCtrl-C
```

UIは予想→操作→比較→原典/実装→答えの順。caseとstepを選び、「結果はmigrated/refused/rolled-backのどれか」「元のliteral行とschemaが同じになるか」を予想します。選択step前→後のdiffと、case開始時のliteral行/schemaへ戻るかの判断を分けて表示します。保存済みの実DB原票を開く操作で、DB再実行は`--record`です。

| ケース | 実測する結果 | 判断 |
|---|---|---|
| normal-up | v2、3行がhand mappingと一致 | literal row hashは変わるが意味を保つ |
| roundtrip / empty-roundtrip | up→downでv1の行/schema hashへ戻る | 実行した逆移行の保存条件 |
| zero-boundary | 0.00→0cent、正常 | 非負金額の下限 |
| lossy-refused | 1.005をBEGIN前に拒否、旧DB無変更 | centで表せない値を黙って丸めない |
| lossy-forced-roundtrip | 悪例で1.005→100→1.00 | commit後の逆移行だけで損失を直せない |
| unknown-state-refused | refundedを拒否、旧DB無変更 | 未定義のstateを既定値にしない |
| noncanonical-refused | 01.20を拒否 | 元表記の保存が必要なら正規化でも情報損失になる |
| overflow-refused | int64最大centを1超える値を拒否 | 型容量の境界 |
| failure-after-copy / failure-after-drop | ROLLBACK、旧行/schemaへ戻る | 実transaction内のDDL/row変更の取消 |
| down-unknown-refused | v2 code30を拒否しv2を保つ | 新writerの未知値は旧stateへ戻せない |
| unsupported-version | user_version99を拒否 | metadataを無視して推測移行しない |

[migration.py](migration.py)が実移行、[runner.py](runner.py)がtask-owned DBのseedと別process実行、[checker.py](checker.py)が固定hand mappingと直接read-only SQLです。before.sqlite、after-N.sqlite、working.sqliteを閉じたwriterの後で採取します。live DB file copyや本番backupではありません。row hashはid順の全literal行、schema hashはuser_version・sqlite_schema・table_infoのcanonical JSONをSHA-256したものです。DB bytesのdigestは別に保存します。

## 実務判断

事前に「どの値を表せるか」「元表記まで戻す必要があるか」を決め、未知値を拒否するか情報を保持する列を設けるかを判断できます。raw SQLとpre/post DBを照合し、copy直後だけでなく旧表DROP後の失敗も検査できます。移行成功のexit0と、原値保存・逆移行可能性は別の条件です。row countやdigestだけを成功証明にせず、独立hand mapping、schema、全行を比較してください。

表記も保存したい01.20やcent未満を扱いたい1.005について、この教材は拒否を選びます。実データの仕様変更で正規化/丸めが認められる場合は、その決定と損失・backup経路を別途明示する必要があります。今回は悪例のlossy option以外で黙って変換しません。

## 限界 → 次の実験

production zero-downtimeと他databaseは未実行です。小さなstandalone tableとimplicit PK indexだけに限定し、追加table/view/trigger/依存indexを持つschemaは拒否します。state_codeは将来のcode30を物理的に格納できるschemaにして、逆変換時の未知値拒否を測ります。全enumをDB CHECKで保証する設計ではありません。

同時writer、lock timeout、長時間backfill、FK再作成、migration tool/ORM、disk full/電源断、backup復旧は未教材。事前読取とBEGIN後の行再照合はありますが、稼働中の旧/new clientの互換性を実証したものではありません。[Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)のexpand/migrate/contractと、今回の一transaction内のstaged copyは別の実験範囲です。

[coverage.json](coverage.json)に主要領域の具体的な問い・範囲・一次資料を対応させています。学習は旧挙動と保存条件→変換と検査→失敗/復旧→互換clientと長い移行→保守/廃止判断へ進みます。

1. **N1 old/new client**：expand/contractで両clientを動かし、cutover条件とlock停止時間を実測する。
2. **N2 backup復旧**：活性DBのBackup APIで実restoreし、逆移行・transaction rollback・restoreを比較してRPO/RTOを決める。
3. **N3 大data/依存schema**：FK/view/trigger/indexを一つずつ移し、batch中断/再開の重複・欠落と停止時間を確認する。
4. **N4 legacy/互換性**：characterization testで旧挙動を固定し、schema/API互換性を分ける。小履歴のbisectと別DBのDDL/型を独立追試する。

## 原典 → 実装 → 答え

[sources.json](sources.json)に確認日、章locator、source bindingをまとめました。SQLiteのtransactionとALTER TABLE §8を[migration.py](migration.py)のCREATE/COPY/DROP/RENAMEへ対応させ、raw traceのROLLBACK/COMMITを確認します。[SQLite Backup API](https://www.sqlite.org/backup.html)は、逆移行で戻れないときの次の学習につながります。

答え：canonicalな固定dataでは逆移行でrow/schema hashが戻ります。copy/DROP後の注入失敗はtransaction rollbackで旧schemaへ戻ります。端数を切り捨てた悪例は二stepともexit0でも原値を復元できません。未知値は無変更で拒否します。

## 原票・QA・状態

[current.json](current.json)が現実行を指します。各原票にUTC時刻・Python/SQLite/OS環境・入力・raw command/stdout/stderr・SQL trace・pre/post実DB・hand oracle・row/schema hash・source/artifact SHA-256とサイズを保存します。digestは対応関係の検査であり正しさ自体の証明ではありません。通常checkerはread-onlyで、source driftは失効を報告します。

[QA記録](qa.json)に実IAB、capture保存可否、初回loopback制約と専用server終了を記録します。ローカル限定。commit/push/公開、旧Portal/Core/Graph gate、Goal更新は今回の範囲外です。
