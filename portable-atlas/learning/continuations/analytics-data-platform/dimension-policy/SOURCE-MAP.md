# Atlas：未知キーの方針を支える資料

目標69（分析データ基盤）の次の一歩に対応する。元教材のLEFT/INNER JOINによる欠落、NULL集計、注文粒度は前提として再利用し、新しい証明として数えない。履歴時点のJOINを扱うas-of教材とも別の問い。



2026-10-06に公式本文を正規web経路で読んだ。本文bytesは保存しておらず、本文hashは主張しない。

| 原典 | 読んだ箇所 | この教材で使う範囲 |
|---|---|---|
| [SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html) | §1のNULL child key、§2の接続別有効化とトランザクション中変更不可、§4.2の即時制約 | 非NULLの不存在とNULLを分ける。OFF/ONを明示して読み戻す。失敗した単文と全バッチ拒否を同一視しない |
| [SQLite aggregate functions](https://www.sqlite.org/lang_aggfunc.html) | count、sum | COUNT(*)とCOUNT(amount)の差、既知値がなければSUMはNULL |

3方針の採用、NULLキー許可、対象の明細存在条件、欠損割合の分母は教材の明示した規約で、SQLiteや一般業務が一つの方針を推奨するという意味ではない。元担当の現在状態は未確認で、共有元は変更・統合しない。
