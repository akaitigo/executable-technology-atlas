# Atlas：規則と参照実装の対応

[参照位置・hash](sources.json)へ、実際に読んだ既存ファイルと公式ページの範囲を記録した。外部場所は出所の案内であり、教材単体HTTPから到達確認したリンクとは扱わない。

| 原典・実装 | 今回へ結ぶこと | 境界 |
|---|---|---|
| [Software Foundations Smallstep](https://softwarefoundations.cis.upenn.edu/plf-current/Smallstep.html)：A Toy Language / Values / Strong Progress and Normal Forms | 一歩の項変化、計算する場所の規則、値と規則適用不可の区別 | 原典の自然数の例に対しAtlasは整数・関数を組み合わせる。原典の証明を実施済みにしない |
| [Software Foundations Stlc](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html)：Substitution / Operational Semantics | 閉じた値の代入、関数本体を適用まで還元しない値渡し | 原典ST_App2は任意valueを関数位置に許す。Atlas CallArgはFn限定で、整数callの引数を先に評価しない旧実装へ合わせる |
| [固定した旧評価器](inputs/prerequisite-interpreter.py)：Evaluator.evaluate / run | 同じASTの最終値とnot-callableを別経路で照合 | 元ファイルの完全bytesコピー。環境再帰評価のevent列を小ステップ列と呼ばない |
| 既受入capture-avoiding-substitution | 閉項の今回と、open項の捕獲回避の必要性を分ける | 置換算法の新しい完成件数にしない |
| 既受入compiler-ast-stack | 式の意味と命令の動作を比較する前提 | 命令のstack1遷移は、式の規則1遷移ではない |

公式本文は2026-10-06に読んだ。`plf-current`は可変ページであり固定commitの証明ではない。第三者本文・図・コード全体は保存せず、本文bytesのhashを取得したとは主張しない。Rocqの定理や型安全性、任意入力の終端性は今回実行しない。
