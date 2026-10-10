# Atlas：ASTからstack命令へ写す

この契約・入力・手書き期待値を新しいproducerの実装前に固定します。専有先はこのディレクトリだけ。元分野ownerの現況は未確認で、元repository、旧教材、共有台帳は読取り専用です。

## Atlas の到達点・前提・増分

[目標12](../../../../2026-10-06/task-8/atlas-97-field-goals-ja.md)の「整数式をスタック命令へ変換し、木の評価結果とVMの値・スタック境界を照合する」に対応。元の `learning/subjects/programming-languages-compilers-runtimes/LEARNING_PATH.md:54` が今回の局所計画です。

前提は文字列、AST（構文のまとまりを表す木）、再帰、型と例外。元 `language.py` のtokenize/Parser/evaluateを [完全一致コピー](inputs/prerequisite-language.py)として再利用し、解析器を作り直しません。コピーの出所とhashは [記録](records/input-provenance.json)へ。名前解決・GC・Tiny8は既存範囲であり、新しい成果として数えません。

新しい範囲は、AST→定数表/命令列/対応表、および独立したstack VMです。元の木評価器は命令列を使わず評価し、VMはASTを読まず命令列だけを実行します。両者の値に加え、手で固定した命令順とstack前後を照合します。加算・乗算は可換なので値の一致だけでは左右逆転を検出できません。

## Atlas の有限な言語と命令規則

元grammarの非負ASCII整数（6桁以内）、加算、乗算、括弧を使用。入力256 code point/括弧深さ16の前提を変えません。今回実行する入力は固定5式だけです。Python整数を使用し、機械整数overflowや実言語互換は扱いません。

- `CONST i`：定数表index iの値をstackの右端へ積む。iは値そのものではない。
- `ADD` / `MUL`：2要素必要。右端からright、次にleftを取り、left+right / left*rightを積む。命令に定数index operandは付かない。
- 終端：stackが厳密に1要素なら値を返す。0や2以上なら拒否し、値なし。

命令はJSONの配列で表す独自の構造化命令で、バイト列や実CPU命令ではありません。pcは0始まりの**命令番号**、byte offsetではありません。定数表はASTを左→右に辿って最初に出た値の順で登録し、同じ整数値は同じindexを再利用します。この重複除去は今回の選択で、著者の実装一般の保証ではありません。

IntegerはCONSTを1つ出す。二項nodeは左subtree→右subtree→自身の演算命令の後順に出す。Groupはchildの命令範囲へ対応し、独自の命令は出しません。全nodeのid/spanと命令範囲[start,end)、各命令の出所nodeを保存します。最適化や順序変更はしません。

## Atlas の実装前期待

|正常入力|定数表|命令|値・最大stack高|
|---|---|---|---|
|`2 + 3 * 4`|[2,3,4]|CONST0 CONST1 CONST2 MUL ADD|14・3|
|`(2 + 3) * 4`|[2,3,4]|CONST0 CONST1 ADD CONST2 MUL|20・2|
|`2 * 3 + 4 * 5`|[2,3,4,5]|CONST0 CONST1 MUL CONST2 CONST3 MUL ADD|26・3|
|`0`|[0]|CONST0|0・1（値なしとは別）|
|`2 + 2 * 2`|[2]|CONST0 CONST0 CONST0 MUL ADD|6・3|

固定7拒否：上限外index、負index、ADDの0operand、MULの1operand、空の終端、2要素の終端、未知opcode。indexは `0 <= i < len(constants)` を先に検査し、Pythonの負indexを流用しません。二項演算はpopより前に要素数を確認します。拒否した命令の前後stackは同一で、後続へ進みません。期待された拒否とproducerの実行失敗は別分類です。具体的pc/stack/診断は `expected.json` で固定します。

命令列は最大64、定数数64、stack高64、AST node数64/深さ32に限定。今回の入力はこの範囲内です。独自VMの引数形や整数型も検査しますが、任意入力の安全なsandboxや全境界の網羅証明とは呼びません。

## Atlas の原典と独自部分

Robert Nystrom著者本文の [A Virtual Machine](https://raw.githubusercontent.com/munificent/craftinginterpreters/master/book/a-virtual-machine.md) の A Value Stack Manipulator / Stack tracing / Binary operators、[Chunks of Bytecode](https://raw.githubusercontent.com/munificent/craftinginterpreters/master/book/chunks-of-bytecode.md) の Constants を読みました。後順、stackでの一時値保持、定数index、right→leftのpopを参照します。サイト本体2ページは各1回400で終了し、著者repository本文へ戻りました。

masterは可変で、固定commit証明ではありません。原文全文や画像を教材へ複製せず、読取日・URL・節/行と短い自分の説明を保存します。著者のC/double/byte encodingと、今回のPython整数/JSON命令/明示拒否を区別します。

## Atlas の実行・保存・受入

既存Python標準ライブラリーのみ、producer子1件・worker0・再試行0。子開始前のlauncherで自身のnice10以上を設定/実値確認し、確認不能なら対象を開始しません。子wall time3秒、CPU time2秒、全手順10秒を目安とし、timeout時は自己所有groupだけTERM後0.5秒、必要ならKILL後1秒回収。stdout/stderr・部分結果・起動数・完全入力hash・環境と回収を保存します。SDK/install/service/OS設定変更なし。

fresh資源読取でload<6、idle25%以上、memory query空き20%以上/推定2GiB以上、既知重処理/他headlessなしを確認。psが空/一部不正/自身PIDなしならunknownとして停止し、正式read-only審査を使えます。低負荷の余裕値を確保保証とはしません。

保存結果と固定期待、木評価とVM、全命令前後stack・診断・node対応を別担当が確認。予想→命令とstackの操作/対照→原典/実装→答え→限界のreader/図/限定Skillを作ります。図は保存値を説明する模型です。

現在Chrome新規起動・openURL・前面化は禁止待機。実DOM/画像は0のまま、CLIと静的資料を閉じます。GUIなしで全単元 `accepted:true` にしません。元統合・正式分類・作者による教材数加算は0です。

残りは変数/関数/型検査、制御flow、SSA/optimizer、machine code、ABI、JIT/GC連携、非可換演算や副作用の順序、他言語・性能です。この小言語成功をcompiler全般の保証にはしません。
