# 未教材と次の実験

元[Performance / capacity README](../../../subjects/performance-capacity-engineering/README.md)末尾「Capacity / scaling」の有限2server・bounded queue比較。元Subject/Portalを変更せず、この単位の範囲だけを記録します。

|未実証の問い|次の有限実験（未実施）|一次原典locator|
|---|---|---|
|job costが異なるとどうなるか|service1/5混在でFIFOと優先度の完了順/tail比較|[Handling Overload: Pitfalls of QPS](https://sre.google/sre-book/handling-overload/)|
|retry/deadlineの影響は|bounded retry/deadlineでattemptとlogical requestを分離|[Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)|
|producer待ちを実測から失っていないか|専用local benchmarkでoffered/accepted timestampsと未完了を保存|[Monitoring: golden signals](https://sre.google/sre-book/monitoring-distributed-systems/)|

TCP、adaptive throttling、本番capacity、CPU/IO/memory、autoscaling、無限流の安定性、producer間公平性は未実証です。
