# 実行済み範囲と主要未教材

有限教材のdenominator：6 order / 6 line / 2 dimension row、指標1、8方式・16 SELECT。分野全体の件数へ算入しません。

実行済みは、order/line fan-out、preaggregate/EXISTS、DISTINCT value collapse、未知/NULL dimension、既知0・全NULL・空集合、固定手集計によるgrain/lineage/結果照合、read-only checkerと原子的原票保存です。

未教材の道筋は[READMEの次の実験](README.md)へ。dimension履歴→as-of JOIN、data quality→orphan/NULLの拒否・隔離・保持、incremental ETL→重複batch/idempotency、plan/性能容量→index前後の同値query比較の4本は、問いと公式locatorだけを準備し未実施です。

その他の主要未教材：実DWH/lake/BI製品、columnar/partition、分散query・分散ETL/ELT・orchestration・streaming、schema evolution、catalog/lineage管理、semantic layer/metric governance、dashboard、権限/privacy、cost/性能容量・障害回復・本番運用。実SQLite結果を製品/全分野の証明へ流用しません。
