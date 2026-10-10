# pathnameを消す・置換する。open済みFDはどこを読むか

このMac標準Pythonの専用TemporaryDirectoryで実OS操作を観測する。unlink後の新openはENOENTだが旧FDはold bytes。準備済ファイルを単一os.replaceすると旧FDはold bytes、新openはnew bytes。unlink→replaceを別々に呼ぶ対照は、間の同期readerでENOENTを観測する。

```sh
python3 -B server.py --port 0
python3 -B runner.py
python3 -B route.py baseline
python3 -B checker.py
```

予想→操作→比較→原典/実装→答え: server表示の127.0.0.1 URLを開き、FDとpathnameの予想を記入する。ケースとpayload/fsync/modeを変更して実行。3経路の全trace・図・syscall原票を比べ、文書viewerで実装と手表を読む。予想/入力/ケース/resetは前の結果を消す。保留した旧結果は編集後に無視される。

[契約](EXPECTATIONS.md)、[手表](hand-trace.json)、[独立oracle](oracle.py)、[原典と取得限界](SOURCES.md)、[coverage](COVERAGE.md)、[Skill](skills/atlas-unlink-replace/SKILL.md)。通常CLI/checker/routeは候補のファイルを書かず、実測に使うtempdirは毎回cleanupする。原票更新は明示`runner.py --record`のみ、古い世代を削除しない。

入力はold_payload/new_payload/fsync/modeの4fieldのみ。各payloadは0〜512 ASCII bytes（NULや制御文字もpayloadとして扱う）、fsyncはbool、modeはcompare/missing-source/closed-fd。任意pathを受け付けない。ファイル名live/prepared/missingは内部固定。絶対temp pathを原票に記録しない。

inodeは(st_dev,st_ino)を同一run内のold/newへ対応付ける。再実行や別経路の数値を比較しない。同じ内容でも別inode。図は実原票を描画した説明図、native画像は実UIの静止画。FD番号はprocess内の観測値であり永続identityではない。

単一replaceの原子性は公式API契約へ接続するが、有限before/after観測で全raceの証明はしない。対照のgapはunlink→同期callback→replaceの明示境界であり、sleepでraceを探さない。fsync成功は準備FDへの呼出成功だけ、directory fsync/F_FULLFSYNC/crash durabilityは未検証。全FS/Windows・停電・kernel内部・既存pipe/mmap・pollへ結論を広げない。Subject参照は学習用で計算runtime依存なし。global gate/公開は未実行。
