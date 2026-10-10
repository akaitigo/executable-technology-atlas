---
name: atlas-parallel-hpc
description: Route local finite two-worker integer sum, partition, timeout and cleanup questions to the existing parallel-hpc checker and UI. Exclude MPI, SIMD, cluster provisioning and performance guarantees.
---

既存の有限教材だけを使う。新worker実装、cluster、外部依存、性能保証を追加しない。

1. [README](../../README.md)で前提・限界を読む。
2. `python3 route.py integer-sum` のsupported routeは `python3 verify.py` と[UI](../../index.html)。通常checkerはfile read-onlyだが、各runで自分のspawn worker2個を起動し終了する。全16runを順に行い、同時worker上限2。
3. 原票更新を明示依頼されたときだけ `python3 verify.py --record`。実IABが観測した原票のhashは上書きしない。QA後のreceipt更新は `python3 verify.py --seal-record` が観測済みrawを保持して行う。
4. `mpi-cluster`等はunsupportedを返し[coverage](../../coverage.json)へ戻る。MPI/GPU/規格/cluster管理や速度優位へ広げない。

balanced uneven1..7は28、drop-remainderは21（7欠落）。worker-error/timeoutはparallel_result None、完成sumとして扱わない。Python整数1/1とfloat1/0の結合則境界を区別する。elapsedは今回の観測のみ。Skill validation/作者routing smokeは独立AgentEvalではない。
