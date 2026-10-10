---
name: atlas-computer-architecture-digital-systems
description: 有限read-only direct-mapped cache教材のblock/index/tag/eviction raw traceと正常・tag省略異常の比較へrouteする。実CPU測定、write cache、HDLやcoherenceの検証には使わない。
---

# Logical cache教材

教材rootはこのdirectoryの`../..`。[README](../../README.md)で既存入口、[Coverage](../../COVERAGE.md)でgeometry/address/traceの有限境界を確認する。

- 保存観測は[run](../../evidence/run.json)の時刻・環境と[raw](../../evidence/stdout.json)へroute。0→16→0→16、16B/line4Bで正常0 hit/4 miss/3 eviction、tag省略版3 hit/1 miss/誤byte2。実Mac CPU cacheやcycle実測とは呼ばない。
- CLIの通常操作は`python3 -B check.py`、customは`python3 -B check.py --input-json '{"capacity_bytes":16,"line_bytes":4,"address_bits":8,"addresses":[0,16,0,16]}'`。拒否はexit2。`python3 -B verify.py`は手計算＋独立enumeration検査。checker／optionなしobserveはread-only。
- 原票更新の明示依頼がある場合だけ`python3 -B observe.py --write-evidence`を使い、その後verify/UI reload。未再観測を最新の実測にせず、成功に合わせてEvidenceを自動更新しない。
- [UI](../../index.html)は予想→read step→bit分割/指定行→正常・異常比較→原典/実装→答え。任意input実行はCLI。[cache.py](../../cache.py)と[独立oracle](../../verify.py)が実装、[trace図](../../evidence/conflict-trace.svg)は再描画でcaptureではない。

無効inputの結果なしと空traceの正常0readは区別。tag-mismatchすべてを3Cのconflict missとは呼ばず、中心traceで再訪blockが他行空きでもmissする事実を示す。異常版hit率を性能改善とは扱わない。

実CPU測定、write-through/write-back、associativity、JIT/HDL/coherence等は具体的に未対応と回答。新依存・外部サービス・OS設定・global Skill install・公開へ勝手に拡張しない。
