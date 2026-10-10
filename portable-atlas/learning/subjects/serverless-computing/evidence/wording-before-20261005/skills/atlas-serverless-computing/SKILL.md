---
name: atlas-serverless-computing
description: このAtlasのlocal serverless教材を既存runner/checker/UIで実行し、warm mutable state漏れ、request分離、idempotency store寿命を比較する。実cloudや課金functionには使わない。
---

教材rootはこのファイルから `../..`。README.mdの寿命の表と未教材coverageを読む。
正常/warm漏れは `python3 -B run.py`。cold/store消失は `--reuse cold-each --lifetime process-local`、1run共有比較は `--lifetime run-shared`。エラーは `--error handler-error`。独立state/result oracleは `python3 -B check.py`。
UIは `python3 -B server.py` のloopback URLで予想→操作→状態/result→原典→答え。所有serverを終了する。通常checkerはread-only。原票更新の依頼がある場合だけ `check.py --record`。
未対応cloud要求は `run.py --reuse live-cloud` の拒否で確認できる。実cloud deployment、課金function、cold-start測定、永続DBを要求されたら教材限界と区別してREADME coverageを案内する。新たなrunnerや外部設定を作らず既存コマンドへだけrouteする。
