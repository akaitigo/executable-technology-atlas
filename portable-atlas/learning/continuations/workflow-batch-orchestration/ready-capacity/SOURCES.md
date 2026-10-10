# Atlas｜DAG・容量と原典の対応

2026-10-06、[Python 3.9 graphlib公式本文](https://docs.python.org/3.9/library/graphlib.html)を読みました。公開本文の版は3.9.25です。本文・例の転載はせず、次の狭い箇所を自分の実装へ対応させます。

- `TopologicalSorter.get_ready()`：前の仕事についてdoneが通知された後で、後続を取り出せること。
- `TopologicalSorter.done()`：呼出側が処理済みと通知すること。API自体が現実のworker終了を検証するわけではありません。
- 冒頭のparallel processing説明：取り出した仕事と完了通知を別段階にする読み順。
- `static_order()`：順序が得られることと、容量付き実行を観測したことを区別する前提。

既存教材・選定根拠はすべてread-onlyで確認しました。





一次資料はscheduler最適性や本教材の仮想時間短縮を保証する根拠にはしません。Airflowや実workerの操作・設定・互換性確認は行いません。
