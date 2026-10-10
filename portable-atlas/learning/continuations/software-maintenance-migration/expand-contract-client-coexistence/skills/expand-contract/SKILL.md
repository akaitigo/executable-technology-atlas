---
name: expand-contract
description: この固定SQLite教材で旧新client共存、bridge更新、cutover拒否、contract後の非互換を再確認する。
---

この単元のREADME→UI→oracle→原典を読む。通常verify.pyとroute.pyは読み取り専用。seed/expand/backfill/bridge/guard/contractでschema、全行、client出力を区別する。旧client廃止boolは合成入力。全行一致だけでcontractしない。EXECUTION_FAILUREを正常答えへ変換しない。本番DB、同時writer、zero downtimeを保証しない。明示record以外で原票を書き換えない。
