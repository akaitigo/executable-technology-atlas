# producer実行前に固定する契約と手表

単一consumer。tick0..horizonを観測し、[start,end)のserviceを処理。preemptionは全条件で無し。各tickは①終了予定がこのtickのjobを完了、②同着イベントをinput配列順で受入/drop、③idleかつtick<horizonなら待機jobを一つ選択して開始、④状態記録。horizonで完了・到着は扱うが新規開始しない。容量は待機jobだけ、実行中は別。idleでも同着全件を先に受入れる。満杯はその到着をdropし、evictionしない。

受入はFIFO admission。policy=fifoなら先着、priorityなら大きいpriorityが先、同priorityは受入順。これはjob選択の独自模型で、RTOS task priorityやmessage queue内の自動priority順ではない。service1..6は作為的整数tickで、WCET・実時間・実IRQは測定しない。

|条件|受入 / drop|service [start,end)|horizonで実完了順|
|---|---|---|---|
|priority A4 capacity2|ABC / DE|A0–4,C4–5,B5–7|ACB|
|FIFO 同入力|ABC / DE|A0–4,B4–6,C6–7|ABC|
|B priority3,C1|ABC / DE|A0–4,B4–6,C6–7|ABC|
|長いA6|ABC / DE|A0–6,C6–7,B7–9|AC、Bは処理中|
|短いA1|ABCDE / 無|A0–1,C1–2,D2–3,E3–4,B4–6|ACDEB|
|capacity3|ABCD / E|A0–4,C4–5,D5–6,B6–8|ACDB|
|完了/到着同tick capacity1|AB / C|A0–2,B2–3|AB|
|同着A低,B高 capacity1|A / B|A0–1|A|
|horizon0|A / 無|開始なし|完了なし、待機A|
|故障 horizon4|ABC / DE|A0–4、C/Bは待機|実Aのみ、報告ABC=3は誤り|

[oracle.json](oracle.json)はこの手表の全固定interval/受入/drop/拒否。intervalから各tickの待機・処理中・累積完了を集合演算で展開するため、tick loopと選択をproducerと共有しない。個々のwait=start−arrival、完了response=end−arrivalも比較。未開始waitや未完了responseはnull。長いA6のBはstart7、予定end9、horizon8ではresponse未観測、残り1。priority A4のB wait4/response6、C wait3/response4。FIFO B wait3/response5、C wait5/response6。

入力はexact capacity/horizon/policy/report/events。capacity0..3、horizon0..12、event0..6件、ID A..F重複なし、arrival0..horizonの昇順、priority0..3、service1..6、全数値exact intでbool拒否。event exact id/tick/priority/service。report=actual/accept-fault。全件を処理前に検査し、拒否は全traceなし。実RuntimeError対照は正常計算とは別。通信503も別に注入する。

[可変literal](custom-oracle.json)はD/F/Eの独立表。priorityはD,E,F、FIFOはD,F,E。horizon4のD4はDだけ完了し、新しいEの開始は行わない。capacity1では同着Fを先に受入れ、高priority Eをdropする。空入力の全数0も独立対照。

初回accepted-faultの手表には終端4でC開始と誤記した。horizonで新規開始しない契約との不一致を実照合で検出し、この表だけを修正。修正前source/手表と失敗23条件rawをrevisions/evidenceへ保存し、成功currentへ昇格しない。
