# Atlas｜配置条件の原典と既存教材への対応

目標は[97分野目標の47](../../../../2026-10-06/task-8/atlas-97-field-goals-ja.md)です。確認した目標ファイルのSHA-256は `1868f9e246b20c24dd7688fc44667dd3f361b72db9cd13856e64ead5ef5221c1`。171受入（旧127＋独立44）の索引では、同分野の追加はCPU・memory教材です。索引だけで未対応と決めず、下記の現実装を読取りました。

## 前提と今回の差



## 公式本文の狭い参照

2026-10-06に以下の公式本文をwebで読みました。第三者本文全体は保存せず、適用した条件と対象外だけを記します。

- [Kubernetes: Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) の冒頭とConcepts：tolerationは配置の許容で、配置保証ではない。Equalではkey/effect/valueの一致を使い、NoScheduleは新規配置の条件。今回の模型は明示した1taint・Equal・NoScheduleだけを扱います。
- [Kubernetes: Assigning Pods to Nodes — nodeSelector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector)：指定したlabel条件を満たすnodeへ限定する。affinity/anti-affinityは別節で、本単元へまとめて実装済みにしません。

これは公式本文の一部に基づく独自の有限模型です。Kubernetesの製品版を実行しておらず、将来の仕様全体や実schedulerのnode順序を保証しません。A→Bは原典の規則ではなく、比較を固定する教材の選択順です。
