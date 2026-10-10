---
name: atlas-control-noise-robustness-confirmation
description: 制御2×noise2/各3合成反復で目標二乗lossと別fixture確認を比較する有限入口へ案内。SN/直交表/実物robust保証を扱わない。
---

[README](../../README.md)の予想→操作→2stage図→[一次資料](../../sources.json)/[実装](../../calculate.py)/raw→答えへ。[手表](../../hand-oracle.json)と[独立oracle](../../checker.py)のpairwiseばらつき/moment lossで検算。

[契約](../../contracts.json)の目標10/loss≤3/等noise/4cell各3整数だけ。selectionとconfirmationのID/全配列を分け、settingはselectionだけで固定。確認データで選び直さず、tieは確認未実行。copy拒否は教材replay防止で、値の違いだけで統計独立性を証明しない。

loss=bias²+V_N、s²_Nminus1ではない。分母6/5/2とarb/arb²を保持。loss0は有限0、SNや無限値へ置換しない。control/noise/signal、parameter/toleranceの違いを説明し、[COVERAGE](../../COVERAGE.md)のSN/直交表/物理noise/因果/独立性等未教材を残す。

[QA](../../qa/README.md)で明示reset/condition変更消去、stale/refusal、実画像、memory-only原票と保存snapshotを読む。server停止でRAM linkは失効、通常再試験はunitを記録しない。旧unit/QE/globalを書かず、全体系完成/実データ助言は拒否する。
