---
name: hash-collision-resize-cost
description: 固定mod整数keyのchainingと容量倍増を、実Python・list oracle・論理比較数とrehash移動数で学ぶ有限教材。
---

# hash衝突と拡張の有限実験

このskill内の教材ディレクトリは ../..。README、CONTRACT、hand-oracleを先に読み、予想を固定してからserve.pyの画面で同じ列を固定/倍増へ実行する。正常とdelete-whole-bucketを比べ、chaining.py、list_oracle.py、oracle.py、原票を読んでから答えを開く。条件変更で旧答えを使わない。

再現は教材ディレクトリでpython3 -B verify.py。既存原票を上書きしない。install、公開、他教材の修正は含まない。comparisonsとrehash movesは論理操作数であり実時間と呼ばない。負key、空、閾値等値、既存key更新とcollision中deleteを確認する。COVERAGEの乱択、縮小、open addressing、並行性、一般計算量の未対応を埋めたと扱わない。
