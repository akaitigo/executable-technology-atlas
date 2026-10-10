# Performance / capacity engineering：未完了jobを平均から落としていないか

Subjectの入口です。stdlibの単一server・有限batch FIFO workloadを実行し、arrival/start/finish、wait、queue、window面積を比較する有限教材です。全Subject未完成。本番capacity・forecast・実負荷benchmarkの保証ではありません。

## 前提 → 主要概念と仕組み

前提は区間、積分（長方形面積）、平均、throughputです。各jobのservice時間は2model tick。初期systemは空。同時arrivalは入力順FIFO、start=max(arrival,前job finish)、finish=start+service。有限入力は最大20jobでqueueも有限ですが、buffer上限やdrop policyはありません。tickは秒ではなく、executionObservedNsはローカル計算時間でjob latencyではありません。

wait=start-arrival、response=finish-arrival。Lはsystem内（待ち＋service）の時間平均人数、Lqは待ちqueueだけ。utilizationは窓内busy面積/Tで、throughputは完了数/Tです。有限batchにbelow/at/overloadを付けていますが、定常安定性や将来負荷を測ったものではありません。

## 予想 → 操作 → 正常・境界・意図異常の比較

「censoredの完了jobだけの平均response×完了率はLと同じか」を予想し[UI](index.html)で操作します。

```sh
python3 -B runner.py --case censored
python3 -B server.py
```

表示された127.0.0.1動的portを開きます。timelineの窓境界、未完了job、segmentsとintersectionを追ってください。

|case|arrival / window|system area / queue area|理解する比較|
|---|---|---|---|
|below-capacity|0,3,6 / [0,10)|6 / 0|待ち0・idleあり|
|at-capacity|0,2,4,6,8 / [0,10)|10 / 0|service終了とarrival同時、待ち0|
|overload-drained|0,1,2,3,4 / [0,10)|20 / 10|wait0,1,2,3,4、窓終端で排出済み|
|censored|同overload / [0,6)|14 / 8|j4,j5未完了。L=7/3、完了だけの積=3/2|
|cropped|同overload / [2,6)|11 / 7|j2 carry-in、j4,j5 carry-out。L=11/4、完了だけの積=7/4|
|arrival-at-end|0,6 / [0,6)|2 / 0|時刻6arrivalは窓外、j2はcohortに含めない|
|empty|空 / [0,6)|0 / 0|L=0、job平均は対象なし。0/0にしない|
|invalid-service / invalid-window|service0 / 幅0|拒否|不正時間を成功・空queue扱いしない|

## 原典 → 実装 → 答え

[Little 1961](https://pubsonline.informs.org/doi/abs/10.1287/opre.9.3.383)の原典abstractと[MIT queueing講義](https://web.mit.edu/1.041/www/lectures/L8-queuing-models-2026sp.pdf)でL・λ・Wと理論の前提を読みます。[runner](runner.py)のevent境界segment積分と[独立oracle](oracle.py)の固定手書きtimeline＋unit slot積分を比較してください。原典の定常確率過程の平均と、今回の有限決定workloadは同一ではありません。

有限窓[a,b)ではsystem areaは各jobの[arrival,finish)∩[a,b)の長さの合計です。queue areaは[arrival,start)とのintersectionです。runnerはeventで切ったsegment人数×長さ、oracleは整数tickの独立slot countで照合します。完了数はfinish∈(a,b]、arrival数はarrival∈[a,b)。finish=aは前窓、finish=bは今回の完了数です。

答えはcensoredで完了j1–j3のresponse平均3、完了率1/2、積3/2。未完了j4,j5の窓内滞在を除いた積はL=7/3に一致しません。croppedでは窓前arrivalのj2も面積に寄与します。

正しい有限面積の会計恒等式として、intersectionが正の全K job（carry-in/未完了を含む）をcohortと定義し、K/T × mean(clipped residence)=area/Tを表示します。cohortRateは到着率でも完了率でもなく、cohortExposureMeanはfull responseではありません。この恒等式が一致してもLittle's lawの定常適用やcapacity保証になりません。emptyは面積0・L0ですが平均未定義と明示します。

```sh
python3 -B checker.py --record  # 明示的にcase/生成workload原票を更新
python3 -B checker.py           # 保存原票・oracle・hash・QAのread-only検査
```

[実行原票](observations/run.json)、[QA](observations/qa.json)、[session](observations/session.json)、[sources/locator/binding](sources.json)、[module skill](skills/atlas-performance-capacity-engineering/SKILL.md)。実UTC/環境/input/raw/source/artifact digestを保存し、通常checkerは更新しません。

## 実務判断 → 限界 → 次に学ぶ

今回判断できるのは有限workloadの待ち、backlog、境界で失われる観測、LとLqの違いです。capacity分析では、測定窓・cohort・未完了処理を先に揃える視点が得られます。将来capacityや本番server数は求めていません。

単一FIFO・一定service・整数tick・非preemptive・drop/retryなし。実CPU/IO/memory/network、service分布、優先度、多server、autoscaling、tail latency、実benchmarkは未実証です。

|未教材coverage・問い|次の実験（すべて未実施）|公式locator|
|---|---|---|
|Workload / resource：同QPSでもcostは同じか|架空service分布とCPU/IO costを変え、同arrivalのwait/tail比較|[Handling Overload: Pitfalls of QPS](https://sre.google/sre-book/handling-overload/)|
|Measurement / benchmark：平均はtailと未完了を隠すか|専用local benchmarkでraw samples・p95/p99・warmup・censorを比較。baselineと環境を記録|[Monitoring: golden signals](https://sre.google/sre-book/monitoring-distributed-systems/)|
|Capacity / scaling：server増加とqueue制限はどう効くか|架空2server・bounded buffer・drop/backpressureを追加しlatencyと処理数比較|[MIT queueing](https://web.mit.edu/1.041/www/lectures/L8-queuing-models-2026sp.pdf)、[Handling Overload](https://sre.google/sre-book/handling-overload/)|
|Overload / resilience：retryは回復を助けるか|架空retry/deadline/load sheddingでbacklog・失敗数・回復時間を比較|[Cascading Failures: Load Testing](https://sre.google/sre-book/addressing-cascading-failures/)|
