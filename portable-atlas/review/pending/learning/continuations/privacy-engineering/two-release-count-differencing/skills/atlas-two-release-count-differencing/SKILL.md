---
name: atlas-two-release-count-differencing
description: 合成A/B/Cの2release countと与えられた対象追加前提から、有限背景変更候補を全列挙してcategory一意/曖昧/不整合を比較。実人物linkageや法判断には使わない。
---

[README](../../README.md)、[契約](../../contracts.json)、[手表](../../hand-oracle.json)、[COVERAGE](../../COVERAGE.md)、[原典](../../sources.json)を読む。

対象追加/残存はgiven。背景add/delete各≤2、delete≤before、対象/新record削除なし。全count-vector候補最大300を[checker](../../checker.py)/[runner](../../runner.py)で検算。予想→背景前提1操作→候補と誤推論比較→原票/原典→答え。0候補はinconsistent、曖昧は安全保証でない。witness数を確率にしない。

通常readonly/memory-only、明示採取だけ新UTC、過去raw保持、RAM停止失効。旧RR/元教材はread-only。実人物/外部dataset/公表/法適合/DP保証/対象存在推定は範囲外。有限前提からcategoryが一意でも現実再識別率を主張しない。
