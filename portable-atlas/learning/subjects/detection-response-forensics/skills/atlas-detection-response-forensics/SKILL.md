---
name: atlas-detection-response-forensics
description: Atlasの架空固定JSONログ教材で時間窓検知、到着順の見逃し、重複・不正時刻と証拠記録を比較する。実アカウント監視、攻撃や実端末forensics操作には使わない。
---

module rootはこのファイルから `../..`。[README](../../README.md) の道筋・ルール・限界を読む。

- 複数失敗後の成功を検知したい要求は、moduleで `python3 -B run.py --case normal` へrouteする。
- 到着順の見逃しを比較する要求は `--case late --mode arrival` と `--case late --mode event-time`。同じ固定入力でprocessing order、decision chain、alert idsを比較する。
- 時間境界は `--case boundary --window 30` と `--window 29`。重複/型不正/別userは `--case duplicate` / `invalid` / `other-user`。
- 視覚教材は `python3 -B server.py` の動的loopback URLで予想→操作→比較→原典/実装→答えを通す。自分が開始したserver/tabだけ終了する。
- 検査は `python3 -B check.py`（read-only）。明示的な原票更新の要求に限り `--record`。input hash、正規化、decision chain、source/artifact bindingと実実行時刻を確認する。
- 実アカウント監視、攻撃、実端末/実ログの収集・forensics・隔離は未対応。READMEのcoverageと公式locatorへrouteし、教材を実運用手順に転用しない。

alertは侵害確定でなく、hash一致は出所/真正性/chain of custodyの証明でない。main-agent routing smokeを独立forwardAgentEvalと呼ばない。新runner、依存追加、Docker、外部サービス、global install、module外の変更は不要。
