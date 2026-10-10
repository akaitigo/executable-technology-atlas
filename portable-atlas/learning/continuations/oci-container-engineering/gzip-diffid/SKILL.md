---
name: atlas-oci-gzip-diffid
description: Atlasの固定gzipとDiffIDの保存結果を案内し、descriptor・展開上限・信頼の境界を分ける。
---

# Atlas｜gzipとDiffIDの資料を使う

[前提の非圧縮tar](related.html?topic=oci-base)→[契約](CONTRACT.md)→[実装前期待](expected.json)→[保存計算](observations/run-01/results.json)→[原典](SOURCES.md)→[範囲](COVERAGE.md)を辿る。入口は[学習画面](index.html)。11条件の実計算・独立照合に加え、保存結果を読むGUIと代表3画像を確認済み。[状態](qa/reader-acceptance.json)を見て最終受入の状況を区別する。関連資料は同じページへの移動と本文を照合済み、リンク実クリックは未確認。

1. 「gzipのmtimeが違えばDiffIDも違う？」：normal-mtime0/1のheader・91byteのblob digestの不一致・2048byteの展開tarの一致を辿る。tar memberのmtimeを変えた実験とは分ける。
2. 「descriptorが一致すれば元のimage内容？」：changed-contentの自己整合descriptorと元DiffID不一致、期待値の信頼を分ける。署名や認証を実装したとは答えない。
3. 「小さい圧縮blobなら安全？ 連結gzipは不正？」：output-limitとconcatenated、cap+1診断、単一memberという独自subsetへ戻る。一般的なarchive安全性やgzip全仕様適合は主張しない。

この3例の資料利用を確認する限定Skillで、未知質問への一般Agent評価や安全認証ではありません。global install、元repo、共有計画を書き換えません。
