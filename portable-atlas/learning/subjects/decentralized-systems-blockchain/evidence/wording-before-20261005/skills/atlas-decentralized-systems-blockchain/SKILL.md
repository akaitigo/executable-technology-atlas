---
name: atlas-decentralized-systems-blockchain
description: Atlasの架空hash chainと残高validator教材で、正常送金・残高偽装・replay・金額境界を比較する。live chain、実資産、consensusやsmart contractの操作には使わない。
---

module rootはこのファイルから `../..`。[README](../../README.md) の道筋と限界を読む。

- hash一致でも不正残高が通る理由を学ぶ要求は、moduleで `python3 -B run.py --case normal` と `--case forged-balance` / `forged-conserving` へrouteする。naiveと完全validator、実blockとdecision chainを比較する。
- 金額境界は `--case all-spent` / `zero` / `negative` / `overspend`。改変や重複は `tamper-hash` / `tamper-link` / `replay`、未知口座は `unknown-account`。
- 視覚教材は `python3 -B server.py` の動的loopback URLで予想→操作→比較→原典/実装→答えを通す。自分が開始したserver/tabだけ終了する。
- 検査は `python3 -B check.py`（read-only）。明示した原票更新要求のときだけ `--record`。受理ledger、input/raw/source/artifact digest、実実行時刻を確認する。
- 実資産送金、live chain、consensus実装、smart contract実行や金融助言は未対応。READMEのcoverageと公式locatorへrouteし、教材を運用手順に転用しない。

hashの整合、業務規則、認可、分散合意は別条件。教材の完全validatorに署名/認可は含まない。main-agent routing smokeは独立forwardAgentEvalではない。新runner、Docker、外部サービス、依存追加、global install、module外変更は不要。
