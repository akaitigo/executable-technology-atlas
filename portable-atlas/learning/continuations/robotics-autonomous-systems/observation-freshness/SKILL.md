---
name: atlas-robot-observation-freshness
description: Atlasの固定観測列で時刻・version・期限・unknownと次edge候補判断を読む。実robotやNav2安全性の保証には使わない。
---

# Atlas — 観測の新しさを読む3問

[README](README.md)→[契約](CONTRACT.md)→[画面](index.html)へ進みます。実装前の[手追跡](expected.json)と、実行後の[保存結果](observations/run-01/results.json)、[実行時実装](observations/run-01/inputs/freshness.py)を区別します。前提は[mapとworld](related.html?doc=base)、[footprint](related.html?doc=footprint)、[制動](related.html?doc=braking)です。

1. **新しく届いたclearを採用してよい？** `reversed-clear` のnow6/7を比較。新到着でも観測時刻4/version1は古い。保守版はoccupied/採用v2/更新1を保持し、故障はfree/採用v1/更新2へ変わります。現実の障害物が消えたとは判断しません。
2. **拒否した観測が来れば期限は延びる？** `reversed-clear` now10/11と `expiry-boundary` now4/5を読む。期限は保持observedAtから測り、拒否で延長しません。age4と5、storedStateとeffectiveStateを分けます。unknownをfreeとみなしません。
3. **新しいunknownと未観測は同じ？** `explicit-unknown` now0/1と `expired-arrival` now10を比較。次edgeは不明で停止でも、保持根拠・version・age/freshは異なります。知識上のMOVE_ALLOWEDから実移動・幾何・制動の安全性を推論せず、[原典](SOURCES.md)と[未対応範囲](COVERAGE.md)へ戻ります。

資料と固定結果を辿る3つの有限利用例です。一般Agent評価や、未知の観測源/時計/実robotでも安全判断できることを実証しません。

3問の案内は保存結果と実行時実装へ独立に辿って確認しました。実画面の15時点30応答、前提とこのSkillへの実クリックは[画面確認記録への参照](qa/reader-acceptance.json)に保存しています。狭幅の左右別表示と公式原典の遮断確認という範囲を保ち、独立受入の現在値は[確認状態](qa/reader-acceptance.json)を参照します。
