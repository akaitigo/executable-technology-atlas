# Atlas：規則と原典の対応

読取日：2026-10-07 UTC。Web本文は取得時点の著者・大学公式資料で、固定commitの証明とは扱いません。本文を大量複製せず、今回の契約へ対応する小範囲を読みました。

| 原典 | 読んだ箇所 | 今回の対応と差 |
|---|---|---|
| [Poole & Mackworth, Artificial Intelligence 3e §4.2](https://artint.info/3e/html/ArtInt3e.Ch4.S2.html) | 全割当、部分割当の違反、DFS | 全16割当との全解集合照合。今回のcounterは独自に定義 |
| [同 §4.3](https://artint.info/3e/html/ArtInt3e.Ch4.S3.html) | domain、arc consistency、非空でも解なし | 非空を解ありとしない。今回FCをACとして説明しない |
| [同 §4.4](https://artint.info/3e/html/ArtInt3e.Ch4.S4.html) | 場合分けと解集合の和、枝ごとのdomain | 枝に局所的な削減を戻す。書籍のGAC実装の再現ではない |
| [UC Berkeley CS188 §2.3 Filtering](https://inst.eecs.berkeley.edu/~cs188/textbook/csp/filtering.html) | Forward Checking と Arc Consistency | 新割当に隣接する未割当domainだけを削減。削除からqueue伝播しない |

今回の実装は固定の二項不等号に限定した独自の小さな模型です。[疑似コード](PSEUDOCODE.md)の候補snapshot、失敗時の打切り、trail逆順復元が具体的仕様です。

取得失敗：AIMA Python公式repositoryのraw master/csp.pyは1回404で本文未取得。連続再試行はせず、上記の著者・大学本文へ戻りました。未取得本文の内容やhashを根拠にはしません。GUIで外部原典をクリックする検査では外部通信を遮断し、ローカルnoticeへの遷移だけを確認しました。本文読了とは別です。具体的範囲は[GUI記録](GUI_VERIFICATION.md)へ。
