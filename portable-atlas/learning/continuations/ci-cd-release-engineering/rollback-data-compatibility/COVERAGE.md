# 到達範囲

増分：実SQLiteでのapp×schema 6条件、additiveとrenameの2release flow、synthetic health failure、保存artifact digestへのpointer rollback、rollback後の実旧reader成否、schema/row/closed DB digestの前後比較。

主要未網羅：write互換性、expand/contract・backfill・制約、混在versionと長期migration、concurrent promotion、署名とprovenance、権限/secret、canaryの実metric、backup restore、point-in-time recovery、実CI/registry/cluster、online migration／無停止／crash保証。

次の有限実験（未実施）：

1. expand→backfill→contractの各時点で旧/new readerを混在させる。rename単発との差を固定表で比較。[SQLite ALTER TABLE §3/§4](https://www.sqlite.org/lang_altertable.html)
2. 専用fixtureへ旧/new writerを加え、default・NULL・constraintとbackfillの意味を照合する。[SQLite ADD COLUMN制約](https://www.sqlite.org/lang_altertable.html#alter_table_add_column)
3. 新割当の専用DBでbackup→restoreを明示実行し、schema/rowと保存時点のhashを確認。今回のbefore copyをrestore成功と読み替えない。[SQLite Backup API](https://www.sqlite.org/backup.html)

[Kubernetes Pod template rollbackの境界](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)は原典参照だけ。実Deployment動作は未実行。Subject全体、Atlas Core audit/npm gateは今回の有限受入に含めない。
