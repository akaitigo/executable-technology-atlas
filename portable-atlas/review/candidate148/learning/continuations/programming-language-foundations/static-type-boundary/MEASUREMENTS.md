# Atlas：保存した初回の型判断と評価

[run.json](observations/attempt-20261007T000929746801Z/run.json) に5条件と完全stdoutを結び、[保存値検査](observations/attempt-20261007T000929746801Z/verification.json) で217照合と7種類の意味改変拒否を確認した。対象Pythonは1回、exit0、実nice10、CPU soft2/hard3秒、経過0.1168455秒。自動retry0、所有子reaped、所有process group不在。

| 条件 | 型判断 | 通常評価call | 別診断call / 結果 |
|---|---|---:|---|
| function-value | Int→Int | 1 | 1 / Fn value・0歩 |
| higher-order | Int | 1 | 1 / Int3・3歩 |
| integer-call | $.fnでnot-arrow | 0 | 1 / not-callable・stuck・0歩 |
| function-add | $.leftでint-required | 0 | 1 / addition-type・stuck・0歩 |
| latent-invalid-function | $.body.fnでnot-arrow | 0 | 1 / Fn value・0歩 |

5条件の型木は計21node。通常評価2回と診断5回は別の呼出しで、process起動数とは違う。診断比較のFn valueは本体が型付け可能だという証拠ではない。値3だけでなくΓ・規則・位置・未検査部分・注釈消去ASTを照合する。

通常sandboxのtop/ps読取不成立、初稿の未採用追加CPU条件によるholdも保存済み。後者の条件をroot方針に合わせて観測のみへ戻し、新しい今回decisionとfresh観測で実行した。旧snapshotのallowedを書き換えていない。補助一覧にある既存プロセスの用途まで判明したとはしない。

入力形式拒否、Arrow引数型不一致、shadow等の未実行枝はこの5入力の実測範囲外。7改変は保存JSONへの検査で、producerの異常実行ではない。現在のGUI/独立受入は [状態記録](status.json) を参照する。
