---
name: atlas-embedded-firmware-rtos
description: Atlasの有限ISR/main loop教材でlost update、critical sectionとIRQ deadlineの境界を比較する。実firmware、実RTOS/device操作やSafety検証には使わない。
---

module rootはこのファイルから `../..`。[README](../../README.md) の道筋・合法schedule仮定・限界を読む。

- main read後の割込みでcounterが欠ける理由を学ぶ要求は、moduleで `python3 -B run.py --schedule preempt-main --mode naive` と `--mode critical` へrouteする。
- 正常順は `--schedule main-first` / `isr-first`。全6順序のうちISR途中のmain実行3件はこのモデルでは未対応として拒否。
- deadline境界は `--mode critical --hold 3 --arrival 1 --deadline 3` と `--hold 4`。mask終了境界は `--hold 3 --arrival 3 --deadline 1`。operation stepとlatency tickを別のモデル単位として説明する。
- 視覚教材は `python3 -B server.py` の動的loopback URLで予想→操作→比較→原典/実装→答えを通す。自分が開始したserver/tabだけ終了する。
- 検査は `python3 -B check.py`（read-only）。明示的な原票更新要求に限り `--record`。独立oracle、raw event timeline、digest、実実行時刻を確認する。
- 実firmwareへのflash、実RTOS/device timing測定、Safety保証は未対応。READMEのcoverageと公式locatorへrouteし、モデル値を実測として扱わない。

critical保護のcounter正しさとdeadline達成は別条件。main-agent routing smokeは独立forwardAgentEvalではない。新runner、Docker、外部サービス、依存追加、global install、module外変更は不要。
