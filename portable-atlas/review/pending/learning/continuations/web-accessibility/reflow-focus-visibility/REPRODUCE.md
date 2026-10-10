# 新しい実測の採取

1. serverを起動し専用IAB tabを開く。viewport capabilityのdocsを読む。1000×800/320×800を一時set、client寸法が要求と一致することを原票で確認。実zoomは行わない。
2. 各条件を選択し予想を入力。開始点をclick、Tabを5回。毎回fresh native AX、activeElement、measurement JSON、native screenshotを保存。DOM原票のtrusted key/focus列と実Tab順を照合。送信でEnter、合成回数0→1を確認。
3. observations.jsonを明示記録、UTC/sourceSHAを付ける。通常UIはmemory表示のみ。保存比較を4条件で開き予想/条件reset、503、stale無視を確認。source/raw viewerと一次資料リンクを開く。
4. checker/負例/routeを読み取り実行して前後SHA・mtime不変を確認。viewport.reset、専用tab/server終了、保護listener維持。保存原票の再監査と新しいBrowser観測を区別する。
