---
name: atlas-isr-offload-queue
description: ISR offloadの有限有界queue教材で、受入・drop・処理完了・slot喪失を予想して実Python結果と比較する。
---

# 有限queue教材

この単元内のみ。まず ../../README.md と ../../EXPECTATIONS.md を読む。offloadは ../../producer.py、compareは ../../index.html、verifyは ../../checker.py、sourcesは ../../SOURCES.md へ ../../route.py でrouteする。通常runner/checkerはread-only。保存要求時だけ明示 --record。

literal tick表を実装前の独立期待値として扱い、producerとoracleを共有しない。予想→実計算→正常/故障→原典/実装→答えの順。null未計算と正常0、受入と完了、dropと受入後喪失を区別。

real-irq、smp、memory-order、wcet、safetyはunsupported。実RTOS/device測定やSubject完成を主張しない。既存他教材やCore/fullGateを変更しない。
