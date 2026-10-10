# SQLを、残す行と拒否する書込みから学ぶ

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存実装・原票・QA・source束縛は変更していません。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実装・未実行です。

## 1. 前提と概念の見取り図

表の行・列、ID、同じIDの参照、真偽値、件数を確認します。SQLを読む時は「1行が何を表すか」「何行残すか」「何を欠損として扱うか」を言葉にします。実装まで読む場合はPythonの関数とsqlite3のconnection/cursorが前提です。

tableとkey → SELECT/FROM → JOINの多重度 → NULLと条件 → WHERE → 集計 → 書込み制約 → transaction、の順で学びます。SQLの表や結果には重複行があり、ORDER BYなしで順序を前提にしません。NULLは0や空文字と同じ値ではなく、通常の比較でUNKNOWNを生みます。WHEREはTRUEだけを残します。

関係モデル・key・正規化はデータの意味、SQLはその操作、index/plannerは実行経路です。結果の意味と実行速度を分けて調べてください。

## 2. 既存の正常・境界・拒否を読む

[画面](index.html) → [README](README.md) → [experiment.py](experiment.py) → [raw SQL/rows](evidence/raw-results.json) → [実行identity](evidence/run.json) → [COVERAGE](COVERAGE.md)の順で辿ります。再現手順はREADMEにあり、この追補ではSQLやcheckerを実行していません。

保存fixtureはrows 3行、events 3行です。`score = NULL` は0行、`score IS NULL` はbetaの1行。INNER JOINは3行、LEFT JOINは未対応gammaを含む4行です。LEFT JOIN後にWHEREでkind='keep'を絞るとalphaの1行、ONに同じ条件を置くとbeta/gammaをNULL拡張した3行になります。

これらのSQLはそれぞれ有効です。「全rowsを保持したい」という目的に対してWHERE版が不適切になるのであり、WHERE一般が欠陥とは呼びません。NOT NULL/UNIQUE/FOREIGN KEYの不正書込みは実IntegrityErrorで拒否されています。foreign_keys=ONは同connectionで確認、UNIQUE列の複数NULLは2行残ります。

画面は保存原票の再生です。記録上のSQLite 3.51.0/Python 3.9.6に限定した観測で、他dialectの実行や現在環境での再測定ではありません。

## 3. 実務で判断できることと限界

NULL検査に通常の等号を流用しない、外部結合で残したい行を後段filterで消していないか確かめる、JOINの行数とIDの多重度を読む、制約拒否を成功へ変換しない、という判断に使えます。制約の有効化・connection・dialectを記録します。

NULLの意味や保持すべき行は業務契約で決めます。未知値を0へ変えると異なる意味になり得ます。今回だけでは正規化設計、全SQL、index/planner、transaction isolation、並行更新、migration、backup/障害回復、権限や本番性能を判断できません。SQL結果の一致を速度の優劣へ読み替えません。

## 4. 一次資料へ戻る

既存の [sources.json](sources.json) はSQLite公式の [Expressions](https://sqlite.org/lang_expr.html) §2/§14、[SELECT](https://sqlite.org/lang_select.html) §2.1/§2.3、CREATE TABLEのNOT NULL/UNIQUE、Foreign Key Supportの有効化へ対応しています。URL digestは本文を固定するhashではありません。

次の入口は公式 [Aggregate Functions](https://sqlite.org/lang_aggfunc.html) のcount/sum/total、[Window Functions](https://sqlite.org/windowfunctions.html) §2.2 Frame Specifications、[Transaction](https://sqlite.org/lang_transaction.html) §2.1 Read/Write Transactions・§2.2 DEFERRED/IMMEDIATE、[ALTER TABLE](https://sqlite.org/lang_altertable.html) のMaking Other Kinds Of Table Schema Changesです。現在の公式文書には既存runtimeより新しい機能もあり得るため、使う版の対応を別に確認します。

## 5. 未教材の具体概念と問い

| 主要未教材 | 学びたい問い | 接続 |
|---|---|---|
| 集計・GROUP BY/HAVING・NULL・DISTINCT | 件数と既知値数を区別できる？ JOIN後の集計で重複しない？ | 次案1 |
| window・partition・frame・peer | 同順位の行を1行ずつ進める計算と、まとめる計算は同じ？ | 次案2 |
| transaction・isolation・locks | 同じ値を読んだ別connectionの書込みをどう扱う？ エラー後のstateは？ | 次案3 |
| schema evolution・制約・migration | コピー途中の拒否で旧schema/dataを保持できる？ | 次案4 |
| relation・機能従属性・正規化 | 更新異常を防ぐためにどこで表を分ける？ | 専用原典・実験は未選定 |
| index・統計・planner | 同じ答えでも計画は変わる？ 速さは何で測る？ | このmoduleには計画/性能原票なし |
| CTE/recursive query・dialect | 再帰をどう停止し、版ごとの意味をどう確かめる？ | 専用実験未整備 |
| 権限・backup/recovery・運用 | 誰が何を変更でき、失敗後に何を戻せる？ | in-memory fixtureでは実証しない |

## 6. 次の4実験（未実装・未実行）

1. **NULLと集計の分母**：値列[0,NULL,10]、全NULL、空集合の3条件を固定し、COUNT(*)/COUNT(value)/SUM/TOTALを比較する。入力行数、既知値数、NULL/0/floatの結果型を別に記録し、手集計oracleへ照合する。原典locatorはAggregate Functionsのcount(X)/count(*)/sum(X)/total(X)。JOINによる増幅とGROUP BYはさらに別条件です。
2. **window frameと同順位**：id・sort_key・amountを持つ小表に同sort_keyを2行入れる。SUM OVERの既定RANGEと明示ROWSを同じ入力で比較し、各行に含まれるID集合と累積値を記録する。ROWSではORDER BY sort_key,idとして順を固定、RANGEではsort_keyだけでpeerを保つ。ORDER BY契約の違いも明記し、frameに入るIDを独立列挙する。原典locatorはWindow Functions §2.2、default frame・peerの説明。
3. **transactionの競合**：新しいtask-owned使い捨てDBへ2connectionを接続し、同じ固定statement順でBEGIN DEFERREDとBEGIN IMMEDIATEを比較する。journal mode・版・timeoutを明記し、read snapshot、write開始、busy/error、rollback後の行を保存する。成功ラベルだけで並行安全性を結論しない。原典locatorはTransaction §2.1/§2.2。実parallel thread性能、全schedule、他製品のisolationは別検証です。
4. **制約付きmigration**：小さな旧tableからNOT NULL/UNIQUEを持つ新tableへ、正常入力、NULL混入、duplicate混入を別transactionでコピーする。拒否を注入した時のrollback後schemaと全rowsを旧snapshotに照合し、成功時はID・件数・制約を検査する。index/trigger/view/foreign keyを足す場合はそれらもinventoryへ含める。原典locatorはALTER TABLEのMaking Other Kinds Of Table Schema Changes。単純なコピーだけで公式手順全体やproduction migrationを再現したとは扱いません。

4本とも新実装・独立oracle・原票が必要です。分野全体の網羅、他DBの導入判断、実運用復旧への証拠は増えていません。

## 7. 資料取得と検証の状態

2026-10-05にread-only webで上記新規4ページの本文を取得し、aggregateのNULL規則、windowのdefault frame/peer、transaction開始条件、schema変更手順のlocatorを確認しました。新規URLに取得失敗はありません。既存のExpressions/SELECT等はsourcesと既存教材の対応を読み、この追補で本文を再取得したとは主張しません。第三者本文・図・コードは転載していません。

確認したのは文書と静的リンクです。実験、runtime、実UI再QA、repository全体の完成判定は追加していません。既存証拠のhashやsource束縛は再封印していません。
