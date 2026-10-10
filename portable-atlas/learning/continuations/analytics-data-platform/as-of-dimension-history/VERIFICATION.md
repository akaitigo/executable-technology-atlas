# 観測と検証の区別

`observations/attempt-01/raw.json` は実際のSQLite実行、SQL、入力、UTC、環境、終了コード、記録時source hashを持つ。記録時とUI修正後のsource hashは別に保持する。`data.js` は同じ結果のUI用写像。SQLとオラクルは独立で、21tickの版台帳と注文ID手計算に照合する。境界t10、gap、unknown、overlap、無効区間、SQLite実行故障を含む。

`--seal-record` はUI QA後に現在source/artifact receiptを作る。初回receiptを別名で残し、生SQLを作り直さない。通常verify/routeは全結果の再計算・receipt照合だけ。UIは別の実観測として条件変更、予想だけの変更、拒否時保持、異常時比較停止、ソースリンクを試す。実際のIAB captureはツールに表示されるが、ローカル画像として保存できたことは主張しない。全ファイルhashとmtimeの前後一致をread-only-proofへ記録する。
