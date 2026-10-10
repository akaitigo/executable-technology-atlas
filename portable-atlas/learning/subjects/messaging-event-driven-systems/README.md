# 処理した。でもackしていない。

Field ID: `messaging-event-driven-systems`。Python stdlibとtask-owned SQLiteによる有限教材です。commit後・ack前にconsumer子processを実際に終了させ、同じeventを再び渡しました。naiveはeffect 2回・残高14、inbox keyとeffectを同じDB transactionへ保存する方式はeffect 1回・残高7でした。

配送・ack・requeue・DLQはdriverのモデルです。実brokerは起動していません。DB内のこの観測をend-to-end exactly-onceや外部決済の保証とは呼びません。

## 読む・操作する順序

1. 前提：JSON、event ID、SQL transaction、commit/rollbackを区別する。
2. 機構：[画面](index.html)でeffect row数を予想し、入力→commit/crash/replay→DBとoracle→答えの順に進む。
3. 正常と異常：normal→naive-crash→inbox-crashを比較し、same-id-conflict、poison-3、transient-successへ進む。
4. 実装：[consumer](consumer.py)のBEGIN/COMMIT/ROLLBACKと[有限driver](experiment.py)を読み、[独立checker](checker.py)で保存DBを直接検算する。
5. 実務判断：配送回数とeffect数、IDとpayload、markerとeffectのtransaction境界、初回込み総配送上限とretry回数を分ける。
6. 制約と次の実験を読み、[一次資料locator](sources.json)へ戻る。実表示確認は[QA](qa/QA.md)。

## 起動と検証

このDirectoryを作業Directoryにする。追加依存、Docker、ネットワークサービスは不要。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
node --check app.js
python3 -u -m http.server 0 --bind 127.0.0.1
```

最後のcommandが表示する動的portの`http://127.0.0.1:<port>/`をブラウザで開く。titleは「処理した。でもackしていない。 — Inbox Lab」、bodyのField IDは`messaging-event-driven-systems`。このserverは別terminalで維持し、閲覧後Ctrl-Cで終了する。通常checkerは保存済みDBを`mode=ro&immutable=1`＋`query_only`で開き、原票や画面pointerを更新しない。loopback bindが拒否された環境では失敗を保持し、通常の権限審査を使う。禁止を別手段で回避しない。

原票を新しく生成したい場合だけ、次を明示する。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
```

fresh run Directoryに14個のDBを作り、子process各5秒・outer 30秒の上限で実行する。outer attempt 1/retry 0。全条件とhand oracleが成立した場合だけ`observation-data.js`を置換し、以前のrunを保持する。optionなしのrunnerは拒否し、再生成しない。crash exit70、poison exit65、conflict exit66、rollback exit75は条件で意図した観測で、delivery command原票に残す。モデル内retryとouter再実行は別。

## 実測

[run原票](observations/20261005T063719877708Z-events/observation.json)、[outer command](observations/20261005T063719877708Z-events/command.json)、[独立oracle](observations/20261005T063719877708Z-events/oracle-report.json)、[全Artifact index](observations/20261005T063719877708Z-events/artifact-index.json)。144 indexed files（index自身を加えて145）。7 checker tests。

UTC `2026-10-05T06:37:19.940446Z`〜`2026-10-05T06:37:21.493817Z`。CPython 3.9.6 / SQLite 3.51.0 / Darwin 25.1.0 arm64。実consumerのstdoutにSQL trace・PID・commit/crash/rollback、commandにstdin/exit/stdout/stderr/time/hash、DB前後とfinal SQLiteを保存する。producerの報告を信用するだけでなく、独立hand expectationとread-only SQLを照合する。

| 条件 | effect rows | 残高 | 配送 / retry | model ack / DLQ | 判断 |
|---|---:|---:|---|---|---|
| normal | 1 | 7 | 1 / 0 | 1 / 0 | 正常 |
| naive-crash | 2 | 14 | 2 / 1 | 1 / 0 | duplicate-effectを検出 |
| inbox-crash | 1 | 7 | 2 / 1 | 1 / 0 | commit後crash、reopenしてdedup |
| same-id-replay | 1 | 7 | 2 / 0 | 2 / 0 | redelivery flagに依存しない |
| same-id-conflict | 1 | 7 | 2 / 0 | 1 / 1 | delta9を拒否、delta7を保持 |
| distinct-id | 2 | 14 | 2 / 0 | 2 / 0 | 別keyは別event |
| poison-3 | 0 | 0 | 3 / 2 | 0 / 1 | 初回込み3で停止 |
| poison-1 | 0 | 0 | 1 / 0 | 0 / 1 | retry枠なし |
| transient-success | 1 | 7 | 3 / 2 | 1 / 0 | 2 rollback後のcommitのみ残存 |
| transient-exhausted | 0 | 0 | 2 / 1 | 0 / 1 | rollback、上限で保持 |
| invalid-limit-zero | 0 | 0 | 0 / 0 | 0 / 0 | consumer前にblocked |
| invalid-limit-bool | 0 | 0 | 0 / 0 | 0 / 0 | boolをintに変換しない |
| invalid-id | 0 | 0 | 0 / 0 | 0 / 0 | 狭いevent ID schemaで拒否 |
| zero-delta | 1 | 0 | 1 / 0 | 1 / 0 | 残高0でも処理履歴1 |

oracleの`single-effect`は各event keyのeffectが1回という意味であり、distinct-idの全DB row数は2。naiveの`matches_expected: true`は期待した二重effectを観測したという意味で、idempotency成功ではない。

Source binding：

- consumer.py: `sha256:06b49b88c32f89701f829a0e64b3d4d4ee4b46a7733dfd01ef0c0a124114331f`
- experiment.py: `sha256:f9d2604ea7909ade982163df04bf2a5d5574848b8efdd08ac11818733f16b454`
- checker.py: `sha256:c8cdc15c9f249594be4a0dafee88bc4d668d57fc485b8fcd127d7cacd4a3d851`

## どこまで判断できるか

同DB内のinbox marker・payload fingerprint・effect row・balanceが同じtransactionに入るか、process終了後の再openでcommitが残るか、同ID別payloadを成功扱いしないかをこの有限入力で検査した。実ROLLBACK後はmarkerもeffectも残らない。

ACKモデル、総配送上限1..3、synthetic account、狭いID/delta schemaが教材の境界。実AMQP channel、delivery tag、publisher acceptance、queue persistence、並行consumer、OS/power failure、機器耐久性、外部HTTP/email/決済effectは未実証。inbox保持期間や業務上のkey定義も一般解ではない。

## 未教材Coverageと次の4実験

Subject全体は未完成。今の教材から次の具体的な問いへ進めるが、以下はまだ実行していない。

1. **Outbox・publish/confirm境界**：合成outboxのpersist→send→confirm各境界へcrashを入れ、欠落と重複を比較する。将来の実broker acceptanceは別実験。[Publisher Confirms](https://www.rabbitmq.com/docs/confirms#publisher-confirms)
2. **並行処理・順序・key保持**：同一keyを2consumerが同時処理し、異なるevent順やinbox期限後replayを比較する。prefetch・再接続・queue orderingの実broker保証は別。[Reliability](https://www.rabbitmq.com/docs/reliability)
3. **Poison・backoff・redrive**：有限backoffとDLQからの再投入を実装し、payload修正後のsame-ID conflictを検査する。実DLX routing/durabilityは未検証。[Dead Letter Exchanges](https://www.rabbitmq.com/docs/dlx)
4. **Log replay・offset・retention**：合成append logにcheckpoint/crash/retentionを入れ、queue再配送との違いとpartition内順序を比較する。実Streamは未起動。[Streams](https://www.rabbitmq.com/docs/streams)

routing/queue types/HA/network partitionとfailure recovery、protocol/client互換、schema/versioning、sagasと外部effect、TLS/authN/authZ、observability、throughput/capacity、backup/upgrade/運用復旧はこの4実験でも網羅しない。今回の実行をこれらの成功へ流用しない。

一次資料はlocatorとmetadataだけを[sources.json](sources.json)に保存。RabbitMQ docs 4.3はモデルの概念参照で、実RabbitMQ 4.3を走らせた記録ではない。[Automatic requeueing](https://www.rabbitmq.com/docs/confirms#automatic-requeueing)、[Python sqlite3 transaction](https://docs.python.org/3.9/library/sqlite3.html#controlling-transactions)、[SQLite Atomic Commit](https://www.sqlite.org/atomiccommit.html)。Python 3.9文書のpatch版と実runtime 3.9.6は同一ではなく、未サポートruntimeを更新したとも主張しない。
