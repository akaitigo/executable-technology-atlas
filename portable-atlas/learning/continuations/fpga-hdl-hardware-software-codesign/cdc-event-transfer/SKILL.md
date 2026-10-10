---
name: atlas-fpga-cdc-event-transfer
description: Atlasの固定5例から理想2クロックのsample、2FF、level/toggle検出を読む。物理CDC安全性や実RTLの検証には使わない。
---

# Atlas — 事象転送を読む3問

[README](README.md)→[契約](CONTRACT.md)→[画面](index.html)の順に読みます。実装前の[手時系列](expected.json)、実行後の[保存結果](observations/run-01/results.json)、[実行時実装](observations/run-01/inputs/cdc.py)を区別して読みます。[counter](related.html?doc=counter)と[ready-valid](related.html?doc=ready-valid)の前提へ戻れます。

1. **2FFなら短いpulseも届く？** `short-pulse` と `held-level` のsample列を比較。前者の1は宛先edgeの間だけなのでsampleは全0。後者は複数回1をsampleしても立上り検出はt=9の1回です。2FFを置くことと事象を保持することを分けます。
2. **toggleなら何回でも数えられる？** `toggle-single` / `toggle-spaced` / `toggle-close` を比較。近接2反転は宛先から全0に見えます。送信件数と未観測数は教学側の診断です。間隔12の成功を一般の最小間隔保証にしません。
3. **t=9から13まで出力が1なら何件？** 保持中のsource t=10,12を読む。検出数はdestination edge直後だけで増えます。未検出の遅延nullを0に置き換えません。MTBFや実装安全性を尋ねられたら[原典](SOURCES.md)と[未対応範囲](COVERAGE.md)へ案内し、理想0/1計算から保証しません。

これは資料と固定保存値を辿る3利用例です。保存readerでは条件・予想・100時点を実pointerで選び、前提5本文とSkillを含む文書への導線を確認しました。狭幅で波形の右側を読むと信号名が画面外になるため、左右を往復して照合します。一般Agent評価、未知の回路の正しさ、すべてのclock比やresetを扱えるという評価ではありません。
