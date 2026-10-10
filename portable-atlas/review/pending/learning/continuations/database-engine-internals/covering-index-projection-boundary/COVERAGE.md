# 検証範囲

| 問い | 有限観測 | 未検証 |
|---|---|---|
| 投影とcovering | 同bucketの2列/3列、raw4列EQP | 全SQLite版の同一plan |
| 結果の意味 | NULL/empty/重複/asc-desc、全行独立filter | 任意SQL/type/collation |
| index構造 | schema、table_info、index_list/index_xinfo | 物理B-tree/page訪問 |
| provenance | SQLite版/source_id/compileoptions、fresh再照合 | 別環境での同一性能 |
| cleanup | :memory: connection close後ProgrammingError | disk/WAL/crash durability |
| 未教材 | stats/join/partial index/write cost/全engine | 別実験が必要 |

plan未成立と結果不正を区別。速度/倍率/visit数、backend README N4、Subject/Atlas全体完了を主張しない。
