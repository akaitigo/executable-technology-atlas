# 実証した範囲と次の問い

| 領域 | この教材 | 未対応・次の最小実験 |
|---|---|---|
| 入力生成 | 固定seed1/7・有限2/4件、uniform cycleとboundary | 実libraryの乱数、任意seed、分布の統計検査 |
| property | 有限整数集合仕様と正常版/M1/M2の照合 | 複雑な構造・状態・非同期predicate |
| shrinking | 規定候補順、失敗保持・schema拒否、局所停止 | 複数座標の連動候補・別順序を比較 |
| 最小性 | rankを固定した252組全列挙 | 無限領域の最小性・別rankとの比較 |
| 再現 | 全入力/全候補/全列挙、UTC、source hash | fast-check seed/pathの実replay |
| mutation | M1/M2と8つのchecker fault注入 | 自動mutation、timeout、compile invalid等の実runner |
| UI | 予想、全入力変更reset、stale/refusal、source、通信断 | 全browser・file URL・支援技術の検査 |
| 品質全体 | この純粋関数の契約だけ | integration、regression、fuzzing、性能、security、信頼性、CI |

生成反例なしを全入力passと呼ばず、局所停止をglobal最小と呼びません。境界生成の2件でもM1を逃す例があります。全252列挙の一致は指定した有限領域だけの検査です。全Software Quality Subject、QE Atlas、Coreの完成や学習者の理解を測っていません。
