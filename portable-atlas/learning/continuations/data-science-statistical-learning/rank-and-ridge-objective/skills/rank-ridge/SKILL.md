---
name: rank-ridge
description: この固定2特徴教材のrank、非一意OLS、ridgeの別目的を保存Fraction観測と独立閉形式で再確認する。
---

README→UI→hand-oracle→oracle→原典の順に読む。verify.pyとroute.pyは通常読み取り専用。rank(X)とrank(正則化係数行列)、RSSと罰則を区別。NON_UNIQUEは数学的結果でEXECUTION_FAILUREではない。実装solverをoracleへ共有しない。実データ性能、float安定性、λ選択を主張しない。明示record以外で原票を変えない。
