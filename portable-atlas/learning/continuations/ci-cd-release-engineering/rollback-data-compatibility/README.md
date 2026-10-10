# Artifact rollback と data recovery の境界

[元CI/CD教材の次3](../../../subjects/ci-cd-release-engineering/README.md)を実SQLiteへ進める独立continuation。保存済みbytesのdigestへactive pointerを戻す操作と、schema/dataを戻す操作を分ける。外部CI、実deploy、provider、Kubernetesは起動しない。

## 予測 → 操作 → 比較

`python3 preview.py` が表示する動的127.0.0.1 URLを開く。migrationを選び、戻したv1 readerの成否とDB復旧を予測して比較する。release時点、実SQLiteのcolumns/row、artifact digest、command/SQL/exit/rawを照合する。UIは保存観測を読むだけ。

[互換表](compatibility.json)はproducer実行前に手書きで固定した。v1 readerは`SELECT id, name FROM person ORDER BY id`、v2 readerは`SELECT id, display_name FROM person ORDER BY id`。fixtureは(1, Ada)。additiveはdisplay_name追加とAda-v2のbackfill、renameはname→display_nameとAda-v2へのUPDATE。

|schema|固定v1 reader|固定v2 reader|
|---|---|---|
|v1|exit0: (1,Ada)|exit3: no such column: display_name|
|additive|exit0: (1,Ada)|exit0: (1,Ada-v2)|
|rename|exit3: no such column: name|exit0: (1,Ada-v2)|

6互換条件のSELECT成功は4、実SQLiteエラーは2。期待通りのエラーをSELECT成功件数へ混ぜない。

## 2つのrelease flow

専用DBを初期化しclosed `before.sqlite`を保存 → migrationを実行してclosed `migrated.sqlite`を保存 → 実v2 reader bytesのdigestへpointer変更 → 実v2 SELECT → **固定合成health failure(exit42)** → 保存v1 bytesを再hashしてpointerを戻す → そのdigestで選んだv1 readerを実subprocess実行 → closed `after.sqlite`を保存。

additiveではv1 SELECT成功。ただし旧readerのAdaと新readerのAda-v2は意味が異なる可能性があり、「SELECTが通る」だけでbusiness互換性を証明しない。renameではpointerは旧digestへ戻ってもv1 SELECTが失敗。両条件ともmigration直後とrollback後のDB SHA256が同じ、migration前とは違う。**DBをrestoreする操作は行っていない。** before copyは比較証拠でありbackup restore成功のcreditではない。healthは実serviceの検査でもreader errorでもなく、明示fixtureの独立subprocess失敗。

## 再現と原記録

- [CURRENT](CURRENT)が現在のrunを指す。runの`result.json`/`stdout.json`はSQL・app command・stdout/stderr・exit・UTC。`inputs.json`は事前互換表のcopy。`artifacts.json`は全rawのbytes/SHA256。
- 実装：[runner](runner.py)、[独立checker](checker.py)、[v1 reader](app_v1.py)、[v2 reader](app_v2.py)。
- 実artifactは固定reader Python sourceの保存bytes。store名はSHA256で、sourceと保存bytesの一致をcheckerが再計算。active/pointer-before/promoted/restored JSONを保存。digestはbytes identityであり署名やbuild provenanceではない。
- `python3 runner.py`、`python3 checker.py`、`python3 route.py inspect` はread-only。checkerはproducer/migration/app実装をimportせず、独立literal互換表、SQL順序、raw/exit、closed DBのschema/row、pointerとDBのdigestを照合。保存DBはmode=ro&immutable=1/query_onlyのSELECTで読む。
- **新規観測の明示指定時だけ** `python3 runner.py --record` または`python3 route.py record`。UTC別runへ追記し旧rawは保全。CURRENTのみ更新する。
- `python3 test_negative.py` はraw/derived/hashを整合させた6種類の誤りを一時copyで独立拒否し、通常検査のSHA256/mtime_ns不変を確認する。
- 実runtime SQLite/Python/source ID/compile optionsを記録。Python APIが返さないerror code/nameを推測で埋めない（今回Python3.9ではnull）。subprocess executable pathは名前へ正規化し、個人絶対pathを保存しない。
- [QA記録](QA.json)、[coverage](COVERAGE.md)、[module Skill](skills/rollback-data-compatibility/SKILL.md)。route inspect/lesson/record、未知routeはexit2。

## 増分と限界

元教材のartifact identity/promotion/rollback境界に、実schema migrationとapp×schema互換性を追加した。[SQL transaction学習](../../../subjects/relational-database-sql/LEARNING_PATH.md)や[WAL snapshot/checkpoint](../../database-engine-internals/wal-snapshot-checkpoint/README.md)と接続する。元READMEの未実施計画はread-onlyで保つ。この追加はCI/CD全体のcompleteではない。

[SQLite ALTER TABLE §3 RENAME COLUMN / §4 ADD COLUMN](https://www.sqlite.org/lang_altertable.html)で変更対象を確認。[Kubernetes Deployments: Rolling Back](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)の注意はrollback対象がPod templateであること。ここからDB recoveryを推論しない。online migration、混在writer、バックアップの復元、無停止、耐障害性、実CI/clusterは未検証。
