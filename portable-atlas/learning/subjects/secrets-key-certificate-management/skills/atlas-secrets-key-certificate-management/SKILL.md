---
name: atlas-secrets-key-certificate-management
description: 公開dummy鍵によるAtlasのversioned HMACローテーション教材を実行し、権限・MAC・期限の結果を比較する。実秘密、実証明書、KeychainやCAの操作には使わない。
---

このSkillのmodule rootはこのファイルから `../..`。まず [README](../../README.md) の学習の道筋と限界を読む。

- v1発行・重複検証・v2発行・v1失効を学ぶ要求は、moduleで `python3 -B run.py --phase initial --version v1`、`--phase overlap --version v1`、`--phase overlap --version v2`、`--phase revoked --version v1` へrouteする。
- 境界は `--now 109` / `--now 110`。意図異常は `--fault tamper` / `unknown` / `input`。実MAC、version、権限、固定時計を説明する。
- 視覚教材は `python3 -B server.py` の動的loopback URLを開く。予想→操作→比較→原典/実装→答えを通す。自分が開始したserverだけを終了する。
- 検査は `python3 -B check.py`。通常はread-only。原票更新が明示された場合だけ `--record` を使う。記録時刻と固定モデル時計を混同しない。
- 実秘密の移行、実Keychain、実CA、実証明書の更新や失効を求められた場合は、この教材では未対応と説明し、READMEのcoverageと原典へrouteする。dummyモデルを実運用手順に転用しない。

新runner、外部サービス、Docker、依存追加、global installはこの教材に不要。module外を変更しない。既存の実装/原票を比較し、失敗を隠さない。main-agent routing smokeは独立forwardAgentEvalと呼ばない。
