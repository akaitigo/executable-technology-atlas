---
name: atlas-partial-apply-recovery
description: 保存された合成JSONのpartial apply原票で、失敗直後のstateとrefresh/replan復旧を学ぶ教材限定Skill。本番Terraform・cloud適用やrollback保証には使わない。
---

# Partial applyを原票で学ぶ

[README](../../README.md)の前提/予想→段階操作→正常異常比較→原典/実装/raw→答えを案内する。[contracts](../../contracts.json)と[原典locator](../../sources.json)を読む。通常[checker](../../checker.py)と閲覧はread-only。明示採取を依頼された場合だけ[runner](../../runner.py) --recordを使い、新runを保存する。failure後storeを初期化して成功扱いしない。

[route](../../route.py)：正常apply→normal、変更前failure→before-second、変更後failure→after-second、盲目replay→blind-replay、再観測と復旧→refresh-replan、原票検算→checker.py。前faultはbaseだけ、後faultはbase/configが残る。blind create replay拒否と、同じ宣言から新planを作るreconcileを分ける。exit、stderr、partial、refresh、recovery actions、2回目no-opのfile hash/mtimeへ戻る。

実Terraformを適用、cloud resource変更、rollback保証、分散transaction検証は未対応と答え、READMEの残る実験へ案内する。JSON模型を実provider/rollback/transaction保証へ一般化しない。元教材97入口・他module・Portal・利用Node PID3901/port53478を変更せず、次実験を自動開始しない。
