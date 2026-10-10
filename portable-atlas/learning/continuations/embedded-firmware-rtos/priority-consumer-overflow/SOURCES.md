# 一次資料と模型の境界

2026-10-06 JST確認。本文/code/図の転載なし。

- [Zephyr Scheduling](https://docs.zephyrproject.org/latest/kernel/services/scheduling/index.html)：ready thread priority、同priorityの待ち順、cooperative/preemptiveの違いを参照。今回のpriorityは独自job dispatcherの大きい整数を優先する規則で、Zephyr thread priority値やschedulerの実証ではない。
- [Zephyr Message Queues](https://docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html)：有限bufferとmessageの送受信、fullとconsumer受取の文脈。今回のFIFO admission後のpriority選択は独自模型で、標準message queueがmessageをpriorityで並べるとは主張しない。
- [Zephyr Offloading ISR Work](https://docs.zephyrproject.org/latest/kernel/services/interrupts.html#offloading-isr-work)：ISRからthreadへ重い処理を移す設計の文脈。consumerのservice tickは作者が置いた整数で、実IRQ・RTOS・WCET測定にしない。

前単位のqueue/offload入力に処理時間・選択priority・完了までの待ちを追加した。今回の到着/phase順序/preemptionなし/horizon cutoffはEXPECTATIONS.mdの独自契約で、原典準拠や実RTOS認証ではない。図は実モデルのinterval/arrivalからBrowser SVGで独自生成。追加依存・実device・外部画像・Dockerなし。
