# Atlas：hardlink と内容コピーの範囲

分野目標 14 の「名前と参照」「所有する一時ファイルの観測」を進める単元です。ストレージ分野全体の完了ではありません。

| 問い | 今回の根拠 | 残る範囲 |
|---|---|---|
| 同じ内容なら同じ実体か | 3 つの名前の全 6 バイト、同一実行の `(st_dev, st_ino)` | 別実行での番号比較はしない |
| hardlink は更新を共有するか | alias 経由の BRAVO 書込みが original にも見える | replace や並行更新は未実験 |
| copy はどう違うか | 新規ファイルへ内容コピー後、COPY! 書込みは A へ伝わらない | 物理ブロック、属性全体、clone/reflink は未測定 |
| 宛先が既にあるとき | EEXIST と前後の完全一致 | EXDEV、権限拒否、ディスク故障は未実験 |
| 元の名前を消すとき | original は ENOENT、alias は BRAVO、nlink が 2→1 | 開いた参照を保持する旧 OS 教材は新作扱いしない |
| 後片付けと失敗 | 準備失敗 1、実験 1、全一時ファイルの削除 | 性能、耐久性、OS 全般の保証ではない |

元計画は storage の `learning/subjects/storage-filesystem-engineering/COVERAGE.md` の次 1、分野目標は `atlas-97-field-goals-ja.md` の目標 14です。目標文書に残る疎ファイルの次手順は、今回の明示された hardlink の割当とは区別しています。参照時のハッシュは [sources.json](sources.json) に保存しました。

既存 OS の `learning/continuations/operating-system-kernel-engineering/unlink-replace-open-descriptor/README.md` は unlink 後の開いた参照、replace、同内容で別の実体を扱います。今回の増分は **同時に存在する original・hardlink・copy と、直接書換えの伝わり方**です。有限の索引調査で見つからない項目を「存在しない」とはしていません。既存実行環境担当の現在の活動は未確認であり、この独立パスだけを同じ作者が編集しました。

6 時点・148 項目の保存結果照合を実施しました。画面は 19 項目・74 回の実ポインター操作を確認し、1280px と 390px の実画像 7 枚を目視しました。別担当による受入と Atlas への統合はまだ実施していません。撮影後の末尾 1 行の状態案内だけは未再撮影で、差分と撮影版を保持しています。既存教材と Atlas 全体の受入数は変更していません。
