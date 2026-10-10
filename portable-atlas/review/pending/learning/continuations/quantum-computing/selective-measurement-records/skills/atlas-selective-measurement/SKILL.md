---
name: atlas-selective-measurement
description: この教材の1qubit Z射影のσ・確率・条件付きdensityと記録破棄ensembleをexact算術で再現し、正規化・重み・zero branchを検証する。実機測定や一般POVMには使わない。
---

2階層上の教材rootで[契約](../../EXPECTATIONS.md)を読む。σk、pk、conditionalを別に保持し、pk0ではconditionalをnullにする。到達不能branchを測定全体の不正と扱わず、zero割りは別faultで示す。record指定は説明用で実shotでない。

weighted ensembleと直接diagonal mapを独立に照合し、H後は全densityを比較する。biased入力はH後の確率だけが一致する等重み故障の反例。conditional正規化とensembleの重みを一つの処理へ潰さない。oracleの成分閉式をproducerの汎用行列helperへ統合しない。

`python3 -B runner.py`、`python3 -B test_negative.py`、`python3 -B checker.py`を実行する。通常modeはread-only、原票更新だけ明示--record。UI変更では予想→record/JSON→branch/ensemble/fault全density→原典/実装→答えを実ブラウザ検査し、編集失効・保留旧結果・503も確認する。

[根拠](../../SOURCES.md)と[範囲](../../COVERAGE.md)に従い、exact CPUを実機shot/一般POVM/量子優位性へ拡張しない。このSkillから公開やglobal installの権限を推定しない。
