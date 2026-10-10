---
name: atlas-frozen-baseline-control-limits
description: 有限合成baselineの固定管理限界と現在点を含む再推定故障版を比較する。実工程の安定/原因/確率判断には使わない。
---

[README](../../README.md)、[契約](../../contracts.json)、[手表](../../hand-oracle.json)、[COVERAGE](../../COVERAGE.md)、[原典](../../sources.json)を読む。対象は整数arb baseline4..12/monitoring1..8/宣言spec、母σ未知の未補正sample-s模型。

予想→実child操作→固定/故障の点signalとspec比較→原典/原票→答え。N−1、平方距離厳密境界、zero/N不足拒否を保つ。通常[runner](../../runner.py)/[checker](../../checker.py)はreadonly、明示採取だけ新UTC、RAM停止失効。QAは専有dirへ、既存親資料はread-only。

s/c4/I-MRを完成扱いしない。normality/independence/ARL/false alarm/工程安定/原因特定/工程能力は未実証。単一点が内側でもrun異常なしとは主張しない。契約変更や実工程診断は範囲外。
