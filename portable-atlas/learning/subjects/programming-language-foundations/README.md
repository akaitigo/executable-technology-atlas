# Closure Paths: xはどこへ戻る？

独自の小さなAST/closure interpreterでlexical scopeと、activation parentをcallerへつなぐ意図異常を比較する有限教材です。Python stdlibのみ、`eval()`/`exec()`/host言語ASTは不使用。Scheme/Loxの互換実装や一般言語Runtimeではありません。

学習の道筋は **AST・name・parameter → environment/binding/shadow → closureの定義envとcall → 正常/異常trace → parentと自由変数を実務で判断 → 限界 → 一次資料**。初めてならInt/Var/Letのinitializer caseから、中心capture caseへ進めます。

## 問い・正常・意図異常

この記法は入力JSON ASTの説明表示で、text parserが受理する言語ではありません:

```text
let x = 10 in
  let f = fn(u) → x in
    let x = 20 in
      f(0)
```

正常は10。fのClosure c0は定義env e1を参照し、parameter frame e4→e1でxへ解決します。誤実装はe4→caller e3で20へ解決。同AST・初期env・引数でactivation parentだけを変えます。dynamic scopeという言語設計自体を一般に不正とは呼ばず、この教材の宣言lexical semanticsに対する欠陥です。

| case | 正常lexical | 意図異常caller-parent | 判断点 |
| --- | --- | --- | --- |
| capture | 10 | 20 | 自由変数の環境 |
| parameter_shadow | 7 | 7 | parameterは近い束縛。1成功例では欠陥を見逃す |
| argument_caller | 30 | 40 | 引数xはcallerで20、body自由変数xは正常10 |
| escaped_closure | 10 | 20 | 外へ返したclosureも定義envを参照 |
| let_initializer | 11 | 11 | 新xのinitializerは外側のxで評価 |
| caller_rescue | unbound-name | 20 | callerだけのxは正常を救わない |
| unbound | unbound-name | unbound-name | missingを0にしない |
| not_callable / addition_type | Runtime error | Runtime error | integer call / closure Add |
| literal_boundary | 0 | 0 | -1000+1000。正常0とerrorの結果なしは別 |
| invalid_literal / invalid_ast | AST拒否 | AST拒否 | literal1001 / parameter bool、評価開始前 |
| fuel_boundary | budget停止 | budget停止 | self-application、発散の形式証明ではない |

保存13caseの[run](evidence/run.json)に実行時刻・環境・input/source/raw/artifact digest、[stdout raw](evidence/stdout.json)に全frame/closure/enter/capture/call-parent/lookup/return/errorを残しています。env/closure IDはそのrun内の連番で、実機addressや永続IDではありません。

## 既存checkerを使う（read-only）

Repository rootから:

```bash
cd learning/subjects/programming-language-foundations
python3 -B check.py
python3 -B check.py --case capture
python3 -B check.py --case parameter_shadow
python3 -B check.py --ast-json '{"kind":"Let","name":"x","value":{"kind":"Int","value":10},"body":{"kind":"Var","name":"x"}}'
python3 -B verify.py
```

通常はstdoutだけ。custom/caseの正常経路がerror/拒否ならexit2。固定batchは期待されるerrorも教材観測として含みexit0です。optionなし`observe.py`もread-only。stdlib Python3.9以上、install/外部サービス/Docker不要。

**原票更新を明示的に行うときだけ**:

```bash
python3 -B observe.py --write-evidence
python3 -B verify.py
```

checker subprocessを再実行し時刻/環境/raw/source hashとSVG、`data.js`を更新。検査に合わせた自動書換えではありません。各fileのtemp→replaceであり、世代全体の原子的swapを保証しません。

## UI操作とQA

```bash
python3 -B -m http.server 0 --bind 127.0.0.1
```

表示されたportの`http://127.0.0.1:PORT/`を開き、title `Closure Paths — xは、どこへ戻る？`、mainの`data-field-id=programming-language-foundations`を確認します。port0は専用空きport割当。終了は自分のterminalのCtrl-Cで、他担当listenerは停止しません。index.html直接表示でも保存data.jsを読みます。

予想→Capture→Call parent→束縛Lookup→最後、全eventからstepへjump、AST node、原票/実装/原典、答えとroadmapへ。現在までに生成されたframeと探索chainを表示します。8frame超のdiagramは先頭8だけ、table/rawは全体。両経路はevent番号で再生し、短い経路は終端に留まります。同期意味論のlockstep証拠ではありません。

UIは保存13caseのreplayで、任意input評価はCLI。実UIの操作/capture保存可否は[visual QA](evidence/visual-qa.json)、[SVG](evidence/environment-chain.svg)は実lookupの**再描画**で実captureではありません。

## 独立検査・一次資料

- [interpreter.py](interpreter.py)：親linkを持つEnvironment object、Closureが定義envを参照する実装。既存frameは変更せず、新frameを追加。
- [verify.py](verify.py)：別のtuple-of-binding-groups oracle（production Environment/lookup/evaluateを再利用しない）と手計算e4→e1/e3。value、parameter parent、capture、probe、return列、errorを照合。seeded200 AST、depth16/node64/literal境界、13 malformed AST、束縛/digest改変7件、3 subprocessのmodule byte不変を検査。全ASTや形式的type safety証明ではありません。
- [R7RS公式報告](https://standards.scheme.org/official/r7rs.pdf)：§3.1（printed p9）、§4.1.4（p13）、§4.2.2。lexical regionとprocedure environment。今回の単parameter、immutable binding、左から評価順、budgetは独自仕様で、Scheme全体の仕様と同一にしません。
- [Nystromの原著Repository / Resolving and Binding](https://github.com/munificent/craftinginterpreters/blob/master/book/resolving-and-binding.md)：Static Scope / Scopes and Mutable Environments / Resolving Variable Bindings。book website fetch失敗のため著者Repositoryを使用。本文・図・コードを保存せず[sources.json](sources.json)へlocatorのみ。

## 今回から判断できること／限界

自由変数の宣言位置、parameter shadow、callerでの引数評価を分けて調べ、interpreter reviewでcapture/activation parentとlookup chainを検査できます。「関数の呼出し場所で常にnameを探す」「1caseの出力が合えばscopeは正しい」は今回の反例で拒否できます。

lexical/static scopeとstatic typingは別概念。実装したnot-callable/addition-typeはRuntime guardで、静的type checkerはありません。closureは環境を参照し、このmodelではbindingを変更しないだけです。mutable変数の値snapshot、Scheme location/storage、実Runtime lifetime/GCの一般的な性質まで証明していません。

[COVERAGE.md](COVERAGE.md)はSubject全体の未教材。有限1unitをSubject/Portal完成や学習者理解度へ昇格しません。[module内Skill routing](evidence/skill-routing-check.json)はmain-agentの通常/未対応確認で独立Forward Evalとは別。global Skill installなし。この教材は旧repo/Core/Graphへ依存せず、module内だけで実行できます。commit/push/公開なし。旧Goalは未達pausedのまま、新Goalなし。

## 次の4実験（未実施）

| 未教材概念 → 問い | 次の有限実験 | 一次資料locator |
| --- | --- | --- |
| free/bound name、alpha equivalence、substitution → 単純置換が別の変数を捕獲しない？ | 1. alpha rename＋capture-avoiding substitutionを小ASTで実装し、環境oracleと結果を比較。今回は新実装なし。 | [R7RS §7.2](https://standards.scheme.org/official/r7rs.pdf#page=65)、[Software Foundations / Stlc: Substitution](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html) |
| operational semantics、stuck、termination → traceと規則導出は同じ？ | 2. 別のsmall-step evaluatorでvalue/stuck/budgetを分け、有限step列とbig-step値を比較。instrumented traceだけで証明しない。 | [Software Foundations / Small-step](https://softwarefoundations.cis.upenn.edu/plf-current/Smallstep.html) |
| type system、type safety → 何を実行前に拒否できる？ | 3. Int/arrowのcheckerを追加し、integer callやclosure Addを拒否。progress/preservationは別の証明課題へ。 | [Software Foundations / Stlc: Typing](https://softwarefoundations.cis.upenn.edu/plf-current/Stlc.html) |
| bindingとstore、effects → capture後の代入はどこを変える？ | 4. name→location→valueを別modelで導入し、assignment前後のclosureを比べる。immutable frameの今回の結論を流用しない。 | [R7RS §3.4 / §4.1.6](https://standards.scheme.org/official/r7rs.pdf#page=14) |

さらにrecursive definition、polymorphism/parametricity/subtyping、equivalence/denotational/full-abstraction、exceptions/continuations/effect handlers、module/ownership/GC、concurrency/memory model/securityの各問いが残ります。上記4実験でも全範囲は閉じません。定義済みRuntimeや形式証明・一次資料Evidenceは未整備で、[Coverage](COVERAGE.md)を参照してください。
