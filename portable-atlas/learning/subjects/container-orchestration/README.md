# 置く場所が、足りなくなったら？

2node（各2slot）の有限desired-replica配置モデルです。実JSONによる16条件では、故障後も残容量が足りれば再配置、容量が足りなければPendingになりました。容量filterを故意に抜くbad実装は「bound」と返してovercommitし、独立enumeration/invariant oracleが拒否しました。実Kubernetes・クラスタ・コンテナは起動していません。

## 学ぶ道筋

1. 前提：JSONと個数、revisionを読めれば始められます。Docker/kubectl/cloud accountは不要です。
2. 概念と仕組み：desired replica数を満たすmodel podをcreate/deleteし、healthと残slotのfilterを通した候補へbindします。node割当のBoundと未配置のPending、欲しい数と配置可能数を区別します。
3. 正常/境界/異常：[画面](index.html)で予想→入力→event→配置/独立検算→公式/実装→答えを確認。create/scale、故障・収まる/故障・Pending、回復、同入力のBAD、invalid入力の順で比べます。
4. 実務判断：故障後の余裕、Pendingの理由、無効入力をどう扱うかを問えます。「割り当てた」の自己報告だけを成功とせず、容量/health/ID集合/最大可能配置/既存healthy保持の制約を照合できます。
5. 限界：slotはCPU/memoryではなく、1pod1slotの独自単位。healthは合成boolean、故障unbindは即時、同IDを再利用、scoreは使用数/名前順です。実検出/eviction待ち、新Pod UID、実scheduler tie-break、並行API、Running/Ready、通信、耐久データは証明しません。
6. 原典と次へ：下の未教材Coverageと[sources.json](sources.json)から公式locatorへ戻ります。replica維持、配置可否、実Pod起動/Readyを同一視せず、今回だけで本番node台数やサービス可用性を判断しません。

## 読み取り・明示的な観測更新

このdirectoryで（Python stdlibとブラウザのみ）：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
python3 -u -m http.server 0 --bind 127.0.0.1
```

通常checkerはread-onlyです。serverが表示する動的portのloopback URLを開き、title「置く場所が、足りなくなったら？ — Scheduler Lab」とField ID `container-orchestration`を照合。終了時は自分のserverだけCtrl-Cで停止します。UI操作は原票再生で実experimentを起動しません。

観測更新を明示選択する場合だけ：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
```

runnerはtask-owned新runへ実JSONを書き/読みしてmodelを実行し、独立checkerの`--oracle-json observations/<run>`（stdoutのみ、read-only）を別processで実行します。oracleがbad2条件だけを拒否した場合に画面pointerを置換。旧runは残します。optionなしrunnerはexit1で無変更。外部インフラ/Pod/containersへ変更は行いません。

## 実観測と独立検算

current run [`20261005T061705657357Z-scheduler`](observations/20261005T061705657357Z-scheduler/observation.json)、UTC `2026-10-05T06:17:05.715714Z`–`06:17:05.748888Z`、CPython 3.9.6 / Darwin 25.1.0 / arm64、attempt1/retry0。モデルとoracleの[command](observations/20261005T061705657357Z-scheduler/command.json)、[oracle-command](observations/20261005T061705657357Z-scheduler/oracle-command.json)、[86 fileのartifact index](observations/20261005T061705657357Z-scheduler/artifact-index.json)を保持。初回model観測`20261005T061601539930Z-scheduler`も消していません（独立report追加前の84 file、旧成功観測）。

| 条件 | producer結果 | 独立oracle / 比較 |
|---|---|---|
| create / scale-up / scale-down | 2 / 4 / 1 Bound | 容量内、healthy割当保持 |
| node-failure-fit | node-bへ2 Bound | 2slot内で再配置可能 |
| node-failure-pending | 2 Bound + 2 Pending | 故障後最大配置数2 |
| node-recovery | 4 Bound | 直前の故障結果と1:1で入力が一致、healthy配置保持 |
| over-capacity | 4 Bound + 1 Pending | 最大配置数4 |
| both-down | 0 Bound + 2 Pending | 配置候補0、要求は残す |
| zero | 0個、outcome bound | 空の要求を満たす（可用性を意味しない） |
| stale-revision | blocked | revision/state/hash不変 |
| invalid-negative / invalid-bool / unknown-node / duplicate-pod | blocked | 値/型/固定topology/ID拒否、state保持 |
| bad-over-capacity | 5 Boundと報告 | node-a 3/2、capacity超過・feasible optimum違反でrejected |
| bad-failure | 4 Boundと報告 | node-b 4/2、capacity超過・feasible optimum違反でrejected |

正常9条件は2回目reconcileでchanged=false、state/revision/hash同一。Pendingが残っていてもstateは冪等です。拒否5条件は不正inputを補正せず現stateを保持。bad2条件は正常completionへ算入しません。

[独立oracle原票](observations/20261005T061705657357Z-scheduler/oracle-report.json)は全配置組合せを列挙し、健康な既存bindingを固定した容量内の最大配置数を算出します。producerのgreedy loopをimport/再利用しません。7テストで実16条件、event replay/revision/hash、冪等性、故障→回復入力binding、改変負例、desired0..6×health4種の28条件、raw/input/source/commandを検査。28条件は独立oracleの数学的有限検査であり、実製品28試験ではありません。

観測時のfile bytes SHA-256：

- [model.py](model.py): `a3a03a00e1886eb47f7a3fbcb6c35c9660dca599edd9a27bee73aaa9c33761fc`
- [experiment.py](experiment.py): `c495a4c384d215a59015aa73769850a765a9ddd0a559e6891a369c89c45c0380`
- [checker.py](checker.py): `202d8fdc91fe99602b4afdd80e6f681e1bc306f010307a8dbe37509428d1996e`

## 未教材Coverageと次の実験

以下4本は提案のみ、未実装/未実行です。製品検証には別の明示scope/実環境が必要です。

| 次の問い・主要概念 | 次の有限実験（未実行） | 公式locator |
|---|---|---|
| CPUは余るがmemoryは足りない？ requests/limits/allocatable | ① 合成2次元容量+requests/overheadを追加してslot数判定と比較。実runtime limits強制は別。 | [Resource Management / Requests and limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) |
| 空いても置けない？ taints/tolerations/affinity/topology | ② 合成制約を追加して、容量余裕ありPendingと障害余裕を比較。実scheduler policyは別。 | [Taints and Tolerations / Concepts](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) |
| Boundなら応答できる？ lifecycle/probes/Ready | ③ 合成起動・Ready・failure stateを分けてprobe不合格を比較。実kubeletは未起動。 | [Pod Lifecycle / Pod phase / Container probes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/) |
| どのreplicaへ送る？ Service/EndpointSlices/rollout | ④ 合成Ready endpoint集合とrolling切替を比較し、Pod数と到達可能数を区別。実ネットワークは別。 | [Service / Defining a Service / EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/service/) |

CSI/PVC/StatefulSetとデータ復旧、RBAC/authn/Secrets/admission、Deployment/PDB/DaemonSet/Job、autoscaling、CNI/DNS/NetworkPolicy、etcd/watch/resourceVersion/並行更新、observability、upgrade/backup、production reliability/性能も未教材。これらをslotモデルへ集約して対応済み扱いにはしません。

今回の概念の原典は[ReplicaSet / How it works](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/#how-a-replicaset-works)、[Scheduler / Node selection](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/#node-selection-in-kube-scheduler)、[Nodes / Node controller](https://kubernetes.io/docs/concepts/architecture/nodes/#node-controller)。2026-10-05に一次資料URL/locatorを確認し、第三者本文は保存していません。モデルの即時再配置やID維持を実Kubernetesの動作保証へ置換しません。

[実表示QA](qa/QA.md) / [module-local Skill](skills/atlas-container-orchestration/SKILL.md)。有限1教材であり、全Subject/Repository完成ではありません。
