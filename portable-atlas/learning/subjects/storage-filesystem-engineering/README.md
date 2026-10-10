# Storage・filesystemを学ぶ入口 — 旧fileをいつ手放す？

有限1教材。task-owned temp filesだけを使い、write-new/atomic rename commitとtruncate overwrite途中exceptionを実OSで比較する。ここでのcopy-on-writeはアプリケーションの別fileへの新版書込戦略で、filesystem block CoWの実証ではない。[UI](index.html)は実行原票をreplayする。全Subject完成ではない。

**前提 → 主要概念・仕組み:** byte列のlength/hash、pathとopen FDを区別する。target.binを読んでいるreaderを開いたまま、同じdirectoryのnew.tmpに新版を書きflush/fsyncし、os.replaceで名前を切り替える。replace前はpath/readerとも旧data、replace後はpathが新版・held readerが旧data。旧inodeへのreaderを閉じた後のrecoverable backupは作らない。truncateは同じinodeを0byteへ変えてから書くため、例外でold bytesを失う。

**予想 → 操作 → 比較:** [UI](index.html)で「new.tmpに4byteだけ書いて例外になったら、旧targetと既存readerは何を読む？」を予想。caseを選びeventを進め、old/newtemp/path/held readerの状態図とlength/SHA-256表を独立oracleに照合。原典/実装を開いてから答えへ進む。browserは保存replayだけで、file操作を新規実行しない。

| case | commit前途中 | 最終path reader | 最終held reader | replace |
|---|---|---|---|---|
| atomic-commit | path/held=old, candidate=new | new | old | 成功 |
| atomic-abort | path/held=old, candidate=prefix | old | old | 呼ばない |
| truncate-fail | path/held=empty→prefix | newのprefix | newのprefix | 呼ばない |

**今回の実装・正常異常:** [experiment.py](experiment.py)が実TemporaryDirectory/flush/fsync/os.replace/reader snapshotsを実行。[oracle.py](oracle.py)は実行codeをimportせず入力のold/new/prefixからlength/hash/hexを独立計算し、inode/reader状態とcommit因果順・temp cleanupを判定する。基準caseはold=`OLD:version1\n`、new=`NEW:version2\n`（各13byte）。cut=4のabortはold13byteを維持、truncate反例はpath/heldとも`NEW:`4byteになりoldを失う。new空の正常commit、cut0のtruncate failure、empty-oldとnew最大1024、cut全長で例外となる境界も残す。

入力は`{"mode":"atomic-abort","old":"old","new":"new","cut":1}`のみ。modeはatomic-commit/atomic-abort/truncate-fail、old/newは0..1024ASCII文字、cutはinteger0..len(new)（bool/float拒否）、commitはcut=len(new)。extra key・外部path拒否。modeやbounds拒否ではtempを作らない。例外注入はOS障害や電源断の再現ではない。writer flush後の実on-file dataをunbuffered held readerで読むのでPython read-aheadの旧cacheと混同しない。

このdirectoryで:

```sh
python3 -B runner.py
python3 -B runner.py --input-json '{"mode":"truncate-fail","old":"old","new":"new","cut":1}'
python3 -B checker.py
python3 -B route.py replace
python3 -B route.py power-loss # 未対応 exit2
python3 -B preview.py # dynamic 127.0.0.1 URLを開く。終了はCtrl-C
```

runnerはmodule内の新規owned tempだけを書き、cleanupし、原票は更新しない。通常checkerはread-onlyで保存raw/oracle/digest/local linksを検査。明示的な原票再観測にだけ`python3 -B observe.py --write-evidence`、artifact binding更新にだけ`python3 -B checker.py --seal-evidence`。input拒否exit2、unexpected error/検査失敗exit1。intentional exceptionは期待する反例なので記録してexit0。[raw](evidence/raw.json)に実input/event/time/PID/readerstate/length/hash/inode/fsync/cleanup、[run](evidence/run.json)に時刻・環境・input/source/artifact digest。[状態図](evidence/reader-states.svg)はrawから生成した図でcaptureではない。[実IAB QA](evidence/ui-qa.json)はcapture保存可否・ownedserver終了を記録する。[初期failure](evidence/bootstrap-failure.json)も保存し、修正済みと区別した。

**実務判断 → 限界:** commit前例外でoldを残す、pathの可視性と既存readerの寿命を分ける、truncate failureでold復元を期待しない、と判断できる。ただしsingle-file runtime atomicityとpower-loss durabilityは別。今回はfile/directory fsyncの呼出・成功/失敗を記録するだけで電源断を試さない。F_FULLFSYNC・device cache flush・filesystem全path・multiwriter・metadata/ACL維持を証明しない。path observerは各checkpointの新規readで、全並行実行の網羅ではない。

**次に学ぶもの → 原典:** [全Subject coverageと次の4実験](COVERAGE.md)でnamespace/metadata→multiwriter→persistence/crash→block CoW/checksum/RAIDへ進む。[公式locator](SOURCES.md)と[専用skill](skills/atlas-storage-filesystem-engineering/SKILL.md)から既存runner/checker/UIへ辿る。Docker・新依存・disk/mount/host設定・外部data・global Skill登録・旧Gate・commit/push/公開は今回行わない。
