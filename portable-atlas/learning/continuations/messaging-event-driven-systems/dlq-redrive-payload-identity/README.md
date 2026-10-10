# DLQ redriveとpayload identity — 同IDの修正はいつ受理できるか

Python stdlib、実SQLite、専用consumer子processの有限教材です。poisonを仮想tick0/1/3の3attempt後にDLQへ置き、同IDを修正してtick4からredriveします。未適用の修正と、commit済みpayloadの変更を区別します。

## 前提と読む順番

JSON、ID、SQL transaction、commit/rollback、配送attemptとeffectの違いが前提。Python 3標準sqlite3のみで、broker/install/sleepはありません。

1. [元Messaging Subject](../../../subjects/messaging-event-driven-systems/README.md)のinbox/commit/ackを読む。末尾実験3「Poison・backoff・redrive」の追加単位です。
2. [事前oracle](oracle.json)で固定tick・元DLQ履歴・inbox literal・effect/残高表を予想。
3. [UI](index.html)でpoison-only→poison-corrected→committed-same→committed-changed→id-only故障版を比較。
4. [consumer](consumer.py)のinbox/effect/account transactionと[driver](driver.py)のモデルack/DLQ/redriveを分け、[checker](checker.py)の独立直接SQLへ戻る。
5. [incremental ID/payload教材](../../data-engineering-orchestration/incremental-corrected-batch/README.md)とのidentity境界を比較し、[未教材](COVERAGE.md)へ進む。

## 独自契約 → 予想 → 操作

固定ID m1、original delta="poison"。初回attemptは0,1,3、3回込みでpoison-exhaustedとしてDLQ行1を追加。redriveは同IDのみ、別generationのattemptを4,5,7で最大3回行います。成功/duplicateでmodel ack、identity-conflictは即停止し新DLQを追加。元DLQは更新・削除せず、新attempt/source_dlq・redrive row・新DLQへ結びます。

未適用poisonにはinbox marker/effectがありません。修正delta7を同IDで適用するとeffect1。commit済み対照では **tick−1に同ID/delta7を実commit** してから元poison3attemptを走らせます。型検証はinbox比較より先なので、既適用IDでもoriginal poisonはPOISONです。valid redrive7はcanonical payload一致でduplicate、redrive9はidentity-conflict。canonical JSONはid+deltaを含みます。

strict consumerはBEGIN IMMEDIATEの中でinbox/effect/accountを一緒にcommit。duplicate/conflict/poisonはrollback。id-only故障版はmarker IDの存在だけでACKし、変更payloadを見逃します。effect追加0・残高7が同じでもpayload identity成功とは扱いません。

seedはexact bool、mode strict/id-only、redriveは同IDのid/delta objectまたはnull。deltaのvalid schemaはinteger1–100、bool除外。今回は1original+1redriveまで。ID変更はconsumer前にscope拒否し、IDを変えれば業務重複を避けられるとは主張しません。

~~~sh
python3 -B runner.py --record  # 明示更新：新UTC runのみ、旧raw保持
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

previewの動的127.0.0.1 URLでredrive outcome・追加effect・残高を予想して比較。条件変更は全予想をreset。予想単独変更は新予想群を保持し、旧比較/答え/DB表示/attempt/rawを消します。拒否/実行失敗に正常答えを補いません。別terminalのpreview終了はCtrl-C。配信は専有moduleと指定元/関連READMEのみ、参照欄は原本の読み取り表示です。

[CURRENT](CURRENT)に実UTC/環境/input/exit/stdout/stderr/source・artifact hashを持つrunを記録。各attemptはinput/stdout/stderr/command.jsonを別保存。通常runner/checker/routeは読取専用。checkerはconsumer/driverをimportせず、mode=ro&immutable=1＋query_onlyの直接SQLと固定literalを照合。[QA](QA.json)に実IAB・capture・readonly hash/mtime・資源終了を記録します。

## 比較 → 原典 → 実装 → 答え

|case|inboxの事前適用|redrive|追加effect / 最終effect|残高|元DLQ / 新DLQ|
|---|---|---|---|---|---|
|poison-only|なし|なし|0/0|0|1/なし|
|poison-corrected|なし|delta7 COMMITTED|1/1|7|元1保持|
|poison-unchanged|なし|poison4/5/7で再exhaust|0/0|0|元1＋子2|
|committed-same|delta7 commit済み|delta7 DUPLICATE|0/1|7|元1保持|
|committed-changed|delta7 commit済み|delta9 CONFLICT|0/1|7|元1＋子2|
|committed-changed-id-only|delta7 commit済み|delta9 DUPLICATE_ID_ONLY / 誤ACK|0/1|7|元1保持、変更を検出しない|
|new-ID / invalid mode|未実行|scope拒否exit2|未観測|未観測|DBなし|
|malformed JSON|未実行|EXECUTION_FAILURE exit3/stdout空|未観測|未観測|DBなし|

[RabbitMQ DLX](https://www.rabbitmq.com/docs/dlx)のSafety/Dead-Lettered Effects on Messagesが一次資料です。dead-letter republishの失敗条件とmessage historyを確認する観点で参照します。SQLiteのappend-only DLQはRabbitMQのx-death形式ではありません。今回のbackoff/ack/DLQ/redriveは独自modelで、実broker routing/republish/confirmの保証を再現しません。

[独立checker](checker.py)は固定時刻、original/new DLQ、sourceリンク、inbox payload、effect件数/行、残高、各consumer exit/SQL commit・rollbackを照合します。8つのDB/原票/派生値の改変を拒否します。

答え：未適用poisonの修正には比較対象markerがないため同IDで初適用できる。一方、既適用IDには既commit payloadがあり、同payload再投入と変更payloadを分ける必要があります。DLQの存在だけで「未適用」と判断せずinboxを見ること、redriveで元履歴を消さず新attemptへ結ぶことが実務判断です。effect数だけでidentity検査や業務成功を判定しません。

## 限界

全Subject未完成。有限virtual tick・単一SQLite・単一consumer逐次実行・固定ID。実broker、AMQP delivery tag、耐久性/電源断、外部HTTP/email/payment effect、end-to-end exactly-once、ID変更による業務重複回避、並行処理、実時間backoffは未実証。[次の実験](COVERAGE.md)を参照してください。
