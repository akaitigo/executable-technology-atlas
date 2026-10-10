# 2台serverと待機容量 — backpressureで待ちは消えるか

固定5jobをevent-driven Pythonで処理する有限教材です。1台/2台、待機容量1のdrop/backpressureを比較し、producer待ちがserver内latencyから外れることを確かめます。実serverの負荷試験ではありません。

## 前提と読む順番

Python 3標準ライブラリとブラウザのみ。tickは秒ではなく抽象整数時間。FIFO、arrival/start/finish、平均と分母が前提です。

1. [元Subject](../../../subjects/performance-capacity-engineering/README.md)の有限窓・未完了cohortを確認。元coverageは同README末尾「Capacity / scaling」です。
2. [先固定oracle](oracle.json)で同時刻順序と手書きtimelineを読み、drop数・最後finishを予想。
3. [UI](index.html)で1台→2台→容量1drop→backpressure→入力拒否を操作し、図・状態とrawを比較。
4. [実装](worker.py)のevent jumpと[独立checker](checker.py)のunit-tick照合を読み、[未教材](COVERAGE.md)で次の問いを選ぶ。

既存の[multiwindow alert](../../sre-incident-operations/multiwindow-burn-alert/README.md)は分母と窓の定義を比較する関連教材です。今回その実装を呼び出しません。

## 定義 → 予想 → 操作

offeredAt0、入力順A–E、service2tick、初期空。IDは識別子でソート優先度ではありません。FIFO・非preemptive、空serverは番号の小さい順。

同時刻は **finish（server番号順）→既存queueからFIFO開始→producerからFIFO受理**。受理jobは空serverで即開始、なければqueueへ。capacityは待機queueだけで、in-serviceを含みません。drop版は満杯の新jobを即drop、backpressure版はproducer FIFOに残して次の空きまで受理を遅らせます。producer待ちは明示状態で、ネットワークprotocolの再現ではありません。

server1/2、capacity0–20、service1–10、job1–20、ID重複なし、offeredAt0を受理。boolは整数として扱いません。検証は固定fixtureのみです。

~~~sh
python3 -B runner.py --record  # 明示更新：新UTC原票、旧runを保持
python3 -B checker.py         # 保存原票のread-only照合
python3 -B test_negative.py   # 自己整合改ざん6件を独立oracleで拒否
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

最後のcommandの動的127.0.0.1 URLを開き、2つの予想を選んで「保存rawと比較」。条件変更は予想と表示をreset。予想変更は新予想を保持し前比較を消します。previewは別terminalで稼働し終了はCtrl-C。配信はこのmoduleと、UIからリンクした元Subject・関連教材の2つのREADMEのみ（読み取り専用）です。[CURRENT](CURRENT)が指すrunに実UTC/環境/input/exit/stdout/stderr/source・artifact hashを保存。通常runner/checker/routeは更新しません。

## 正常・drop・入力拒否 → 原典 → 実装

|case|finish（A–E順）|受理/全要求|drop|producer待ち|
|---|---|---|---|---|
|1台/capacity5|2,4,6,8,10|5/5|0|全0|
|2台/capacity5|2,2,4,4,6|5/5|0|全0|
|2台/capacity1/drop|2,2,4,—,—|3/5|2|受理jobは0、dropにcompletionなし|
|2台/capacity1/backpressure|2,2,4,4,6|5/5|0|D/E各2tick|
|server=true/service0/capacity-1/ID重複/unknown policy|未実行|未計算|未計算|exit2、metrics等null|

[Google SRE Handling Overload](https://sre.google/sre-book/handling-overload/)「The Pitfalls of Queries per Second」「Client-Side Throttling」が一次原典。要求resource costと受理・拒否を区別する視点を参照します。原典のadaptive throttlingや本番resource provisioningを再現しません。

[worker](worker.py)は次finishへjumpしてadmit/start/finish/dropをraw eventに記録。[checker](checker.py)はproducerをimportせず、先固定の手書き時刻から各整数tickの半開区間所属、event位相、server番号、metricsを照合。raw/派生result/hashを同時に改ざんした6負例も拒否。[QA](QA.json)に実IAB・readonly・資源終了を記録します。

## 答えと実務判断

capacity1 dropはA/B/C受理、D/E drop。finished/admitted=3/3でもfinished/offered=3/5。受理cohort平均8/3tickは全要求5jobの平均ではありません。dropにcompletionはなく、全要求平均completion latencyは未定義。0latencyを代入しません。

backpressureではoffered→admitted平均4/5、admitted→start平均4/5、service平均2。admitted→finish平均14/5に対しoffered→finish平均18/5。待ちは消えずproducerへ移ります。最終5/5完了・drop0は有限batchを排出した結果で、無限到着の処理能力の証拠ではありません。

実務ではoffered/accepted/finishedの分母、起点、producer待ち、拒否policyをそろえます。queue上限だけでuser体験を判断しない視点が得られます。

## 限界

全Subject未完成。有限整数tick・一定service・単一producer FIFO・server1/2・retry/deadlineなし。異質job、優先度公平性、実serverperformance、TCP、productioncapacity、autoscalingは未実証。[次の未教材](COVERAGE.md)を参照してください。
