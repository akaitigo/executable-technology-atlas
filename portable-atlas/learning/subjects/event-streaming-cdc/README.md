# Event Streaming / CDC — commit と checkpoint の間を読む

この有限1教材は、SQLite の実 source 変更 → commit-coupled outbox → finite consumer → materialization → offset checkpoint を追う。実測対象は合成データ・ローカル SQL・子 process の停止と再起動。実 WAL CDC、Kafka、Debezium、Flink、本番 exactly-once は未実行。この Subject 全体の完成を意味しない。

[学習画面](index.html)で **予想 → 操作 → 実 row/offset 比較 → 原典/実装 → 答え** の順に読む。画面の「保存実測を比較」は既に採取した run を表示する操作で、ブラウザ内で SQLite を再実行する操作ではない。

## 前提 → 主要概念/仕組み

SQL の INSERT/SELECT、transaction の BEGIN/COMMIT/ROLLBACK、process の終了を知っていると読みやすい。未知なら `experiment.py` のテーブル作成と SQL trace から始める。

1. **変更を記録する**：`source` は version ごとの残高履歴。`outbox` は delta イベント。delta 7, -2 から最終残高 5 を得る。source と event を同じ transaction に入れると、別 connection からは commit 前の双方が不可視となり、commit 後の双方が可視になる。単に「送信したはず」という判定では足りない。
2. **再読位置を記録する**：この教材の offset は「最後に適用した seq」。`seq > offset AND seq <= highwater` を昇順に読む。起動時に highwater を固定し、空集合を含め有限で終わる。Kafka の next record offset、partition ごとの位置、WAL LSN、SQLite WAL checkpoint はそれぞれ別物。
3. **出力を記録する**：consumer は `effects` と `materialized` を同じ transaction で commit。冪等版は event ID と exact payload の `inbox` も同じ commit に含める。その後、別 transaction で offset を保存する。
4. **停止境界を選ぶ**：出力 commit 後・offset 保存前の停止なら replay が起きる。naive は delta を2回足す。冪等版は保存済み ID/payload を照合して2回目の effect を作らない。ID の一意性は source 契約であり、異なる event を同じ ID に潰してよいという意味ではない。

transaction の動作は [SQLite Transactions §2/§3](https://www.sqlite.org/lang_transaction.html)、他 connection の可視性は [SQLite Isolation](https://www.sqlite.org/isolation.html)に対応する。consumer の位置と出力の協調という問いは [Kafka Design / Message Delivery Semantics](https://kafka.apache.org/41/design/design/)へつながる。外部 sink にはその協力が必要という仕様上の境界を、本実験の single effect と同一視しない。

## 今回実装 / 正常・境界・意図異常

表の値は独立 hand oracle の予想。実際の DB 値と raw timeline は [保存原票 pointer](observation-data.js)・画面から辿る。異常を意図通り観測したことと、業務上の整合性が保たれたことを分ける。

| 条件 | source残高 / outbox行 | offset / effect行 / sink残高 | 判断 |
|---|---|---|---|
| coupled: +7, -2 | 5 / 2 | 2 / 2 / 5 | sourceとeventが同じcommit、順にmaterialize |
| separate-source-only | 7 / 0 | 0 / 0 / 0 | source commit後に停止、通知欠落 |
| separate-event-only | 0 / 1 | 1 / 1 / 7 | event先行commit後に停止、phantom変更 |
| rollback | 0 / 0 | 0 / 0 / 0 | 同一transaction全体を取消 |
| invalid-schema | 0 / 0 | 0 / 0 / 0 | 実CHECK違反を捕捉し明示ROLLBACK |
| replay-naive | 7 / 1 | 1 / 2 / 14 | exit70→offset0から再読、二重加算 |
| replay-idempotent | 7 / 1 | 1 / 1 / 7 | exit70→再読、inboxにより追加effectなし |
| empty | 0 / 0 | 0 / 0 / 0 | highwater0、有限終了 |
| zero-delta | 0 / 1 | 1 / 1 / 0 | 残高0でもevent/effectは存在する |
| consumer-invalid-schema | 7 / 1 | 0 / 0 / 0 | payload version2を拒否、offsetを進めない |

`source-only` と `event-only` は2つの独立書込みの間の失敗を、片方の commit と明示 stop で再現する。電源断・disk fault の模擬ではない。replay条件は実子 process が `os._exit(70)` で停止し、別PIDのconsumerが saved DB を開き直す。CHECK の statement failure が自動で全 transaction を rollback したと主張しない。明示 ROLLBACK の SQL を見る。

### このPCで再現する

Python 3.9以降の標準ライブラリのみ。macOS、Dockerなし、外部接続なし。

```sh
# このREADMEのあるディレクトリで実行
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 quick_validate.py
# 明示的に新原票を作り、全条件成功時だけUI pointerを更新
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
# 表示された動的portをブラウザで開く。終了はCtrl-C
python3 -u -m http.server 0 --bind 127.0.0.1
```

通常 `checker.py` は immutable read-only SQL で保存DBを照合し、source/artifact digest、README/indexの道筋・local links・source bindingを確認。runner の無optionは書込みせず終了。`--record` だけが新runと pointer を作る。旧runは削除しない。`quick_validate.py` は skill の限定routeの構造検査で、実モデルのrouting成功を装うものではない。

[実装](experiment.py)、[runner](runner.py)、[独立checker](checker.py)、[source locator](sources.json)、[限定Skill](skills/atlas-event-streaming-cdc/SKILL.md)。独立checkerは producerをimportせず、literal tupleと実SQLで検算する。run.jsonに実行時刻・Python/SQLite/OS/architecture・source digest、各input.jsonに入力、commands.jsonに終了状態、timeline.jsonlに実SQL/境界/PID/UTC時刻、artifact-index.jsonに原票digestを保存。artifact-indexは自己参照を避け自分自身を含めない。

## 実務判断

今回から判断できること：source/eventを分離commitすると、通知欠落と実体のない通知の両方を作り得る。consumerのoffsetだけでは effect の一意性を保証できない。replayを許すなら、同じsink transaction内でID/出力を保存するか、出力/位置を原子的に保存する設計を比較する必要がある。無効schemaのoffsetを勝手に進めると損失につながるので、停止・隔離・修復・再実行の方針を別途決める。残高一致だけでイベントの有無は判定できない。

運用設計では「どのcommitに何が入るか」「再読位置の単位」「IDの寿命」「外部effectの協調」を先に書く。event ID と aggregate key を分ける出発点は [Debezium Outbox Basic outbox table](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)。本教材は1 aggregateで単一seq、並列処理も配送ネットワークもない。

## 限界と全Subjectの未教材coverage

この1教材で判定できない主要領域を、次の実験4本へ対応させる。「未完」で止めず、問い・入力・観測・原典を示す。次の実験は提案であり未実行。自動的に開始しない。

| 次の実験 | 主要未教材概念 / 問い | 小さい入力と比較する観測 | 公式 locator |
|---|---|---|---|
| E1: partitionと所有権 | key/partition ordering、consumer group、rebalance、fencing、producer idempotence。全体順序が必要か、同じpartitionを旧consumerが処理し続けたら？ | 2keys×2partitions、consumer2台、処理中rebalance。partition別offsetと重複effect、旧owner拒否、transaction abortとread_committed/read_uncommittedを比較 | [Kafka Design / Replication, Message Delivery Semantics, Using Transactions](https://kafka.apache.org/41/design/design/)・[Debezium outbox aggregateid](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) |
| E2: snapshot→log CDC | snapshot境界、WAL/LSN、replication slot、DDL/schema evolution、delete/tombstone、connector restart。初期scan中の更新は欠落・重複しないか？ | 小さいPostgreSQL表のscan中にupdate/delete、connector停止/再起動、列追加。snapshotフラグ、LSN、before/after/opと最終sinkをsourceに照合。slot retentionも観測 | [Debezium PostgreSQL / Snapshots, Streaming changes, Schema refresh modes](https://debezium.io/documentation/reference/stable/connectors/postgresql.html) |
| E3: 時間と状態 | event time/processing time、watermark、late event、window/join、keyed state、checkpoint/savepoint、backpressure。遅れて来たeventをいつ集計結果へ入れるか？ | event時刻10,12,9の到着順を変え、bounded latenessとwindowを比較。復旧前後のstate/window結果、checkpoint時間、入力lagを測る | [Flink / Event Time, Watermarks](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/time/)・[Stateful Stream Processing / Keyed State, State Persistence, Savepoints](https://nightlies.apache.org/flink/flink-docs-stable/docs/concepts/stateful-stream-processing/) |
| E4: 保持と外部sink復旧 | replay/retention/compaction、offset期限、poison record隔離、schema互換、outbox掃除、外部effect、監視/SLO、access control。sink遅延で保持期限を越えたらどう復旧するか？ | sink停止→保持/compaction→再開、schema変更とHTTP模擬effect。欠損/tombstone、lag、DLQ/redrive、outbox削除タイミング、positionとsinkを同時commitする版を比較。権限拒否も別条件 | [Kafka Design / Log Compaction Basics, Message Delivery Semantics](https://kafka.apache.org/41/design/design/)・[Debezium Outbox / Basic outbox table, Configuration Options](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) |

## 原典と答えの読み方

[source locator一覧](sources.json)の `binding` は各資料と今回の実装/未実験の接点。原典の記述は保証条件を理解する材料で、実行証拠ではない。今回の答えは「outboxでsource/eventの境界を揃え、consumerはreplayに備える」。実サービス選定、性能、耐久性、production exactly-once をこの10条件から一般化しない。

[実IAB QA / capture可否 / owned server終了](qa/README.md)にローカル画面検査を記録する。Core/Graph/Portal/harness の作業は今回対象外で、全分野の完成やCore gate成功は主張しない。
