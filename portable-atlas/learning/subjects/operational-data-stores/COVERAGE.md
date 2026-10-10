# 有限KV教材Coverage

| Surface | 状態 | 根拠・残範囲 |
|---|---|---|
| blind read/write lost update | observed | 実2connectionの固定statement順序、最終値1 |
| version CAS conflict拒否 | observed | 実UPDATE rowcount0、明示再読込みと再計算 |
| expectedversion/type/unknown key | observed | 6 API拒否入力、未知key・古いversion0行更新 |
| 同じkey lifetimeのABA | observed | 値が戻ってもversion3、stale更新拒否 |
| delete/recreate ABA | observed-limitation | version再利用は保護しない。generation token未実装 |
| UI状態図 | explanatory replay | 原票step/state_afterの可視化 |
| KV全機能・TTL・expiration・eviction・cache | unlearned | この整数KV pack外 |
| Document / graph / secondary queries | unlearned | 未実装・未観測 |
| Redis製品・他backend | unlearned | 実行なし |
| 実locking・parallel性能・atomicity全schedule | unlearned | 固定逐次操作のみ、thread/lock計測なし |
| 分散CAS・replication・failover・durability | unlearned | 単一process in-memory fixture |

既存Subject集合を変更しない。この1教材の通過でOperational Data Stores全体をcovered/completeへ昇格しない。
