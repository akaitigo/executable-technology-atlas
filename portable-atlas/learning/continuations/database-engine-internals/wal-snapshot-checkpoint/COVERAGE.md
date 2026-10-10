# 到達範囲

実行済み：2接続のsnapshot保持／解放、BEGINと最初のSELECTの違い、writer COMMIT／ROLLBACK／2回COMMIT、PASSIVE／FULL／TRUNCATE、checkpoint完了とWAL切り詰めの違い、閉じた実DBとWAL原バイト列の照合。

未検証の主要領域：異なる開始位置の複数reader、writer同士の競合、stale reader昇格とSQLITE_BUSY_SNAPSHOTの実コード、autocheckpoint、WAL再利用、shared-memory内部、B-tree page分割／cache／I/O、統計と複合／covering index、電源断と復旧、他OS／NFS／他エンジン、実務データでの性能とサイズ。

次の実験（元Subject候補の消化とは別に提案）：

1. 2 readerを異なるCOMMIT位置で開始し、片方ずつ終了。checkpoint進捗の境界を比較する。[WAL §2.2](https://www.sqlite.org/wal.html#concurrency)
2. 専用DBでautocheckpoint閾値を変え、明示checkpointとWAL再利用を区別する。[PRAGMA wal_autocheckpoint](https://www.sqlite.org/pragma.html#pragma_wal_autocheckpoint)
3. stale readerをUPDATEへ昇格。実エラーコードが得られるruntimeではcode/nameを保存し、得られなければ文言とAPI制限を残す。[Isolation / SQLITE_BUSY_SNAPSHOT](https://www.sqlite.org/isolation.html)

この追加単元はdatabase-engine全体のcompleteではない。元query-plan入口、SQL transactionとwindow-frame単元へはREADMEのread-only参照で接続する。
