---
name: atlas-linux-systems-engineering
description: このAtlasの9bit permissions有限教材を既存runner/checker/UIで実行し、owner/group/other選択、supplementary、any-class許可bugを比較する。実Linux kernel、chmodやOS設定変更には使わない。
---

教材rootはこのファイルから `../..`。README.mdの学習の道筋とsubset、未教材coverageを読む。
正常/owner fallback反例は `python3 -B run.py`。other比較は `--principal other`。supplementary比較は `--mode 040 --principal supplementary`。searchは `--mode 001 --principal other --operation search --kind directory`。未対応rootは `--principal root`、ACLは `--security acl`（JSON rejected、exit2）。
独立手permissions matrixは `python3 -B check.py`。UIは `python3 -B server.py` の所有loopback URL。予想→操作→bits/trace→原典/実装→答えへ進み、所有serverを終了する。通常checkerはread-only。原票更新を指示された場合だけ `check.py --record`。
既存runner/checker/UIだけへroute。新runnerや実chmod/accessを追加しない。Linux runtime、root/ACL/capabilities、実pathname、OS設定の要求は未教材coverageと区別する。実file permissionは変えない。
