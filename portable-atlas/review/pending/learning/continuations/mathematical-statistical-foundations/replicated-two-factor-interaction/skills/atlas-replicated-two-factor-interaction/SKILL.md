---
name: atlas-replicated-two-factor-interaction
description: 4cell各3合成反復でmain/interaction/within varianceとOFAT未観測cellを比較する有限教材へ案内。実因果/有意性/Taguchi SN直交表は対象外。
---

[README](../../README.md)の予想→操作→2図→[一次資料binding](../../sources.json)/実装/原票→答えへ。[手表](../../hand-oracle.json)と[独立OLS checker](../../checker.py)で係数倍率、rank、自由度、nested RSSを検算。

[契約](../../contracts.json)のunit arb/4cell各3/整数−20..40のみ。cell順/±1符号を保持しeffect=2beta、DOD=4betaAB、SS/MSEはarb²、within df8。crossoverは条件A符号反転で、main effect0を必要条件にしない。OFAT第4cellの−2等は予測のまま、観測へ付け替えない。

明示reset/condition変更で古い図・答え・traceを消す。[QA](../../qa/README.md)の実IABとmemory receipt snapshotへ戻る。serverはmemory-onlyで評価/GET時unitを書かず、原票は停止で失効。保存は明示runner --record/QA採取のみ。[COVERAGE](../../COVERAGE.md)の未実施を保持する。

合成反復を物理反復/無作為化/時間順序/因果/有意性へ置換しない。SSE0でもdf8、無限F/確実な効果を出さない。旧QE/global/他unitを変更せず、実データ/個別推奨/Taguchi SNや直交表は拒否する。
