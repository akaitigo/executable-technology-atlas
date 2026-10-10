# Atlas：参照資料と読み分け

- [Apple 保存版 link(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/link.2.html)：同じ実体への別名追加、リンク数の増減、既存宛先の EEXIST を照合しました。本文は 1994 年の日付を持つ保存資料です。現行 Mac 全般の実装保証とはせず、今回の実測と分けて扱います。
- [Python 3.9 の os.link](https://docs.python.org/3.9/library/os.html#os.link)、[stat_result](https://docs.python.org/3.9/library/os.html#os.stat_result)：標準 API の呼出と、デバイス番号・inode・リンク数の意味を確認する入口です。閲覧時の文書は 3.9.25、実行した Python は 3.9.6 です。SDK の追加や更新は行っていません。
- [POSIX.1-2024 link](https://pubs.opengroup.org/onlinepubs/9799919799/functions/link.html)：今回の取得は HTTP 403 でした。未取得の本文を確認済みの根拠として使っていません。

読み取った元の計画と既存 OS 教材の場所・ハッシュは [sources.json](sources.json) に保存しました。元のファイルは変更していません。公式資料は 2026-10-06 に閲覧し、全文の複製は保存していません。

実装は [experiment.py](experiment.py)。新規作成、hardlink、読み書きによる内容コピー、同じ長さの直接書換え、片名の unlink を順に実行します。`os.replace`、`fsync`、clone、長寿命の開いた参照、ディスク設定の変更は使いません。データの内容は [expected.json](expected.json) で先に固定しました。
