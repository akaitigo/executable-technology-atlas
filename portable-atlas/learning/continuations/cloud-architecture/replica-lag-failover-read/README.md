# replica lagとfailover read — Aのack後、Bは何を返すか

Python標準ライブラリで2store・配送queue・routerを明示する有限模型です。A更新ack直後のB readはrevision0/value v0、配送後はrevision1/value v1。partition中もB routeでreadできることと、最新revisionが読めることを分けます。実cloud・quorum・consensus・durability・RTO・性能の検証ではありません。

## 前提と読む順番

Python 3とブラウザのみ。revision、FIFO queue、操作順序、readの観測起点が前提です。

1. [元Cloud Subject](../../../subjects/cloud-architecture/README.md)の「replicatedは複製完了済みの仮定」と末尾Reliability / dataを読む。
2. [先固定oracle](oracle.json)でinitial状態・ack・delivery規則と手書き表を確認。
3. [UI](index.html)でack-a→failover-before-delivery→delivered-before-failover→partition-read→heal-deliverを予想して比較。
4. [worker](worker.py)・[独立checker](checker.py)・rawへ戻り、[WALのsnapshot教材](../../database-engine-internals/wal-snapshot-checkpoint/README.md)とread起点の違いを比較。
5. [未教材](COVERAGE.md)で次の実験を選ぶ。

## 独自契約 → 予想 → 操作

初期A/Bはrevision0/value v0、router A、両store available、配送linkは非partition。単一writerはAだけ、各writeはA revision+1・value更新・FIFO enqueueを行ってからack。ackはローカルin-memory模型の成功で、B反映・永続化の証明ではありません。

deliverは明示command1回でFIFO先頭1件だけBへ反映。partitionまたはB unavailableではqueueを保ち、blockedとして正常に記録。自動配送、quorum、再送、epoch、leader昇格はありません。routeは参照先選択だけで故障検知や昇格ではありません。readは選択storeがavailableなら値を返し、freshは **そのread stepでのA revisionとの一致**。実時間lagではありません。操作は入力順で逐次実行、同時刻概念なし。観測は成功runの最後のreadで固定し、途中readもtraceで表示します。

steps1–20、valueは空でない32文字以下の文字列、boolはexact bool、storeはA/Bのみ。拒否は成功stepまでのtraceを保ち、normal answerはnull。malformed JSONの実行失敗はexit3・stdout空・観測nullで、正常答えを補いません。

~~~sh
python3 -B runner.py --record  # 明示更新：新UTC runのみ作成、旧rawを保持
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

previewの動的127.0.0.1 URLを開き、revision・read available・freshの3予想を選んで比較。条件変更は全予想と旧比較をreset。予想単独変更は新予想群を保持し、旧結果・答え・rawを消します。別terminalのpreview終了はCtrl-C。配信は専有moduleと指定した元/関連README2件のみ。READMEリンクは原本を読み取り専用参照欄へ表示します。

[CURRENT](CURRENT)のrunに実UTC/環境/入力/exit/stdout/stderr/source hash/artifact hashを保存。[runner](runner.py)の通常起動とchecker/routeは更新しません。[QA](QA.json)に実IAB・hash/mtime不変・資源終了を記録します。

## 正常・partition・拒否・実行失敗を比較

|case|最終read store/revision/value|requiredRevision/fresh|配送queue|
|---|---|---|---|
|baseline|A/0/v0|0/true|空|
|ack-a|A/1/v1|1/true|revision1|
|failover-before-delivery|B/0/v0|1/false|revision1|
|delivered-before-failover|B/1/v1|1/true|空|
|partition-read|B/0/v0、available=true|1/false|blockedでrevision1保持|
|heal-deliver|途中B/0、最終B/1/v1|途中false→最終true|復旧後配送で空|
|two-writes-one-delivery|B/1/v1|2/false|revision2残存|
|不正target/op/value/partition、B unavailable read|拒否、normal answerなし|未計算|成功stepまでを保存|
|malformed JSON|実行失敗exit3、stdout空|観測なし|model未実行|

## 原典 → 実装 → 答え → 実務判断

[AWS REL05-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)のdesired outcome/implementation guidanceを設計観点として参照します。今回のreplication規則は独自教材契約であり、AWS製品の具体的挙動を再現しません。

[worker](worker.py)は実際の辞書とFIFO queueを変更し、stepごとの全store・queue・route・ack/readを記録。[checker](checker.py)はproducerをimportせず、先固定のliteral revision/delivery/read表を全step照合します。自己整合するraw/派生値/hashの改ざん7件も拒否します。

A ack後にBへrouteを替えるだけではBのrevisionは増えません。partition-readではavailable=trueでもfresh=false。2更新中1件配送ならBはrevision1、Aはrevision2でfresh=falseです。復旧しても明示deliver前に最新になる契約ではありません。

実務では「readできたか」「どのwrite revisionを要求するか」「どのstepで観測したか」「ackがどこまで保証するか」を分けます。この模型からdurability、real-time lag、RTO、leader選出、cloud製品の保証を推論しません。

## 限界

全Subject未完成。2in-memory store・単一writer・有限FIFO・逐次stepだけ。process crashや永続化、実cloud、quorum、consensus、split brain、重複/順序逆転配送、RTO保証、実性能は未実証。[次の実験](COVERAGE.md)を参照してください。
