# TTLとauthoritative原本の鮮度

原本の実SQLite行とcacheを分け、fake monotone integer clockでhit・期限・versionを比較する。[既存KV学習経路の実験3](../../../subjects/operational-data-stores/LEARNING_PATH.md)の独立した続き。既存のKVやHTTP/Cloudflareキャッシュを実行・変更しない。

このディレクトリで `python3 -B server.py`、表示URLのindexを開く。返却値と鮮度を予想→条件/TTL/policy操作→「SQLとcacheを比較」→実行済timelineのevent step→client/harness/SQL原票→原典/source→答え。event stepは実子processが実行した全eventのmemory表示を辿る操作で、別々の実時間eventを送る操作ではない。

|fake時刻|処理|原本|cache期限|返却と意味|
|---|---|---|---|---|
|0|read/fill|red v1|5|MISS red v1|
|2|原本UPDATE、通知欠落|blue v2|5のまま|cacheはred v1のまま|
|4|read|blue v2|5|HIT red v1、harnessではstale|
|5|read/refill|blue v2|10へ再設定|strictはMISS blue v2|

故障inclusiveはt5もHIT red v1、期限切れもversion違いも成立する。TTLを短くするとmiss/refillが増え、長くすると古いversionを返す期間が伸びる、この操作列での比較。全workloadの性能傾向や最適TTLの推奨ではない。同値redへUPDATEしてもversionは上がるのでvalue差とversion差も区別する。

clientはcache hit時に原本versionの更新を知らない。画面のharness原本auditはclientへ通知されない。cache stateへauditの未受信情報を混ぜない。失効通知が届く対照はinvalidate eventで明示する。期限はfill/refill時のfake時刻+TTL、等値clockは許可、逆行/不正TTL/未知keyはSQL開始前に拒否。

`python3 -B runner.py` はmemory-onlyで全条件を実SQL実行、`python3 -B checker.py` は保存rawのread-only監査、`python3 -B test_negative.py` は負例監査。`runner.py --record` の明示記録だけがraw/currentを書き、成功前にcurrentへ昇格しない。[教材内Skill](skills/atlas-ttl-cache/SKILL.md)で再採取する。global install不要。

SQLite UPDATE/SELECTは実処理。cache policy・fake clockは独自模型で、SQLite/Redis製品のTTL保証ではない。単一key・単一connection・逐次autocommit :memory:。競合/thread/実clock/Redis/負荷/eviction/stampede/Cloudflareは未実装。全cache保証・本番保証・分野完成・accepted数の加算は主張しない。Core/fullGate、公開/install/commit/push/課金/設定変更は対象外。
