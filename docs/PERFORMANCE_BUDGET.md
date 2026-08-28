# Performance Budget

97件fixtureで次をCI Gateにする。

- 初期Client JavaScript: 170 KiB gzip以下
- CSS: 50 KiB gzip以下
- 決定論的Router検索 p95: 100 ms以下（同一processで1000回）
- UIは12件ずつ描画し、全97件の検索可能性を失わない。
- 外部Font、画像取得、Analyticsを初期表示へ追加しない。

`npm run perf`が`evidence/reports/performance.json`を再生成し、超過時に失敗する。
