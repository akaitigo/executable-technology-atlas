---
name: wal-live-backup-boundary
description: 自分のSQLite WAL snapshotのBackup APIとmain-only copyを有限比較し、保存原票を読み取り照合する。
---

module rootでpython3 -B route.py inspect / lesson。元snapshot鮮度→WAL→backupの読む順を保つ。
通常checkerはreadonly。明示更新のみrunner.py --recordで新UTC原票を追加し旧rawを保持。共有DB/外部path/Docker/settings/installを行わない。copy成功とcommit済行の保存、契約拒否とWAL/SQL/JSON失敗を分ける。電源断/RPO/RTO達成を主張しない。
