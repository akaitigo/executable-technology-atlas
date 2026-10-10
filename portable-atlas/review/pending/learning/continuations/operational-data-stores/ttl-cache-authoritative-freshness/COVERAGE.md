# 有限範囲と未実装

固定15＋編集4条件。主timeline、inclusive故障、期限直前/等値/直後、TTL1/10、通知受領、同値新version、空cache、逆行clock、不正TTL、bool時刻、未知key、実model例外。編集TTL3/7、同時刻read/update/read、refill起点をproducer前の手表へ照合する。

全eventのSQL rows/UPDATE rowcount/SELECT rowcount/trace、source/cache/return version、TTL expiry、hit/miss、harness stale version/value、client source SELECT数を独立oracleで照合。clientとharnessの知識、期限と鮮度を別欄に保つ。通常CLIはmemory-only、UIはmemory receiptで原本DBをdiskへ作らない。

single key・逐次処理の合成イベント。実時間、実Redis/Cloudflare、負荷、stampede、eviction、競合/thread、durability、distributed consistency、本番TTL推奨は未教材。更新通知のネットワーク配信を測定せず、invalidateは明示合成event。既存KV/QE/global/受入snapshotは変更しない。
