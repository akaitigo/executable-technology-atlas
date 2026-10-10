# PruneLast単元の対応範囲

分野ゴール62と、前単元 `argocd-prune-order` のPruneLast未対応を引き継ぐ独立単元です。通常pruneの待機・失敗readerは前単元で扱い、この単元ではwave計画の上書きへ絞ります。

|問い|今回の根拠|未確認・模型外|
|---|---|---|
|どの段階でPruneLastを考えるか|固定版1014–1058行を再利用。通常pruneの対称交換後。|その他の生成task・依存調整との全相互作用。|
|上書き先はapply最大値+1か|pruneも含むSync最大値で9になる基本例。|task集合が動的に変わる実行ループ。|
|全体指定と資源単位指定は同じか|global/resource-onlyを同じ元task集合で比較。|annotation文字列解析、target/liveの選択全経路。|
|全waveが負ならどうなるか|初期値0を残し候補1になる手計算例。|異常値・任意manifestの取り込み。|
|PreSyncの大waveやphaseは変わるか|PreSync wave20をSync最大値から外す。pruneのphaseはSyncを保持。|PostSync等のphase混在、hookの実行結果。|
|同waveの資源は順に完了するか|同じ組として表示し、完了順を主張しない。|並行処理・依存・API完了時刻。|
|Healthや削除完了を保証できるか|今回は計画だけで、Healthは入力にも結果にもない。|controllerの待機/失敗/retryと到達条件、実資源消滅。|
|学習と検証を再現できるか|CLI5件、手計算5ケース/18入力、拒否10、出力改変検出5。reader状態38/拒否7、実GUI20確認、実DOM5ケース全項目一致、1280/390pxの7capture目視。|独立受入は別reviewerの記録で確認。LIVEは未実施。|

次の不足は削除確認・削除保護と、Healthを含む到達条件の切り分けです。現在waveの確認ゲート4ケースの次案をNEXT.mdに記載しました。統合・公開・受入カウントの加算は行っていません。
