# 原典からモデルへ

[Zephyr Interrupts: Offloading ISR Work](https://docs.zephyrproject.org/latest/kernel/services/interrupts.html#offloading-isr-work) を2026-10-05に確認。locatorは同見出し。ISRを短くし、時間を要する処理をthreadへ渡す考え方、FIFO/LIFO/semaphoreでhelper threadへ知らせる方法やworkqueueが説明される。実際の実行順はthread priority等に依存する。

本教材はそのoffloadの入口から、有限queueの受入とconsumer完了を分ける問いへ接続する。Zephyr API・kernel・IRQを実行していない。reject-newest、単一slot故障、tick0..5は教材が先固定した契約で、Zephyrの一般保証ではない。[事前契約](EXPECTATIONS.md)・[実装](producer.py)・[独立literal](oracle.json)へ戻る。

[元Subject](../../../subjects/embedded-firmware-rtos/README.md)の「Subjectの主要未教材coverage」queue/semaphore・ISR offload行の一部を扱う。memory order/SMP、実IRQやSafetyは未教材のまま。[関連有界queue](../../performance-capacity-engineering/two-server-bounded-queue/README.md)は2serverとproducer待ちを比較する別モデル。同時刻順序・service時間・容量定義は持ち込まず、この教材の契約を読み直す。
