# 未教材と次の実験

元[Cloud Subject](../../../subjects/cloud-architecture/README.md)のReliability / data候補に対応する有限lag/partition/read比較。元Subject・Portalは変更しません。

|未実証の問い|次の有限実験（未実施）|一次原典locator|
|---|---|---|
|配送の重複・順序逆転をどう扱うか|duplicate/gapを明示入力しrevision規則と拒否を比較|[REL05-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_mitigate_interaction_failure_graceful_degradation.html)|
|永続化前後のcrashで何を失うか|専用local processとfileを使いack境界/再起動後状態を検査|[REL12-BP04 failure injection](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_testing_resiliency_failure_injection_resiliency.html)|
|検知と復旧までの時間はどう測るか|専用process停止/復旧で観測起点・timeout・復旧条件を保存|[REL10-BP01](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html)|

quorum、consensus、durability、RTO、実cloud、TCP、性能・可用性割合は未実証です。AWS文書は設計視点で、今回の独自replication規則の仕様根拠ではありません。
