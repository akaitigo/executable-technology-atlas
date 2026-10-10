# Backend application engineering — 要求の途中で失敗したら何が残るか

この分野を学ぶ入口として、要求の契約、業務処理、永続化、外部通知、資源の寿命を順に結びます。今回の有限1教材は **Python stdlib + 実SQLiteの注文作成とoutbox保存** です。全Subjectの完成ではありません。

実測の結論：正常時はatomic/nonatomicどちらも注文1行・outbox1行。第二SQLでNOT NULL違反を起こすと、atomicはrollbackで両方0行、nonatomicは注文だけ1行残ります。入力拒否は接続取得前、失敗後の次の要求は新しい接続で処理し、全取得接続をcloseします。

## 前提 → 主要概念・仕組み

Pythonの関数・例外・JSON、SQLのINSERT/SELECTと主キーを知っていると読みやすくなります。Python 3.9以上の`python3`に`sqlite3`が必要です。追加pip、Docker、broker、認証、外部サービスは不要です。

バックエンドの要求は「入力を受け取る→契約を検査→業務の不変条件を守る→保存→応答」の境界を持ちます。注文には対応する送信予定が必ずある、という不変条件を本教材の問いにします。outboxは同じDBにある**送信予定**であり、通知の実配信ではありません。

`isolation_level=None`を指定し、暗黙BEGINに依存せずSQLの`BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK`を使います。atomicは二INSERTを一transactionに含め、nonatomicは各SQLが個別に確定します。接続は要求が所有し、`finally`で閉じます。Pythonの接続context managerだけではcloseにならない点も原典で確認してください。[Python sqlite3](https://docs.python.org/3/library/sqlite3.html#how-to-use-the-connection-context-manager)、[SQLite transaction](https://www.sqlite.org/lang_transaction.html)を実装と並べて読めます。

## 今回実装 → 正常・境界・意図異常

このREADMEのあるディレクトリで実行します。

```sh
python3 runner.py                    # 保存済み原票をread-only検査
python3 runner.py --record           # 明示的に12ケースを再実行、新規原票を保存
python3 checker.py                  # handlerをimportせずhand rows + read-only SQL
python3 test_negative.py            # 原票の使い捨てcopyで欠落/改変の検出とread-onlyを確認
python3 preview.py                  # dynamic loopback URLを出力; 終了はCtrl-C
```

画面は予想→操作→比較→原典/実装→答えの順です。ケースを選択し、残る行を予想して「観測と比較」を押すと、保存済みの実実行を表示します。画面のボタンはDB処理を再実行しません。新しい実行は`--record`を使い、画面をreloadします。

| ケース | 注文 / outbox | modeled status | 学ぶこと |
|---|---|---|---|
| atomic/nonatomic 正常 | 1 / 1 | 201 | 正常だけでは境界の欠陥が見えない |
| atomic 第二SQL失敗 | 0 / 0 | 500 | 先行INSERTもrollback |
| nonatomic 第二SQL失敗 | 1 / 0 | 500 | 応答失敗でもDBは部分確定 |
| 数量1 / 100 | 1 / 1 | 201 | 許容範囲の両端 |
| 数量0 / 101 / bool、空白name | 0 / 0 | 422 | 型と業務境界を接続前に拒否 |
| 同じIDを二回 | 1 / 1 | 201, 409 | UNIQUE違反とrollback; idempotent再送応答ではない |
| atomic失敗→別IDで次要求 | bだけ1 / 1 | 500, 201 | 同一processでも前要求の接続/transactionを持ち越さない |

[service.py](service.py)が実handler、[runner.py](runner.py)が独立processの入力/出力採取、[checker.py](checker.py)が固定hand rowsと直接SQLで確認します。`SELECT id,name,quantity FROM orders ORDER BY id`と`SELECT order_id,event,payload FROM outbox ORDER BY order_id`で全行を照合します。接続は読み取り専用URI、integrity/foreign keyも検査します。

## 実務判断

正常応答だけを見て「二操作は安全」と判断しないでください。業務的に一体の書き込みは同じtransaction境界へ置き、第二操作の失敗後の**永続行**を確認できます。入力の型・範囲をDB取得前に確定し、例外が起きても資源を要求内で解放する設計をレビューできます。例外をHTTPへ変換する責任、再送後に返す結果、配信の重複排除は次の段階の判断です。

## 限界 → 次の実験

実framework/DI production/並行性能は未教材です。HTTP statusはCLIの応答モデルで、HTTP要求を受けるserverではありません。SQL失敗注入でありprocess強制停止、電源断、disk fullの実験ではありません。close済みhandleへのSELECTがProgrammingErrorになることと、次の要求が新規接続を持つことを実測しますが、全種類の例外・OS資源・pool漏れは保証しません。

分野の主要領域は[coverage.json](coverage.json)に問い・実測範囲・公式locatorを対応させています。認証/認可、domain/DI、HTTP契約、idempotency、outbox配信/saga、isolation、ORM/migration/index、cache/backpressure、observability/productionは別途必要です。

1. **N1 HTTP adapter/DI**：実要求をWSGI側から送り、例外と応答、要求ごとの接続所有を検査。次に実frameworkの依存性注入とcleanupの差を比較。
2. **N2 lock/visibility**：二process・二接続でwrite競合とtimeout、journal/WALのvisibilityを比較。性能は負荷計測してから判断。
3. **N3 再送/outbox配信**：commit後応答前停止、同一/異なるpayloadの再送、send後ack前停止を順に実験し、inboxで副作用重複を検査。
4. **N4 運用境界**：認可拒否、schema移行、依存先timeoutを小実験に分け、trace contextとエラー契約を調べる。

## 原典 → 実装 → 答え

[sources.json](sources.json)には確認日、章locator、コード/未実験とのbindingを保存しています。Pythonのtransaction controlとclose、SQLiteのimplicit/explicit transactionを読んで[service.py](service.py)の二分岐へ戻り、raw traceのBEGIN/ROLLBACK/COMMITを探してください。SQL文がtraceにあるだけでは確定の証拠にならず、oracleの最終行と照合します。SQLiteの[atomic commit](https://www.sqlite.org/atomiccommit.html)は仕組みの原典であり、本教材が電源断耐性まで測定した根拠にはしません。

答えは「atomic失敗=0/0、nonatomic失敗=1/0」。入力拒否のtraceにはBEGINもconnection-openedもなく、失敗→次要求ではcloseが次のopenに先行します。

## 実行証拠・状態

[current.json](current.json)が現原票を指し、各実行ディレクトリにUTC時刻、Python/SQLite/OS版、入力、raw stdout/stderr/SQL trace、実DB、hand oracle、source/artifact SHA-256とサイズを保存します。架空の実行値で埋めません。digestは対応関係の検査であり正しさ自体の証明ではありません。通常checkerは原票を更新せず、source変更時は失効を報告します。[QA記録](qa.json)に実IAB表示、capture保存可否、preview制約と停止の状態を残します。

ローカル限定・合成注文だけ。commit/push/公開は行いません。Portal/Core/Graphのgate完了や全分野完成は主張しません。
