---
name: atlas-near-plane-clip
description: この教材の正w・side/far内の近面clipを有理数で再現し、同次交点、divide後の面積と故障対照を検証する。GPUや全6平面clipには使わない。
---

2階層上が教材root。[契約](../../EXPECTATIONS.md)の入力範囲、境界包含、退化状態を読む。producerとoracleの算法を統合しない。交点のwを保持してからdivideする。外原頂点の廃棄やclipなしをclipの代用にしない。

教材rootで `python3 -B runner.py`、`python3 -B test_negative.py`、`python3 -B checker.py` を実行。通常モードは証拠を書き換えない。新しい原票には明示 `--record`、失敗も保存しcurrentを失敗へ付け替えない。UI変更は予想→実run→3方式/表→原典/実装→答えをブラウザ確認し、入力変更・保留失効・503も試す。図だけでなくraw/receiptと有理数座標を照合する。

[根拠](../../SOURCES.md)と[範囲](../../COVERAGE.md)に従い、有限CPU観測をD3D/GPU/全6平面/属性補間へ広げない。UNOBSERVED、拒否・退化・故障を残す。このSkillから公開やglobal installの権限を推定しない。
