---
name: atlas-gitops-continuous-delivery
description: このローカル有限教材の宣言file revisionとreconcile loopを実行し、drift修復・観測・stale拒否・rollback・明示ignoreを比較する。GitやArgo製品・cluster操作は対象外。
---

教材rootはこのファイルから`../..`。README.mdとmanifest.jsonを読み、予想→操作→比較→原典/実装→答えへ案内する。

- 実行：rootで`python3 -B runner.py --case drift-restore`。caseはdesired-change、drift-restore、observe-only、stale-revision、rollback、ignore-note、manage-note、tampered-bytes、invalid-ignore、invalid-state。
- 検算：`python3 -B checker.py`。read-onlyが通常。原票更新を明示された場合のみ`--record`。
- UI：`python3 -B server.py`の専用動的loopback URLを開き、実traceのstepを比較。専用serverを終了する。
- Git操作、実Argo/cluster deployment、Docker、認証、署名、prune操作の依頼は未対応としてREADMEのcoverageとsources.jsonへ案内する。他Subjectや旧repoへrouteしない。

managed一致、exact一致、健康を区別する。rollback-v3は古いpacket再送ではなく前内容を新generationで宣言する模型仕様。独立oracle一致を実製品の実証と呼ばない。
