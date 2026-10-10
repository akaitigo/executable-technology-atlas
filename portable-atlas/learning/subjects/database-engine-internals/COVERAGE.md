# 有限教材Coverage

| Surface | 状態 | 根拠 / 未実施 |
|---|---|---|
| SQLite index追加前後の等価WHERE | observed | 実SQL、schema objects、raw EXPLAIN QUERY PLAN、結果16行 |
| 通常indexと式WHEREの境界 | observed | INTEGER固定合成fixtureでbucket+0を比較 |
| 結果multisetと順序の同値 | verified | 独立数学Oracle、欠落・重複negative |
| 画面の経路図 | explanatory | 保存planを模式化。物理訪問数の実測ではない |
| 実time benchmark / 性能勝利 | unlearned | 未計測 |
| 物理ページ / storage / WAL / crash recovery | unlearned | in-memory接続とplanでは未証明 |
| Expression index / covering index / optimizer全体 | unlearned | 普通の単一列indexのみ |
| PostgreSQL / 他DB / 他SQLite版 | unlearned | 実行なし |

既存Subject集合は変更しない。Subjectの完了状態をこの教材から昇格しない。
