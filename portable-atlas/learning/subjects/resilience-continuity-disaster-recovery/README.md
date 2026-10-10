# Resilience / continuity / disaster recovery：復元できた行は最新か

このSubjectを学ぶ入口です。今回の有限教材は、task-owned SQLiteのbackup → 最新write → mutate → digest確認 → file restore → 新接続でSELECTを実行します。全Subjectは未完成です。標準ライブラリだけでMacローカル実行。既存データや実サービスには触れません。

## 前提 → 主要概念と仕組み

前提はSQLのcommit、ファイル、SHA-256、時刻と期間の違いです。backupの存在、同じbyteへの復元、構造整合性、必要な業務データの鮮度は別々に確認します。snapshot digest一致は最新writeを含む証明になりません。hashを一緒に改変できる相手への真正性保証もありません。

RPOは許容するデータ損失の時間に関する目標、RTOはサービス中断から復旧までの許容時間の目標です。今回の`rpoGapSyntheticTicks`は架空write時刻10/20/30とsnapshot時刻（空は0）の差で、秒でも実測RPOでもありません。`dataLossWrites`は実際の欠落件数です。`restoreObservedNs`はdigest確認前からfile copy・再接続・SELECT・integrity確認後までのローカル観測時間です。障害検知・判断・サービス再開を含まず、RTO目標や達成保証ではありません。拒否時はrestoreObservedNs=nullで、attempt時間のみ記録します。

## 予想 → 操作 → 正常・境界・意図異常を比較

「hashが一致したstale backupにはid3が戻るか」を予想して[UI](index.html)で操作します。

```sh
python3 -B runner.py --case stale
python3 -B server.py
```

serverが表示する127.0.0.1の動的portを開きます。runner/UIは専用の一時ディレクトリで毎回actual cycleを実行し、終了時に自身の一時ファイルを消します。ファイルやDBの入力pathは受け付けません。

|case|snapshot → latest|復元後の新接続で読める行|比較の問い|
|---|---|---|---|
|fresh|1,2,3 → 1,2,3|1,2,3|hash一致＋行一致、欠落0|
|stale|1,2 → 1,2,3|1,2|hash一致でもid3欠落、gap10tick|
|corrupt|1,2,3 → 1,2,3|damaged id99のまま|candidate byte改変をdigestで拒否|
|missing-backup|1,2,3 → 1,2,3|damaged id99のまま|candidate不在を拒否、live維持|
|empty|空 → 空|空|空snapshotもvalid、欠落0|
|stale-empty|空 → 1,2,3|空|整合性okでも3write欠落、gap30tick|

mutateはliveの全行を消し、架空id99を挿入します。全接続を閉じた専用liveにcandidateをcopyしてから新接続で読みます。corruptはcandidateの先頭byteだけを変えます。元snapshotは保存。拒否ならlive hashと行がそのままです。restore timelineの順番・実UTC・elapsedNsをrawで追ってください。

## 原典 → 実装 → 答え

[Python backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)、[SQLite Backup API](https://www.sqlite.org/backup.html)、[integrity_check](https://www.sqlite.org/pragma.html#pragma_integrity_check)を読んで、[runner](runner.py)のbackup/copy/reopenへ戻ります。[独立oracle](oracle.py)はrunnerをimportせず手書きdatasetとSQL読取りで照合します。staleの答えは復元行1,2／欠落3／synthetic gap10。構造整合性okやdigest一致だけでは鮮度を判断できません。

[時刻API](https://docs.python.org/3/library/time.html#time.perf_counter_ns)と[RTO/RPO定義](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_objective_defined_recovery.html)を比較し、観測durationと目標値を混同しないことも学びます。

```sh
python3 -B checker.py --record  # 6actual cyclesと専用SQLite artifactの原票を明示更新
python3 -B checker.py           # 保存原票・hash・SQL・oracle・QAをread-only検査
```

[実行原票](observations/run.json)には実行UTC、Python/SQLite/OS、input/raw/source/artifact digest、timelineがあります。[QA](observations/qa.json)、[session](observations/session.json)、[sourcesとlocator](sources.json)、[module skill](skills/atlas-resilience-continuity-disaster-recovery/SKILL.md)も参照してください。recordは保存された自身の前回artifactを置換します。通常checkerはcycleを再実行せずDBをread-only immutableで開きます。

## 実務判断 → 限界 → 次に学ぶ

今回判断できるのは、この入力と実行でsnapshotのどの行が戻り、何writeを失い、candidateが一致し、拒否時liveが維持されたかです。backup運用の設計では、必要な復旧点と行の意味を決めて復元確認を行う視点が得られます。業務の継続可否、稼働サービスの復旧時間は判定していません。

単一process・閉じたDB・rollback journal既定・小さいデータだけです。copyはcrash-safe atomic置換ではありません。電源断、disk flush、WAL/同時write、暗号化/権限、offsite保管、複数サービスの整合性、failover、全durabilityは未実証です。

|未教材coverage：概念と問い|次の実験（すべて未実施）|公式locator|
|---|---|---|
|Resilience：障害の波及とdegradation、fallbackは正しい応答を保つか|架空依存を失敗させ、timeout・fallback・回復後の応答を比較|[REL05-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)|
|Backup/durability：crash、WAL、concurrent write、保存コピーの独立性|専用SQLiteのtransaction途中でprocess停止し再open、backupAPIと閉じていない単純copyを比較|[Atomic Commit](https://www.sqlite.org/atomiccommit.html)、[Backup API](https://www.sqlite.org/backup.html)|
|DR strategy：replication lag、standby、failover/failbackは何を失うか|架空2storeにwriteを遅延させ、切替前後の欠落・二重writeを比較|[REL13-BP02](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html)|
|Business continuity：影響、依存、役割とrunbook、復旧判定は誰が何で行うか|架空tabletopでRTO/RPO目標とdependency readinessを定義しdrillの判断時間・復旧確認を記録|[REL13-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_objective_defined_recovery.html)、[REL13-BP03](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_dr_tested.html)|

一次資料はsources.jsonに実装とのbinding・未実施境界を記録しています。AWS資料は概念比較に用いており、製品の実行証拠ではありません。
