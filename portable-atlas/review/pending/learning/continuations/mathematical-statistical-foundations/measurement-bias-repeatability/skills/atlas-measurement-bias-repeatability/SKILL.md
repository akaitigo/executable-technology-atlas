---
name: atlas-measurement-bias-repeatability
description: 合成参照2水準/固定操作者2/反復3のbiasとwithinばらつきを比較する有限MSA入口。実校正やinstrument認証には使わない。
---

[README](../../README.md)、[契約](../../contracts.json)、[手表](../../hand-oracle.json)、[COVERAGE](../../COVERAGE.md)、[原典](../../sources.json)を読む。

cell順10A/10B/20A/20B、biasと分母2のvariance、within SS/df8、全体混合分母11故障、固定operator差を分ける。予想→実child/1操作+2→正常/故障図→原典/原票→答え。閾値1/2は有限分類だけ。通常[runner](../../runner.py)/[checker](../../checker.py)はreadonly。明示採取だけ新UTC。過去raw保持、RAM停止で失効、新serverは新原票。

参照真値・traceability、不確かさbudget、実instrument、独立/無作為化/等precision、完全R&R・operator母集団再現性・製品工程変動は未実証。低ばらつきでbiasを代用しない。固定操作者差を分散成分へ変換しない。契約外診断は拒否。
