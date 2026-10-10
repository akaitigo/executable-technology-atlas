# Atlas：実行したことと、まだ表示しないこと

初回は2026-10-06 21:39 UTCにcompiler1回/JVM1回を実行。compilerはexit0、JVMはexit1。plain-splitは最終1まで完了し、atomic-splitは2Futureの返値取得後、Executorの終了通知とThread.isAliveの確認が一致せず失敗として停止した。後2条件は未到達。値の期待拒否や、4条件成功として扱わない。

[初回の完全な実行ログ](observations/attempt-20261006T213941864766Z/run.json)、[完全stdout](observations/attempt-20261006T213941864766Z/runtime.stdout.txt)、[stderr](observations/attempt-20261006T213941864766Z/runtime.stderr.txt) を保存。両processのnice10、終了/所有group回収は確認済み。旧入力11件も変更前のbytesで保持した。

[失敗の切り分け](records/failure-analysis.json) は、固定JDKの終了通知位置と今回記録が整合することを示す。OSの正確な時系列まで断定しない。修正は所有Threadの終端を共有300ms期限のjoinで待つ限定変更で、期待値・Barrier・カウンター更新は不変。残存や割込は失敗のままである。

現在の実行回数と修正版の状態は [実行履歴](records/execution-history.json) と [状態記録](status.json) を参照。各runnerのretry0は自動再試行なしを表し、教材全体の累計実行回数とは分ける。修正版の完了済み4条件だけを画面へ接続する。初回失敗を成功へ上書きしない。

## Atlas の修正版の測定結果

2026-10-06 21:48 UTCの明示的な修正後実行は3.354秒、compiler/JVMともexit0。両nice10、所有process group回収と4条件すべての実Thread終端を確認した。新たな自動再試行はない。初回失敗＋修正版の累計はcompile2回/JVM2回である。

|条件|初期化回数|payload実参照|各workerの更新|最終値|
|---|---:|---|---|---:|
|plain-split|1|2worker＋mainが同じ|0→1、0→1|1|
|atomic-split|1|payloadとAtomicIntegerも同じ|個別get0→set1が2つ|1|
|locked-rmw|1|同じpayloadと専用lock|lock内の(0,1),(1,2)。勝者不固定|2|
|atomic-rmw|1|payloadとAtomicIntegerも同じ|返値集合{1,2}。old別読取なし|2|

[修正版の実行ログ](observations/attempt-20261006T214843032325Z/run.json) / [完全stdout](observations/attempt-20261006T214843032325Z/runtime.stdout.txt) / [122照合・10改変拒否](observations/attempt-20261006T214843032325Z/verify.json)。各条件で異なる実worker thread ID2つと各1更新を記録。回収順から全体時系列を再構成しない。

修正版ではjoin直前のaliveは全件falseだったため、joinが実際に待機する分岐はこの実行では未観測。共有300msの有限性はコード読取の根拠であり、待機分岐を実測したことにはしない。
