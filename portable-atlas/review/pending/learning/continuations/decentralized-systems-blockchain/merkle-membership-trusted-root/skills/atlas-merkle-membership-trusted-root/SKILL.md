---
name: atlas-merkle-membership-trusted-root
description: synthetic4葉depth2の位置つきMerkle membershipと、独立保持を仮定した固定trusted rootを比較する有限教材。live chainや署名/consensus認証には使わない。
---

[README](../../README.md)、[契約](../../contracts.json)、[手表](../../hand-oracle.json)、[COVERAGE](../../COVERAGE.md)、[原典](../../sources.json)を読む。

予想→実JSON/同送tree再計算→fold/固定rootと同送root比較→原典/原票→答え。通常[checker](../../checker.py)/[runner](../../runner.py)はreadonly。明示採取だけ新UTC、旧raw保持、RAM停止失効。rootはrequestから信頼しない。

membershipは位置つきで値の一意性を証明しない。内容真/署名/認可/consensus/唯一履歴/root配布認証/実資産/汎用protocolは未実装。教材byte形式はNIST規定ではない。契約外の診断・公開は拒否する。
