# 開いているWAL DB：copy成功でもcommit済み行が残るか

[元Resilience Subject](../../../subjects/resilience-continuity-disaster-recovery/README.md) README:55 Backup/durability次案のうち、開いたWAL DBのBackup APIと主DB単独copyだけを進める有限教材。Python sqlite3と自分のTemporaryDirectoryを使用し、共有DB・Docker・設定へ触れません。

## 前提 → 読む順 → 予想

commit、checkpoint、DB主file/WAL、SHA-256、新接続SELECTが前提です。

1. 元Resilienceのsnapshot鮮度：閉じたrollback-journal DBでhash一致と最新行を分ける。
2. [WAL snapshot/checkpoint](../../database-engine-internals/wal-snapshot-checkpoint/README.md)：readerの可視値とcheckpoint進捗を分ける。
3. 今回：[事前行table](oracle.json)→[UI](index.html)でBackup API行/単独copy行/欠落行数を予想→保存実測と比較→raw/実装→答え。
4. [元DB query-plan](../../../subjects/database-engine-internals/README.md)はアクセス経路の教材。今回の保存境界をquery planの合格へ混ぜない。

## 固定snapshot契約とactual cycle

CREATE records、行1をcommitしTRUNCATE checkpoint完了[0,0,0]。当該専用writer接続だけwal_autocheckpoint=0。行2をcommitした後は追加write/checkpointを行わず、writer接続を保持してsnapshot時点を固定します。main fileは行1時点と同じhash、非空WALにcommit済み行2が残る。新source接続のSELECTは[1,2]です。

その時点のsource main/WAL/shm byteを保存。Connection.backupで別DBを作りdestinationを閉じ、新接続read-only SQLで[1,2]。別対照のshutil.copyfileは主DBだけをcopyし、copy成功・source主fileと同hashですが、新接続SELECTは[1]。保存artifact readはmode=ro&immutable=1、実source readはWALを読むmode=ro。immutableによる主file読取りをWAL pairの論理readに使いません。

| mode | source新接続 | 主fileだけ | Backup API新接続 | 主DBcopy新接続 | copy欠落 |
|---|---|---|---|---|---|
| compare | [1,2] | [1] | [1,2] | [1] | [2] |
| backup-only | [1,2] | [1] | [1,2] | 未実行 | 未実行 |
| main-only | [1,2] | [1] | 未実行 | [1] | [2] |
| unknown mode / external path | 未観測 | 未観測 | 未観測 | 未観測 | 未観測 |
| WAL不可 / SQL障害 / JSON失敗 | 未完了 | 未観測 | 未観測 | 未観測 | 未観測 |

WAL不可対照は専用:memory:へ実PRAGMA journal_mode=WALを行いmemoryが返るためWALUnavailable/exit4。実VFS故障やdisk DBのWAL非対応一般性とは扱いません。SQL障害対照は行2のINSERT先をmissing_tableへ変え、実OperationalError/exit4。行1だけのfailed-sourceを保存。JSON失敗は実decode exit3/stdout空。いずれも通常snapshot完了の答えを補完しません。mode以外のkey/外部pathは一時DB作成前にREFUSED/exit2。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

recordのみ新UTC runへ実command/input/exit/stdout/stderr、SQLite環境、SQL result/trace、source main/WAL、copy/backup DB、hashを保存。旧raw保持。[CURRENT](CURRENT)が原票を指します。自身のlive TemporaryDirectoryはwriterを閉じてcleanupし、捕捉済みartifactだけが残る。checkerはproducerをimportせず固定行tableと別read-only SQLで照合。WAL pairは保存artifactへshmを書かないよう、専用oracle tempへbyteをcopyしてmode=ro/query_onlyで[1,2]を確認します。通常checkerでmodule全SHA/mtimeは不変。

prepareで失敗したSQLはtrace_callbackに出ないことがあります。SQL attempt receiptへ実例外を残し、callback traceと成功executeだけを照合します。失敗を消したり正常SQLに置換しません。[QA](QA.json)は実IAB、全予想変更の新値保持/旧本文消去/閉鎖、条件reset、failure対照、captureと資源終了。

## 原典 → 実装 → actualから答え

[SQLite WAL §2 How WAL Works / §2.1 Checkpointing](https://www.sqlite.org/wal.html)、[SQLite Backup API](https://www.sqlite.org/backup.html)、[Python Connection.backup](https://docs.python.org/3.9/library/sqlite3.html#sqlite3.Connection.backup)を確認。[worker](worker.py)は実SQLiteとfile操作、[checker](checker.py)は固定期待行/SQL順序/別経路read。

答えは実sourceRows/backupRows/copyRows/missingから構築します。copyのbyte成功やintegrity okだけではcommit済み行2の保存を意味しない。WAL状態を含む論理DBを読んだBackup APIと主file単体を区別し、必要な復旧点の行を新接続で確認することが判断材料です。

## 何が増えたか → 残範囲

元snapshot教材は閉じたDBの復元鮮度、元DB教材はqueryアクセス、既存WAL単元はreader snapshot/checkpointを実証。今回だけ **開いたDB・WAL commit済み状態で保存手段の差** を追加しました。

電源断、transaction途中のprocess停止、並行backup/write、offsite、fsync/flash耐久性、実RPO/RTO目標達成、復旧サービス、他DB/FSへの一般化は未実証。[COVERAGE](COVERAGE.md)へ。Core/fullGate/install/公開/commit/pushは割当外。全Subject完成は主張しません。
