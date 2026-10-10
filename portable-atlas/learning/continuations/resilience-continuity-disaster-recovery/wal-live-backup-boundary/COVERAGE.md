# 元coverage → 今回 → 残範囲

[元Resilience](../../../subjects/resilience-continuity-disaster-recovery/README.md) README:55 Backup/durability。今回はlive WAL snapshot固定後のBackup APIとmain-only copyの差だけ。

| 既存/今回 | 有限証拠 | 増えた問い |
|---|---|---|
| 元Resilience snapshot | 閉じたDB、復元byteと行鮮度 | latestより古いsnapshotは |
| 元DB query plan | 同datasetのアクセス経路 | 保存の完全性とは別 |
| [WAL snapshot](../../database-engine-internals/wal-snapshot-checkpoint/README.md) | reader end markとcheckpoint進捗 | snapshot可視値とstorage反映は |
| 今回 | row2 WAL commit後writeなし、backup[1,2]/maincopy[1] | filecopy成功でcommit済dataを失うか |

transaction途中停止/電源断、並行backup、offsite/RPO/RTO、実復旧runbook、暗号化/権限は未実証。次は隔離processの中断と独立復旧行oracle、並行backup時点定義を別scopeで行う。[SQLite WAL](https://www.sqlite.org/wal.html) / [Backup API](https://www.sqlite.org/backup.html)は設計原典で、未実行事項の達成証拠ではありません。
