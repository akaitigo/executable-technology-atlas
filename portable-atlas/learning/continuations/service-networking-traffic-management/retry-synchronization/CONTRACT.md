# 固定分散delayと再試行集中の契約

この単元は4 clientの有限仮想時刻模型です。固定分散delayの有限比較であり、確率的jitterの性能測定ではありません。既存のserial breaker/deadline/budget、endpointの重み付き選択、副作用の再実行判断は前提へ戻します。

## 固定する入力

client IDはA,B,C,Dの順、全員が初回をtick0に予定します。1 attemptは区間 `[start,start+1)` を占め、結果の観測はfinish=start+1です。各tickのserver受理容量は1です。待ち行列はなく、同tickに予算内で開始した最初のclientだけを受理し、残りはOVERLOADEDになります。これらもattemptとして1tick後に失敗結果を観測します。受理されたattemptは確実に成功し、完了時にclient別の合成効果を1件増やします。

追加retry上限は各client2回（初回を除く）、1 clientの最大attemptは3回です。run共通call予算は開始した全attemptを数えます。予算はclientごと・tickごとには補充しません。固定のdelay列2要素は、第1/第2の追加retryを予定するときに使います。失敗したattemptの**完了時刻＋対応delay**が次の最早開始時刻です。delayは全て1以上なので、失敗完了と同じtickにそのclientが再開することはありません。

|ID|待機列 A/B/C/D（各2要素）|共有call予算|
|---|---|---:|
|synchronized|[1,1] / [1,1] / [1,1] / [1,1]|12|
|staggered|[1,1] / [1,1] / [2,1] / [3,1]|12|
|skewed|[1,1] / [1,1] / [1,1] / [1,3]|12|
|budget-five|synchronizedと同じ|5|

未使用のdelay要素も固定入力として保持します。観測結果を見て列を最適化したものではありません。全行はtick0..7を保存し、t7は完了処理だけで固定入力の全clientが終端になります。任意のdelayや無限queueを受け入れるschedulerではありません。

## 同じtickの順序

1. 前tickに開始したattemptをclient ID順に完了させます。成功なら合成効果を増やしSUCCEEDEDへ。失敗時に残retryが0ならRETRY_EXHAUSTEDへ、そうでなければ `due=finish+delay[retries_used]` を保存してWAITINGへ。
2. dueが現在tickと等しいclientをID昇順に一度列挙します。開始候補の順は常にA→B→C→Dであり、公平性の保証ではありません。
3. 各候補について、まず共有call予算を検査します。残0ならCALL_BUDGETへ終端し、attempt開始・retry消費・server判定・副作用はありません。この候補も「到来候補数」には含め、実attempt数とは分けます。
4. 予算内ならattempt数と共有call数を1増やします。追加attemptの場合だけ、この**開始時点**で残retryを1減らします。続けて当該tickの受理枠を検査し、未使用なら受理、使用済みならOVERLOADEDとします。結果はまだclientへ通知せずRUNNINGとし、finishを保存します。
5. このtickの処理後のclient状態・累積値を保存します。全試行表は最終的に分かった結果の一覧で、選択tickまでにclientが観測した結果とは区別します。

予算5のtick2では、Bが5番目のcallを開始してからC,Dを予算拒否します。C,Dの追加retryは消費されません。分散例のtick3はBの完了を先に観測し、その後にCが開始します。実OSの同時実行やrequest到着時刻の測定ではありません。

## 保存する量と停止理由

各attemptにclient、初回を1とするordinal、start、finish、accepted、最終outcome（SUCCESS/OVERLOADED）を記録します。合成効果は受理時でなく成功完了時に加算します。拒否だけで効果は増えません。応答欠落・効果後再送はこの固定模型に含めず、重複効果0は冪等性の保証ではありません。

各tickには完了一覧、到来候補・開始・受理・予算拒否の各client列、call累計と残予算、retry累計、合成効果累計、4 clientの状態を保存します。各clientはstatus、attempts、retries_used、retries_remaining、next_due、in_flight_finish、成功completion_tick、終端terminal_tick、effectsを持ちます。未到達の時刻はnullです。SUCCEEDED/RETRY_EXHAUSTED/CALL_BUDGETの終端後はnext_due/in_flight_finishともnullです。

終端一覧は成功数、成功していない数、終了理由別数、全call数、retry数、合成効果と重複効果、完了時刻を分けます。「成功していない」はt7でも待機中という意味ではなく、本4条件では全員終端です。初回ピーク4は全条件で同じです。retry開始だけの最大同tick数と全attemptの最大同tick数を分け、分散で初回ピークが下がったとは説明しません。

## 入力と検査

fixtures.jsonのschema/version、client順、時刻、容量、整数予算・retry・delay、4条件全値を実型込みで先に照合します。boolをint、floatをintとして受理しません。未知/欠落/余分なキー、順序や値の改変は模型更新前に拒否します。拒否の更新0/attempt0は先行検証による事実で、外部通信回数の測定ではありません。受理された固定条件のCALL_BUDGET/RETRY_EXHAUSTEDは入力不正ではなく模型の結果です。

作者手表は各tickの開始候補・受理/失敗区間・予算拒否・client終端・累積値を先固定します。独立担当はproducerを読まず、区間とID順から別にsuffixではない全8tickの期待を導出します。保存検査はproducerをimportせず、固定手表と別の区間包含/完了回数から値を照合します。ブラウザーは保存値と由来の完全一致を検査して表示するだけで、新しい通信や模型計算は行いません。

## 原典と適用範囲

Microsoft Retry patternのRetry strategiesは複数instanceの要求を時間へ分散する判断、Idempotencyは実行後応答欠落による重複の注意点を説明します。4 client、容量1、ID順、1tick、固定delay、予算12/5は全て教材独自規約です。実network/proxy/mesh、確率分布、hedging、distributed budget、公平性、性能・可用性・冪等性、一般の最適delayは未実証です。SDK/install/外部効果/壁時計待機は不要です。
