---
name: atlas-train-only-preprocessing
description: Route finite synthetic train-only standardization, heldout feature leakage and 1NN cohort questions to the existing checker and UI. Exclude production training, real data and generalization guarantees.
---

[README](../../README.md)を読み、既存有限runnerのみ使う。`python3 route.py preprocessing` はsupportedで `python3 verify.py` と[index.html](../../index.html)へ。通常checkerはfile read-onlyで、実fit/transform/1NNを再計算する。

原票更新を明示依頼されたときだけ `python3 verify.py --record`。QA観測rawを保持したreceipt更新だけなら `python3 verify.py --seal-record`。fit UTCは非決定なのでsemantic結果とparameter digestを照合する。

small/expandedでtrain-only平均[5,.5]分散[25,.25]予測A/A、leakedはA/B。zero varianceはscale1、exact distance tieは最初のtrain行。unknown feature version/order、bool/nonfinite/empty trainは拒否。unsupported `production-train` は[coverage](../../coverage.json)に戻り、新依存/外部API/個人data/運用を追加しない。作者routing smokeは独立AgentEvalではない。
