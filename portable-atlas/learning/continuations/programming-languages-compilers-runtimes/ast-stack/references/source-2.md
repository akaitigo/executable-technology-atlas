# 言語・compiler・runtimeを、文字から実行まで辿る

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存実装・原票・QA・source束縛は変更していません。有限教材の補足であり、分野全体の学習完了を示すものではありません。次の実験案はすべて未実装・未実行です。

## 1. 前提と主要概念

文字列、整数の四則、括弧、treeの親子、関数・再帰を確認します。まず `2 + 3 * 4` を `2 + (3 * 4)` と `(2 + 3) * 4` の2つの木へ分けてください。同じ文字からどの構造を作るかが、計算の意味を変えます。実装を読む場合はPythonのlist・関数・例外が前提です。

文字と位置 → lexerのtoken → grammarとparser → AST → 名前・型の検査 → IR/code生成 → runtime、の順に学びます。今回実装するのは整数式のlexer/parser/tree evaluatorです。tokenは文字の分類、ASTはまとまり、評価は木から値を得る処理です。名前解決・型検査・optimizer・GCまで同じ工程とは扱いません。

## 2. 既存の正常・意図異常・拒否を読む

[画面](index.html) → [README](README.md) → [language.py](language.py) → [生tokens/AST/trace](evidence/stdout.json) → [実行identity](evidence/run.json) → [COVERAGE](COVERAGE.md)と辿ります。起動・再現方法はREADMEにあり、この追補では実行していません。

宣言grammarの `2 + 3 * 4` は14、naive grammarは20です。naiveは+と*を同順位・左結合にする意図的な別grammarで、文法一般として無効という意味ではありません。`(2 + 3) * 4` は両者20となるため、1つの一致例では差を見逃します。

`2 + * 3` はoffset4でparser拒否、`2 + x` はoffset4でlexer拒否。値0とerrorによる値なしを区別します。offsetは0始まりのUnicode code point、line/columnは1始まりです。画面は保存10caseのtrace再生で、任意式を実評価する入口ではありません。

## 3. 実務判断と限界

lexer/parser/評価のどの層で失敗したか、優先順位・結合性がASTへ反映されるか、拒否入力を評価へ渡していないかをreviewできます。error位置は検出点であり、最適な修正箇所とは限りません。括弧あり/なし、0、境界、拒否を組み合わせます。

非負ASCII整数6桁、入力256 code point、括弧depth16までです。Group nodeは可視化用に残します。Python整数なのでmachine overflowは扱わず、変数・関数・静的型・bytecode・実言語互換性も未実装です。eval/execを使わないことだけでは汎用sandboxの安全性を示せません。任意入力や実compiler全体の正当性は証明していません。

## 4. 一次資料へ戻る

既存の [sources.json](sources.json) はNorvell原著のRecursive-descent recognition／The classic solutionと、Nystrom原著ScanningのLexemes and Tokens／Error handlingへ対応します。ここから次の著者教材へ進みます。

| 著者locator | 読む概念 |
|---|---|
| [Parsing Expressions](https://github.com/munificent/craftinginterpreters/blob/master/book/parsing-expressions.md)、Ambiguity and the Parsing Game／Recursive Descent Parsing | precedence、associativity、unary |
| [Resolving and Binding](https://github.com/munificent/craftinginterpreters/blob/master/book/resolving-and-binding.md)、Static Scope／Resolving Variable Bindings | declaration位置と名前解決 |
| [Chunks of Bytecode](https://github.com/munificent/craftinginterpreters/blob/master/book/chunks-of-bytecode.md)、Bytecode?／Chunks of Instructions | 命令・constant・位置情報の表現 |
| [Garbage Collection](https://github.com/munificent/craftinginterpreters/blob/master/book/garbage-collection.md)、Mark-Sweep Garbage Collection／Marking the Roots／Sweeping Unused Objects | 到達可能性、root、回収 |

著者の実装をそのまま今回の独自grammarと同一視しません。リンクは更新され得るmaster本文で、固定版の仕様証明ではありません。

## 5. 未教材の具体概念と問い

| 概念 | 学びたい問い | 接続 |
|---|---|---|
| unary・associativity・diagnostics | -と括弧、同順位の連鎖をどう解釈する？ | 次案1。複数error recoveryは別教材 |
| binding・scope・types・functions | 同名変数はどの宣言へ戻る？ 実行前に何を拒否できる？ | 次案2は名前のみ。型推論/型健全性は未教材 |
| IR/SSA・bytecode・native生成・optimizer | 木を命令へ写して同じ値になる？ 変換で副作用順を変えない？ | 次案3は純粋整数式のみ |
| GC・allocator・lifetime・closure | rootから辿れないobjectだけを回収できる？ | 次案4は合成heapのみ |
| JIT/AOT・ABI/FFI・linking | 実行方式や境界の呼出し規約で何が変わる？ | 専用原典・実験は未選定 |
| concurrency・memory model・security | 単threadの意味を並行実行へ移せる？ resource上限は安全性保証？ | 今回のtraceからは判断できない |
| incremental compilation・debugger・性能 | 編集前後の位置情報やcacheは何に束縛する？ | 専用実験未整備 |

## 6. 次の4実験（未実装・未実行）

1. **unaryと結合性**：独自grammarへ単項−と二項減算を追加し、`-2*3`、`10-3-2`、`-(2+3)*4`を同じtoken列から評価する。正常のleft associationと意図的right associationでAST/valueを比較し、拒否位置も別oracleへ照合する。原典はParsing Expressionsのprecedence/associativityとunary規則。既存grammarに減算があるとは扱わない。
2. **静的な名前解決**：有限なblock/let/variable ASTで、同名の外側・内側宣言と、未宣言名を用意する。resolverが決めた宣言IDと、独立environment探索の値を比較し、shadowとscope外参照を記録する。原典はResolving and BindingのStatic Scope／Resolving Variable Bindings。関数、mutable closure、型検査は次の別段階です。
3. **ASTからstack命令へ**：同じ整数式をconstant/load/add/multiply相当の小bytecodeへ変換し、tree evaluatorと独立stack VMの結果を比較する。命令位置、stack高、constant indexを保存し、underflowと不正indexを拒否する。原典はChunks of Bytecodeの命令列/constant表現。VMの実行規則とcompiler correctnessは次実装時に追加原典を選ぶ課題です。
4. **合成heapのmark/sweep**：固定object IDと参照辺のgraphを作り、rootありcycle、rootなしcycle、root移動前後を比較する。rootからの到達集合を独立graph oracleで求め、mark集合・回収集合・残った参照先を照合する。root探索を故意に1つ省く異常も残す。原典はGarbage CollectionのMarking the Roots／Sweeping Unused Objects。実アドレス、allocator、停止時間、moving/generational GCは未検証です。

4本でも言語・compiler・runtime全体は網羅しません。新実装・oracle・観測が必要です。

## 7. 資料取得と検証の状態

2026-10-05にread-only webで上記4章の著者GitHub本文を取得し、章内の概念を確認しました。著者サイトの同名4章（`https://craftinginterpreters.com/` に各章名と `.html` を続けるURL）はweb toolで取得不能でした。著者Repositoryを代替参照にし、取得不能を本文不存在とは断定していません。第三者本文・図・コードは転載していません。

確認したのは文書と静的リンクです。実験、runtime、実UI再QA、repository全体の完成判定は追加していません。既存証拠のhashやsource束縛は再封印していません。
