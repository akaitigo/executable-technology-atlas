---
name: atlas-wilson-wald-finite-coverage
description: n8・p=.1/.5/.9・丸めz1.96でWilson/Waldの9区間と全256列coverageを比較する有限教材へ案内する。実データ推定や個別助言には使わない。
---

[README](../../README.md)の予想→操作→2手法図→[NIST原典binding](../../sources.json)と実raw→答えへ進む。[手表](../../hand-oracle.json)と[独立checker](../../checker.py)でscore平方不等式/Fraction256列を読む。

[契約](../../contracts.json)のn8/p文字列.1/.5/.9/z文字列1.96/k整数0..8だけ。[COVERAGE](../../COVERAGE.md)の未教材を実装済と呼ばない。Waldをclipしない。Wilsonのbounded端点、丸めz、端点近似、exact mass/包含を区別。nominal95%を保証値へ、反復coverageを固定区間のposterior確率へ置換しない。

編集・予想・入力例のreset/stale/refusal/通信失敗は[QA](../../qa/README.md)。通常checker/runnerはunitのSHA/mtime不変。recordは明示時だけ新UTC証拠を追加。既存raw、元教材、他unit、Subject/Portalを変更せず、全体完了/公開/個別助言は拒否する。
