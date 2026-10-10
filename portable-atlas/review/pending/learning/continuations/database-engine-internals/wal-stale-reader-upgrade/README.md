> 配布用の既定画面は保存13条件の再生です。SQLやAPIを起動しません。元のnative UIは native.html / native-app.js に保持しています。[復元手順・バイナリ検査](MIGRATION.md)を確認してください。以下の新規SQL実験手順と保存再生を区別してください。

# WAL stale readerのwriter昇格

[元WAL単位coverage・次実験3](../wal-snapshot-checkpoint/COVERAGE.md)を実行する第三教材です。[元README](../wal-snapshot-checkpoint/README.md)のsnapshot/checkpoint原票は維持し、この専有unitだけを作ります。この教材単位はローカル受入済みで、Portalへの統合は未実施です。database-engine全体や全分野の完成ではありません。

## 事前schedule → 実SQL → 回復

所有TemporaryDirectoryの架空1行DBを、2つのnative SQLite connectionで操作します。journal_mode WAL、wal_autocheckpoint=0、synchronous FULL、指定busy_timeoutを設定。readerはBEGIN、SELECTでsnapshotを確定、別writerのUPDATE/COMMIT後、旧readerのUPDATEを試します。失敗直後のcodeとautocommit/txn_stateを保存してから再SELECT。reader ROLLBACK→新BEGIN→再SELECT→UPDATE→COMMITで回復を実観測します。

|固定schedule|最初のreader|初回UPDATE code/name|直後row/state|回復前→最終|
|---|---|---|---|---|
|stale: SELECT→writer commit|10|517 BUSY_SNAPSHOT|10 / auto0 READ1|20→21|
|fresh: BEGINだけ→writer commit→SELECT|20|0 OK|21 / auto0 WRITE2|再開始なし→21|
|rollback: SELECT→writer rollback|10|0 OK|11 / auto0 WRITE2|再開始なし→11|
|busy: SELECT→writer lock保持|10|5 BUSY|10 / auto0 READ1|writer取消・新reader 10→11|

「失敗＝transaction自動終了」ではありません。この実測では失敗直後もREAD1、autocommit0。SQLITE_BUSY_SNAPSHOTは5系のextended code517として記録し、一般BUSY5と分けます。busy_ms設定や同じ`database is locked`文言からBUSY_TIMEOUT773を推定しません。monotonic elapsed_nsは各呼出しの実測値ですが、一般的なtimeout保証・待時間比較を主張しません。writer rollbackとbusy対照ではwriter変更をcommitしないため、回復の基準値はinitialです。

## APIと原典の境界

このMacのPython3.9.6 wrapperはSQLite3.51.0ですが、sqlite_errorcode/sqlite_errorname属性はありません。[toolchain棚卸し](qa/toolchain.json)に実例で欠測を保存しました。標準ctypesで既存`/usr/lib/libsqlite3.dylib`の公開C APIを呼び、sqlite3_extended_result_codesを有効にして実sqlite3_extended_errcodeを取得します。Python内部connection pointerを取り出しません。[native.py](native.py)はsqlite3_open_v2/exec/close/get_autocommit/txn_stateを使用。整数codeを[公式result定数](https://www.sqlite.org/rescode.html)へ対応してnameを表示し、文字列messageから推論しません。

[SQLite Isolation](https://www.sqlite.org/isolation.html)と[Result Codes・517](https://www.sqlite.org/rescode.html#busy_snapshot)、[error API](https://www.sqlite.org/c3ref/errcode.html)、[transaction state API](https://www.sqlite.org/c3ref/txn_state.html)、[autocommit API](https://www.sqlite.org/c3ref/get_autocommit.html)を2026-10-06 JSTに確認しました。codeは失敗直後、別SQLより前に取得します。txn_stateの0/1/2はNONE/READ/WRITEです。エラーによる自動rollbackはエラー種別によって変わり得るので、今回取得したstateの範囲だけを述べます。

## 可変入力と検証

入力はexact schedule/initial/writer/delta/busy_msだけ。scheduleはstale/fresh/rollback/busy、initial/writerはexact int0..100かつ別値、delta1..10、busy_ms0..100。bool/float/余分key/非有限/重複JSON keyを拒否します。任意SQL・user path・実DBは受け付けません。writerが同値を書く場合はこの有限契約外です。

[事前literal oracle](expected-table.json)はproducer作成前に13固定schedule/row/code/stateを固定し、実装をimportして期待値を作りません。[checker.py](checker.py)は実SQL順序、failure数/code、回復、DB signature/hashを照合し、exportされた閉DBを所有tmpへ書いてPython wrapperのread-only immutable接続で最終行を独立SELECTします。5つのmutant（旧snapshot喪失、BUSYとの混同、失敗tx自動終了、旧値からretry、timeout名の捏造）を拒否します。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B runner.py --record
python3 -B server.py --record
python3 -B qa/check-ui.py
```

通常checker/runnerは所有tmp DBを作り、閉じて除去する実観測/照合です。unit内の全SHA256/mtimeは変えません。明示recordだけfresh UTC原票と実closed.sqliteを保存。旧失敗を上書きせず、source hash/Python version/native SQLite source ID/stdin/stdout/exit/SQL rows/code/state/header/WAL hash/closed DB bytesを結合します。closed DBは検証用の単独終了後コピーであり、稼働中のbackup/crash recoveryの証拠ではありません。native実行の想定外失敗はexecution_error・exit3、schema拒否はexit2、予定したSQL517/5は観測成功・exit0で分離します。

UIは予想→正常/昇格失敗・回復比較→原典/source/raw→actual答え。可変行値/scheduleを毎回実DBへ通し、返ったactual code/row/stateで本文を作ります。全例/予想/JSON変更と比較開始は本文・trace・結果・rawリンクを空にしdetailsを閉じ、新値保持。revisionでstaleを捨て、入力拒否/host失敗に正常答えを出しません。[実IAB QA](qa/README.md)にcapture・表示制限・cleanupを保存します。preview600ms遅延はstale QA用です。自分のloopback port0 server/tab/tmpだけを除去します。

## 未検証

多process、実service負荷、一般timeout挙動、他OS/NFS/他DB、crash/power-loss、復旧、autocheckpoint/shared-memory/B-tree内部、性能、完全な全入力証明は未検証。旧単位/Portal/Core/global/既存DB/listenerを変更しません。公開/commit/push/install/fullGateなし。第三有限unitとしてfreezeし中央受入を待ちます。
