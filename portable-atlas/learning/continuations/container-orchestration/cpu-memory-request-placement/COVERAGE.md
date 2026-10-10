# 元coverage → 今回 → 残範囲

[元Subject](../../../subjects/container-orchestration/README.md) README:68実験①。今回は固定CPU/memory request+overheadとfirst-fit、全assignmentの容量検算だけ。

| 未実証問い | 次の有限実験案（未実行） | 原典 |
|---|---|---|
| allocatable/RuntimeClassはどう設定されるか | admission入力とoverhead付与を別契約にする | [Pod Overhead](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-overhead/) |
| requestsとactualusage/limits/OOMは | 隔離runtimeとcgroup計測を別scopeで追試 | [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) |
| taints/Ready/autoscale/probes/affinityは | 元coverage実験②③を追加する | [元coverage](../../../subjects/container-orchestration/README.md) |

配置数から処理性能・成功unitcost・本番必要node台数を推定しない。
