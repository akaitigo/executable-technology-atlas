# Atlas｜Unicode編集の原典と前提

2026-10-06に次の公式本文を読取りました。本文・第三者画像の転載はせず、狭いlocatorを記録します。

| 原典 | 適用箇所 |
|---|---|
| [UAX #29 rev43、Unicode15.1](https://www.unicode.org/reports/tr29/tr29-43.html#Grapheme_Cluster_Boundaries) | §3：操作ごとのtailoring、GB9の結合文字/ZWJ、GB11のemoji ZWJ、GB999のその他の境界。EGCを普遍的なBackspace動作としない |
| [UAX #15 rev58、Unicode18.0](https://www.unicode.org/reports/tr15/tr15-58.html#Norm_Forms) | §1.2 NFC/NFD、§3正規化の安定性。e+0301とéの固定対照 |
| [ECMA262 2025 String.normalize](https://tc39.es/ecma262/2025/multipage/text-processing.html#sec-string.prototype.normalize) | 指定した正規化形を削除前に適用する |
| [ECMA402 2025 Segmenter](https://tc39.es/ecma402/2025/#sec-intl.segmenter.prototype.segment) | granularity=grapheme、Segment Data Objectのindexがコード単位offsetであること |

最新UAX29 URLは確認時点でrev49/Unicode18.0でした。比較の根拠は固定rev43で、Nodeがその版そのものを実装すると仮定しません。実Node/ICU/Unicode版は初回実行結果へ保存します。U+0041/U+0042/U+0065/U+00E9/U+0301、U+1F600、U+1F469/U+200D/U+1F4BBの有限入力に対し、literal境界と正規化結果が一致することだけを受け入れます。



- `learning/subjects/cross-platform-client/README.md:9/36`、`validator.mjs:2–7`：正規化なしのscalar/byte契約。E2の削除/正規化が次の問い。
- `learning/continuations/cross-platform-client/swift-character-scalar-wire-units/README.md:5/20/28`、`Wire.swift:6–10/37–44`：実Character/scalar/UTF16/UTF8計数とJSON往復は既存。正規化APIと削除操作は追加。
- 97目標文書 `2026-10-06/task-8/atlas-97-field-goals-ja.md:528–537` の目標44。

162件の受入照合後に既存範囲を差し引きました。専用segmentation教材の別pathは調査範囲で未特定であり、不存在とは断定しません。元ownerの現在状態は未確認、共有統合は行いません。Skillは前提2本文→今回の操作→保存結果→原典/範囲へ案内します。
