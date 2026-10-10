# 教材Coverage / 説明モデルの境界

| 観点 | 今回の実行 | 境界 |
|---|---|---|
| State machine | 2 process / pc / owner | 原子的stepを宣言した独自モデル |
| 正常safety | atomic check-and-enterの全到達状態 | 実CPU atomic命令への写像は未検証 |
| 異常比較 | split check / guardなしclaim | 意図的な欠陥、最短6 transition |
| 全探索 | BFSが到達集合のfixed pointまで探索 | 値domainとprocess数は有限 |
| Counterexample | source/target/action/processを保存 | 保存graph内の最短、他モデルの最短ではない |
| 検査方法の照合 | Cartesian domainから集合展開しBFSと照合 | 同じtransition関数に依存、独立形式証明ではない |
| Safetyとliveness | safetyを検査、飢餓の可能なscheduleを説明 | temporal property / fairness model checkは未実施 |
| Visual | 実graphを使う状態操作・trace再生 | UIは保存観測の再生、実threadを操作しない |

## Refinement gap

実コードが`check-and-enter`を分割したり、言語/CPUのmemory orderingを満たさなければ、正常モデルの仮定から外れます。モデルのsafety成立をそのまま実装へ移すには、concrete stepからabstract stepへの写像と、guard・atomic性・可視性を保つことを証明または試験する必要があります。今回その写像は実装していません。

## 未教材範囲

Peterson、Bakery、TLA+/PlusCal/TLC、Lean/Coq、temporal logic、fairness、deadlock一般検査、weak memory、state explosionとpartial-order reduction、parameterized verification、refinement proof、分散protocol、OS mutexの実装/性能/障害。利用者の理解度は測定していません。
