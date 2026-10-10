# CPU＋memory requestsとpod overhead — slot数で足りる？

[元Container Subject](../../../subjects/container-orchestration/README.md) README:68実験①を具体化した、Python stdlibの有限順序配置模型。nodeA CPU4/memory4、nodeB CPU4/memory2を固定し、pod順とnodeA→nodeBのfirst-fitを使います。実KubernetesやDockerを起動しません。

## 前提 → 読む順 → 予想

JSON、request、容量残量、Bound/Pendingが前提。元slots→今回CPU/memory二次元→[2server容量](../../performance-capacity-engineering/two-server-bounded-queue/README.md)と[FinOps unitcostの分母](../../finops-cost-engineering/unit-cost-denominator/README.md)へ進む。配置可能数、処理throughput、成功request数は別の分母です。

1. [事前literal](oracle.json)でremaining/placements/candidate gateを予想。
2. [UI](index.html)でBound数、Pending数、容量内かを選び→入力JSON→実Python処理→答えを開く。
3. memory-overhead→ignore-memory-fault→no-overhead、CPU制約、greedy-trapを比較。
4. Kubernetes原典→[model](model.py)→[独立checker](checker.py)の全assignment列挙→答え→[未実証](COVERAGE.md)。

## 独自整数unitと固定手表

CPU/memoryはそれぞれ独自整数unitで、millicpu/MiBへ変換しません。requestsは予約配置の入力、actual usage・limits・OOMを意味しません。各podのdemand=request+overheadを両resourceへ加算。正しいfirst-fitはCPUとmemoryの両gateが通る最初のnodeへ置く。置けなければPendingという正常模型結果です。

| 条件 | pod demand CPU/memory | placement | 最終nodeA remaining | Bound/Pending | 全列挙maxBound |
|---|---|---|---|---|---|
| 2pods request2/2＋overhead0/1 | 各2/3 | p1 A、p2 Pending | 2/1 | 1/1 | 1 |
| memory無視故障（同入力） | 各2/3 | p1/p2 A | 0/−2 | 2/0、容量違反mem6>4 | 1 |
| overhead0/0 | 各2/2 | p1/p2 A | 0/0 | 2/0 | 2 |
| 3pods request3/1＋overhead1/0 | 各4/1 | p1 A、p2 B、p3 Pending | 0/3 | 2/1 | 2 |
| greedy trap：p1 2/1、p2 2/4 | overhead0 | p1 A、p2 Pending | 2/3 | 1/1 | 2（p1 B/p2 A） |

固定順序first-fitは全般的な最適配置ではありません。trapは容量内だが最大数に届かない対照。各podをnodeA/nodeB/Pendingへ割り当てる全3^nを独立に列挙し、nodeごとのrequest+overhead合計でfeasible assignment/maxBoundを求めます。producer greedyや元slot matcherは共有しません。literalは候補gate・途中remaining・placementsも別に固定します。

入力は固定nodes（値も4/4と4/2）、algorithm first-fit/ignore-memory、pod1〜3件、ID p1/p2/p3重複なし、request各exact int1〜4、overhead各exact int0〜4、bool/float/nonfinite不可。negative/bool/fractional/nonfinite/duplicateID/unknown topology/schema不正を拒否exit2、placements/remaining未観測。malformed JSONは実子processのJSONDecodeError/exit3/stdout空。Pendingはexit0で、これらの拒否・実行失敗と分けます。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

recordのみ新UTC rawを保存し、旧runを保持。[CURRENT](CURRENT)の実modelと独立audit各子processのstdin/exit/stdout/stderr/UTC/source/artifact hashを照合します。通常runner/checker/routeはreadonly。[QA](QA.json)に実IAB/capture/全予想と編集入力の旧本文消去・閉鎖/条件reset/失敗/旧応答破棄を記録。

UIの編集JSONはPOSTで実Python模型と独立auditへ渡します。範囲を超えた入力を補正しません。予想単独変更は新値群を保持、編集入力変更も入力と予想を保持し、旧比較/図/trace/raw/答え本文を消して閉じます。条件変更は予想もreset。進行中応答はgenerationが変われば採用しません。QA限定query qaDelay=2000は応答を2秒保留する検査だけで、scheduler時間/実故障ではありません。正常UIは遅延なし。

## 原典 → 実装 → 答え

[Kubernetes Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)のRequests and limits / How Pods with resource requests are scheduled、[Pod Overhead](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-overhead/)の冒頭を確認。requestsとlimitsの役割、request合計へoverheadを含める観点を参照し、独自整数unit/first-fitを実schedulerのalgorithmや適合結果とは扱いません。

答え：CPU余裕があってもmemory request+overheadが収まらなければPendingになる。故障版のBound自己報告はmem6>4の容量違反なので成功にしない。first-fitのPendingと数学的最大配置数も分けて調べる。配置BoundはRunning/Ready、成功request、OOM回避や実可用性ではありません。

## 限界

実scheduler、taints/affinity/Ready、autoscale/probe、allocatable計算、limits/OOM/cgroups、usage計測、料金、複数container/RuntimeClass admission、分散API/競合は未実証。Core/fullGate/commit/push/公開は割当外。全Subject完成は主張しません。

## 可変入力の答え検査

答えはaudit.violationsの実node/resource/used/capacityから容量違反を記述します。greedy差はmaxBoundを達成するassignmentをpod入力順へ対応付けます。追加事前literal対照は3podでnodeA memory12>4、nodeB memory4>2、ID順p3/p1のgreedyでp3 nodeB/p1 nodeA。固定fixtureの6やp1/p2を任意編集入力の答えへ流用しません。旧262filesをrevisionsへsnapshot保存し、新sourceに新UTC観測を結びます。

可変3pod対照のalgorithmだけをignore-memoryからfirst-fitへ変更すると1 Bound/2 Pending、容量内になります。JSONの他欄と予想値を保持し旧答えを消すことも確認します。
