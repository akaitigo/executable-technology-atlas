# 応答不明からのPOST再送と冪等性

[既存API契約単元](../../../subjects/api-integration-contracts/README.md)の「POSTが処理済みでも応答を受け取れない場合、再送できるか」を実行で追う継続単元。新しいSubject入口は追加しない。

合成注文の最初のPOSTをSQLiteへcommitし、HTTP responseを送る前にserverが接続を閉じる。clientは実際の `RemoteDisconnected` を受け取り、結果を **unknown** と扱う。教室で観察できるDBの事実を、そのclientが知っていたこととして扱わない。明示的な再送は1回だけ。

| 条件 | 切断後 | 再送後 | clientが受け取る再送結果 |
|---|---|---|---|
| keyなし | 業務row 1件 | 2件 | 201、新しいorder_id=2 |
| 同一key・同一body | row 1件とledger | 同じ1件 | 保存した201/bodyの再生、order_id=1 |
| 同一key・異なるbody | row 1件とledger | 同じ1件 | 409、body conflict |

この表と `oracle.json` は実行前に作成した期待値。`check.py` はproducerのhash関数を使わず固定body bytesからledger hashを照合し、SQLite原票をread-onlyで開く。業務row、ledgerの保存status/body、最初のcommitからclose・client exception・明示再送までの順序も照合する。

## 学び方と再現

Python標準libraryだけを使う。このdirectoryを作業位置にする。

```sh
python3 -B check.py
python3 -B runner.py --case same-key --inspect-evidence
python3 -B server.py
```

最初の2コマンドは保存原票の検査・閲覧。3つ目は `http://127.0.0.1:63185` の教材を起動する。各buttonは表示を切り替えるだけではなく、実HTTPConnection/HTTPServerと新しい一時DBで2回のPOSTを実行する。起動にはloopback bindの許可が必要。終了はCtrl-C。原票を更新する場合だけ `python3 -B server.py --record` または `python3 -B check.py --record` を使う。default checkerは保存ファイルを更新しない。

まずkeyなしを実行して「client exceptionでもcommit済み」を確かめ、同一key/bodyでledgerの保存結果と再送responseを比べる。最後にquantityが1→2になるbody conflictを確認する。`observations/runs.json` のUTC、環境、input、受信bytes、SQL traceと3つの `artifacts/*.sqlite` が原票。first clientに成功responseは存在しない。

## 判断する境界

業務INSERTとledger INSERTを同じ `BEGIN IMMEDIATE` / `COMMIT` に含める。ledgerだけ先に保存すると未完業務を成功として再生し、業務だけ先に保存すると再送で重複し得る。ここでは1DB内の合成rowと保存結果を同一transactionにした。外部決済や配送をこのSQLite transactionに入れたとは主張しない。

POSTというmethod名だけから自動再送の安全性は決まらない。冪等性は同じ操作の意図された効果についての性質であり、再送契約を知る必要がある。[RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)。接続切断による無応答を扱う例外は [Python http.client](https://docs.python.org/3/library/http.client.html)、transactionの開始・commit/rollbackは [SQLite](https://www.sqlite.org/lang_transaction.html) に沿う。

この教材は同じ固定keyを同じbodyで再送する局所契約を実装した。keyは1実験DB内の名前空間、期限なし。canonical JSONはこの固定schemaのsorted keysで、一般的なpayload等価性は扱わない。HTTPServerは教育用のloopback serverであり、本番用HTTP実装ではない。

## 検証状態と残る問い

3条件の実HTTP、3SQLite原票、6つの破損結果に対するoracle拒否を確認。初回にはresponse header文字列をbooleanへ変換し忘れ、oracleが拒否した。`observations/failed-first-runs.json` を残し、client adapterを修正して全条件を再実行した。通常sandboxのbind失敗も保存した。

IABの3button実操作と画面capture、readonly checker、skill routing、cleanupの詳しい結果は `observations/qa.json` と `observations/verification.json` を参照。captureのローカル保存可否はQA原票に明記する。全AtlasやSubject完了、Core audit、npm gate、commit/pushはこの単元の実施結果に含めない。

次の4つは **未実施の実験案**。現行runnerの保証や実行数に含めない。

| 問い | 次に与える入力 | 比較する観測 | 公式locatorと境界 |
|---|---|---|---|
| TTL・scope・body比較 | 仮想時計でTTL=60秒。同じkey/bodyをt=59と61秒に再送。principal A/Bで同じkey、quantity変更も比較 | 期限内の同じorder_id、期限後の再作成、principal別ledger、body conflictを区別。期限仕様を先にoracleへ固定 | [Stripe Idempotent requests](https://docs.stripe.com/api/idempotent_requests) のkey pruning・parameter comparison。Stripeの保持仕様は参考で、教材の60秒やprincipal scopeを指定する根拠ではない |
| 同時再送・複数server・障害 | 同じkey/bodyを2接続でbarrier同時送信。同じDBを使う2serverでも比較。別試行でledger INSERT前・COMMIT後にprocess停止、再起動 | row/ledger 1対1、order_id、一意制約競合、rollback後のrowなし、commit後のreplay。各fault位置と再起動原票を保存 | [SQLite §2.1 Read versus write transactions / §2.2 BEGIN modes](https://www.sqlite.org/lang_transaction.html)。1DBのwrite serializationを確認し、別DBの分散保証へ一般化しない |
| retry deadline・結果照会 | 仮想時間でdeadline=500ms、attempt timeout=100ms、backoff=50/100ms。応答喪失を注入し最大2retry、期限後は合成GET order照会へ切替 | attempt時刻・残時間・停止理由と、照会で得た業務状態。unknownで停止するケースを成功と混ぜない | [RFC 9110 §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2) のnon-idempotent再送制約。時間budget/backoff/照会APIは次案の設計で、RFC指定の数値ではない |
| 外部副作用・outbox | 合成ordersとoutboxを同一commit。workerがevent-1を送ってack前に停止。再起動後同じevent-1を送信。受信側の重複排除なし/ありを比較 | outbox状態、配信回数2と受信業務row数2/1を分ける。DB commitだけでは外部側のexactly-onceを保証できないことを追う | [AWS Transactional outbox / Issues and considerations](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) のduplicate messages・idempotent consumer。実決済を呼ばず合成receiverを使う |

画面は予想選択→実HTTP操作→正常応答の説明と切断/再送実測の比較→公式原典/実装→条件別の答えを接続する。正常応答が届く最初のPOSTは比較説明であり、新しい実行条件として数えない。導線補修のQA/source bindingsは `observations/qa-learning-path.json` と `observations/verification-learning-path.json` に保存し、旧原票を保持する。

既存単元のerror schema、ETag/conditional request、framing等の未実施範囲もそのまま残る。
