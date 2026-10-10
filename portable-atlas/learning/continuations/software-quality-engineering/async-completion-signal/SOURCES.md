# Node原典と証拠の境界

2026-10-05に[実runtimeと同版Node v25.2.1 Test runner](https://nodejs.org/download/release/v25.2.1/docs/api/test.html)のTest runner、Extraneous asynchronous activity、test()本文を確認。同期例外/Promise rejectでtestがfailし、test failureはprocess exit1となる。返すPromiseがどの完了を表すかを明確にするため、[case.test.mjs](case.test.mjs)ではwork Promiseをtest内でawaitする。

先に取得した[latest docs](https://nodejs.org/api/test.html)はv26.10.0で、この実runtime v25.2.1と区別する。mock timersは使わず独自明示gateで順序を制御した。公式例のsetImmediate/setTimeoutを転記しておらず、timer機能の適合試験ではない。

[独立期待](oracle.json)、[実TAP/raw pointer](evidence/current.json)、[producer](case.test.mjs)、[独立検証](oracle.py)へ戻って、全flaky原因や実OS競合への一般化を避ける。test file exit2→outer runner exit1は今回実観測で、公式に全種類の拒否mappingを確認したとは主張しない。
