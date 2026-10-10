# Atlas：原典と今回の規則

2026-10-07 UTCに著者・大学の本文を読みました。Webページは読取時点の内容で、固定commitや取得本文の保存SHAとは扱いません。以下は原文の転載ではなく、今回の仕様との対応です。

| 原典・読んだ箇所 | 今回の対応 | 今回固有の限定 |
|---|---|---|
| [UC Berkeley CS188 §2.3 Filtering](https://inst.eecs.berkeley.edu/~cs188/textbook/csp/filtering.html)：Forward Checking、arc queue、tail値のsupport、候補削減後の追加、空domainで停止 | FCは固定割当の隣を一巡。AC-3は二方向のarcから始め、候補の変化を伝える | 4変数2色・不等号・FIFO・辞書順・重複queueを避ける仕様を固定 |
| [Poole & Mackworth, Artificial Intelligence 3e §4.3](https://artint.info/3e/html/ArtInt3e.Ch4.S3.html)：arc consistencyの定義、図4.4の再追加、例4.18、非空と解の有無・例4.20 | 各候補に局所supportがあっても全体の解は保証しない。削減の影響を他の制約へ伝える | 書籍は変数→制約のGAC。本教材は1辺1個の二項不等号で、tail→headに表す |

Berkeley本文の再追加説明は逆arcを含む形です。本教材ではPoole/Mackworth図4.4の「同じ制約を除いた再追加」を二項・1辺1制約へ限定し、直前のheadを除くneighborからtailへ戻す仕様です。FIFO、最初のsupportで比較を止めること、計数は[疑似コード](PSEUDOCODE.md)を正とします。

書籍のGACは空候補の影響も伝播し続けます。本教材は最初の空domainで止めるため、空停止時の他変数や残queueまで書籍と同じ最終状態になるとは主張しません。三角A=0では再追加BCを残して止まり、そのBCを再popする分岐は今回の4条件では未確認です。

原典の例をそのまま実行したものではありません。[入力](inputs/cases.json)、[実装前手表](HAND_TRACE.md)、[模型](arc_consistency.py)の対応を読みます。全解集合は先に固定した全16割当による手期待で、AC-3が全解を出した結果ではありません。

GUIではBerkeley公式URLへの実pointer操作を、外部通信を転送しないローカルnoticeへ置き換えて確認しました。公式本文をGUIで取得・表示した記録ではありません。その導線確認と、ここに記録した原典本文の事前読取は別です。[GUI確認範囲](GUI_VERIFICATION.md)と[status](status.json)へ。
