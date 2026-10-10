# 有限教材のCoverage

今回実行した経路は独自bounded grammarのlexing→parsing→tree評価です。実言語compilerではありません。

- 正常：非負整数、ASCII whitespace、`+`、`*`、括弧、同順位left association、priority。
- 境界：0、leading zeros、6桁整数、256 code point、depth16。Python整数を使い、machine overflowは扱いません。
- 意図的異常：priorityをなくしたnaive grammarとnormal AST/valueの比較。
- 失敗：不正文字、operand欠落、括弧欠落、隣接整数、multiline定位。AST/valueなし・評価停止。
- 原票：全tokens、half-open source span、AST node ID、parse consume/build、postorder評価、error、runtime/source/artifact hash。
- oracle：固定hand/tree、別lexer/stack algorithm、100 generated balanced expressions、invalid15・mutated Evidence5、通常CLI read-only。

Group nodeを可視化用に残しています。一般的なASTは括弧を省略する場合があります。errorの位置は検出点であって最適修正候補ではありません。単一errorで停止し、自動修正／複数error recoveryは未実装です。

## Programming languages / compilers / runtimes全分野の未教材

負数・unary・float・除算・変数・binding・関数・制御構造、types/type inference、scope/name resolution、IR/SSA、bytecode/native code generation、compiler optimizer、JIT/AOT、GC/allocators、concurrency/memory model、ABI/FFI/linking、incremental compilation、debugger/profiler、実言語のdiagnostics/compatibility、sandbox/security、性能・resource attacks、formal semanticsとcompiler correctnessは未教材・未実行です。

有限例の一致から全input、任意grammar、実言語compiler/runtimeの正当性を主張しません。parserが任意コード実行を使わないことは、汎用sandbox安全性の証明ではありません。分野全体の知識網羅や学習者理解度も未評価です。
