# Failure Fallback

1. Release digestまたは署名が不正なら`quarantined`とし公開Indexへ入れない。
2. Schemaまたは横断契約が不正なら同様に隔離し、理由をImport Reportへ残す。
3. 取込全体が失敗した場合は生成中の一時Indexを採用せず、last-known-goodを維持する。
4. Search Indexを読めない場合は障害として表示し、空のDashboardを成功扱いしない。
5. JavaScriptが無効でも、SSRされた概要、Facet、最初の結果、完成契約を読める。

`fixtures/failure-scenarios.json`が改変、未知鍵、Certificate欠落、除外、実行困難、失効、更新済み、保守終了、fail/inconclusiveを固定する。
