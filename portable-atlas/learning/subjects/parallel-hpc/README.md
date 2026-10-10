# Parallel / HPC：2workerの整数和から分割と終了処理を読む

このSubjectは部分教材です。**実際のstdlib multiprocessing子process2個**で有限整数列を分割・計算・集計します。対象はローカルhostの正しさと資源回収。MPI/SIMD/GPU/clusterや性能優位は未実行です。

## 前提 → 主要概念 → 仕組み

半開区間 `[start, stop)`、整数、processと関数の違いを前提にします。主要概念はpartition coverage、partial reduction、spawn、IPC、deadline、owned cleanup、整数/floatの結合則。2workerへ `[start, midpoint)` と `[midpoint, stop)` を渡し、各workerがloopで整数を足す。親はworker別の一方向Pipeをwaitで受け、**両方成功したときだけ**partialを足します。worker例外はPipeでerrorを報告して正常に終了、timeoutは結果Noneです。全体deadlineはstart直後の起動処理を含めず、2個起動後から計測します。

各runのworkerは2個だけ。Pool/Manager/shared memoryを使わず、spawn contextとmain guardを明示します。成功でもfinallyでjoin。deadline後も生きていれば今回作ったProcessだけterminate→join、なお残ればkill→join。cleanup理由/exitcode/is_alive/PIDを原票に保存し、他のprocessへ触れません。terminate後のPipeは捨てるため、汎用queue/lock回復の保証にはしません。

## 予想 → 操作 → 正常/異常を比較

[画面](index.html)でケースとpartition方針を選び、timelineを前後へ進めます。最初に予測してください：7要素を `n//2` 個ずつ配ると何が抜けるか？ 子が失敗したとき届いたpartialを完成sumとして返せるか？ 空区間の子は必要か？

|ケース|balanced / drop-remainder|判断|
|---|---|---|
|even 1..8|36 / 36|偶数長ではbugが隠れる|
|uneven 1..7|28 / 21|最後の7を落とす|
|empty|0 / 0|空区間2workerも実起動・終了|
|single 5|5 / 0|1要素の端数が全て消える|
|signed −3..3|0 / −3|sum0だけでcoverage成功を判断しない|
|larger 0..999|499500 / 499500|小さな有限量。速度保証なし|
|worker-error|None / None|worker1の意図例外。partial0のみでも集計しない|
|timeout|None / None|両worker20秒delay、親deadline0.35秒で終了回収|

`drop-remainder`は意図的bugです。分割第2区間の終端を `midpoint + n//2` にし、奇数長の最終値を落とします。coverageそのものと独立閉形式 `(start + stop − 1) * (stop − start) // 2` を照合します。子の計算loop・親sum・閉形式の結果を分けて検査します。

## 実務判断 → 限界

正しさはsumだけでなく重複/欠落と件数も確認します。要素数の均等化は処理時間の均等化ではありません。error/timeoutで完成resultを返さず、owned子を回収するのが今回判断できる範囲です。記録elapsedはspawn/IPC/joinを含む局所wall timeの観測で、同時にCPU上で走った証明、速度優位、throughput、scaling、最大応答時間の保証ではありません。deadline後のcleanupには別のjoin猶予があり0.35秒で全処理が終わるとは主張しません。

Python整数は任意精度。固定 `[10**16, -10**16, 1]` は左/右順どちらも1ですが、float変換後は1/0になります。整数の結合則をfloatや固定幅overflowへ無条件に広げません。これは1反例で、補償和・数値安定性・MPI reductionの実測ではありません。

## 原典と実装へ戻る → 答え

[source bindings](sources.json)にはPython3.9 process/IPC公式資料のsection、float公式tutorial、Open MPI reduction、MPI標準目次、MIT6.172の測定/並列算法/cache講義、OpenMP5.2目次のlocatorを収録しました。実行環境Python3.9系への版対応を記録し、最新版defaultへ読み替えません。公式資料から実装との結びつきへ戻った後、上の表と画面で答えを確認してください。

[実装](parallel_sum.py) / [独立checker](verify.py) / [固定入力](fixtures.json) / [raw原票](observations/raw.json) / [UTC・環境・digest receipt](observations/receipt.json) / [検証記録](VERIFICATION.md)。

```sh
python3 verify.py --record  # 初回原票。明示更新だけ
python3 verify.py           # 実worker再検査、file書込みなし
python3 serve.py            # 動的127.0.0.1 URLを表示。検証後Ctrl-C
python3 route.py integer-sum
python3 route.py mpi-cluster
```

画面は保存原票を読み、操作でworkerを追加起動しません。通常checkerは実worker16runを順に再実行し、非決定のPID/elapsed/UTCを同一値と要求せず、決定的semantic結果とcleanupを検証。`--seal-record`は観測rawを維持したままQA/docsのreceiptを明示更新します。作者Skill quick_validate/routing smokeは独立AgentEvalではありません。

## Subject全体の未教材地図と次の実験

[coverage](coverage.json)と画面は主要10領域を示します。並列モデル、reduction、同期/IPC、測定/scaling、scheduler/load balance、cache/NUMA/memory、SIMD/OpenMP/GPU、MPI通信、stencil/線形代数、HPC運用/I/O/故障。各領域に概念と判断の問い・一次資料を対応させています。今回のsumはこの全領域の完成ではありません。

次の4本は未実行：固定仕事量差のload imbalance、float reduction orderとFraction誤差、IPC/chunk granularityの反復観測、taskIDに基づく有限failure retryの重複/欠落。具体的な問いと独立oracleの方向はcoverageに記録しました。規模を大きくする前に正しさ・回収・観測条件を揃えます。
