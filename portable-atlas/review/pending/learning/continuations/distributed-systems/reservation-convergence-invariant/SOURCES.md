# 原典と独自の予約規則

[Lamport, Time, Clocks, and the Ordering of Events (1978)](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)、刊行p.559、The Partial Ordering、Definition。2026-10-06に著者サイトのPDF本文を取得。process内順序・同一messageのsend→receive・推移性から先行を定義し、互いに先行しないeventを並行とする。本教材のpartition中A/B requestには相互message edgeがない。画面global stepからそのedgeを加えない。

この節は在庫規則・union merge・保留応答・直列判定器を規定しない。それらは[契約](EXPECTATIONS.md)で定めた独自simulationである。論文のアルゴリズムや特定CRDTを実装したとは扱わない。本文・図の複製を教材に保存しない。

[既存学習道筋](../../../subjects/distributed-systems/LEARNING_PATH.md) §6実験3から派生。既存max-register・history-linearizabilityの原票を本実験の成功証拠に用いない。
