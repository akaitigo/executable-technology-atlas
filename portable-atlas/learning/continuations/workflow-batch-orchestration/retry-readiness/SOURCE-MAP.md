# Atlas — 既存範囲と原典の対応

前提の順は、元DAGの試行と成功/失敗 → 成功結果の再利用 → ready-capacityの完了/容量 → 既存の待機と予算 → 今回の分類・due・残予算の合同判断です。副作用の安全性が質問の中心ならAPI再送教材へ戻ります。



`retry-results-cache` / `response-loss`という別名の教材位置は、既知索引と元repo内の有限検索では特定できませんでした。不在とは断定せず、上記の実在する逐次DAG・成功再利用・API応答喪失の本文で重複を確認しました。

## 正式に読んだ一次資料

2026-10-06、[Apache Airflow 3.3.2 Tasks](https://airflow.apache.org/docs/apache-airflow/3.3.2/core-concepts/tasks.html)を正式web読取で確認しました。

- Relationships / Task Instances：上流成功とup_for_retryの区別。既存状態規則の根拠。
- Special Exceptions：再試行余力を使わず失敗させる場合の観点。
- Retry Policies / How it works / Composition with existing parameters：失敗別の方針と再試行上限を分ける根拠。方針で上限を増やすわけではない。
- Timeouts：1回の実行上限と別のtimeoutを混同しないための参照。今回の対象には追加しない。

[公式の例示実装](https://airflow.apache.org/docs/apache-airflow/3.3.2/_modules/airflow/example_dags/example_retry_policy.html)も読取りました。方針例は実際のHTTP呼出しを含みますが、本教材は外部要求を実行しません。原典本文・例示コードはこの段階では保存/転載せず、URL・版・locatorのみを記録しています。本文byte hashを取得済みとは記録しません。

TRANSIENT/PERMANENT、固定delay2、now>=due、B→Dの値7/14、故障のsticky blockedは独自の有限契約です。一般的な一時/永続故障の自動分類やAirflow互換性の証明にはしません。
