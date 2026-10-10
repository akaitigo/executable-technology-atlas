# 有限windowの追加範囲

元SubjectのSQLite outbox/offset replayから独立して、2partition maxSeen−Lとglobal min、半開窓、初回fire/allowed-lateness保持/finalize、max故障の早期drop、止まるpartitionを追加。整数tickの明示契約で、Flinkタイマーの完全再実装ではありません。[README](README.md)で境界と再現を読む。

未制作：idle自動判定、periodic emission、無限stream、window join、keyed state、checkpoint/savepoint/復旧、backpressure、実Flink、実WAL CDC、Kafka/Debezium、production latency/completeness/durability/exactly-once。E1/E2/E4も元Subjectの未教材のままです。有限末尾でopenが残ることは隠しません。
