# Atlas：小ステップと観測ログを区別する契約

## 目標と前提

正式な分野目標は07「プログラミング言語基礎」、目標文書115–124行。元README「次の4実験」の2とCOVERAGEのsmall-step未対応へ進む。構文木、再帰、辞書、束縛、関数、値渡しを前提とする。既存の環境評価・捕獲回避置換・AST→stack命令を再制作せず、項から項への規則1歩と実装観測eventを区別する。

専有先は `independent-learning/language-small-step-boundary/`。作成直前に未存在を確認した。元repo・旧教材・台帳はread-only、元owner現状は不明、統合しない。作者加算0。これは実装前の有限契約で、測定成功の記録ではない。

## 言語と規則

JSON ASTの `Int/Var/Fn/Call/Add` だけを使い、入力は自由変数がない閉項へ限定する。値はIntとFn。関数本体は呼出し前に還元しない。nameとliteralの形は旧評価器の有限範囲に合わせ、boolを整数にしない。今回の5入力は64node/depth16以内、literalは-1000..1000。Let、可変store、型注釈、例外、I/O、text parserは追加しない。

一歩は最外項全体のbefore→after。下位項を一度還元して戻す規則も1歩である。

| 規則 | 条件と一歩 |
|---|---|
| AddInts | 両側がIntなら、その和のIntへ |
| AddLeft | 左が一歩進めるなら左だけを書換え |
| AddRight | 左が値で右が一歩進めるなら右だけを書換え |
| CallFn | 関数位置が一歩進めるなら関数位置だけを書換え |
| CallArg | 関数位置がFnで引数が一歩進めるなら引数だけを書換え |
| Beta | 関数位置がFn、引数が閉じた値なら自由なparameter出現を置換 |

同名binderでは置換を止める。closed値だけを代入するため一般open項のalpha renameはこの増分に含めない。Intを関数位置に持つCallは引数を還元せず止まる。これは元Atlasのnot-callable順序へ合わせた独自規則で、Software FoundationsのST_App2（任意valueを左に許す）と同一ではない。Addの整数検査は両側を値にした後とする。

## 5つの固定対照と手期待

[入力](inputs/cases.json)と[全AST手列](expected.json)をproducerより先に固定する。

| 条件 | 予算 | 規則の歩数 | 分類・結果 |
|---|---:|---:|---|
| Int 0 | 0 | 0 | value、整数0 |
| (1+2)+(3+4) | 3 | 3 | 3+(3+4)→3+7→10、value |
| 同じ算術項 | 2 | 2 | 3+7でbudget_exhausted、次のAddIntsは適用しない |
| (fn x → x+1)(2+3) | 3 | 3 | (fn x → x+1)(5)→5+1→6、value |
| 0(1+2) | 4 | 0 | stuck、引数1+2は未還元 |

各時点の分類は、まず値ならvalue、非値かつ規則なしならstuck、規則ありかつ残予算0ならbudget_exhausted、そうでなければ1歩適用。予算がちょうど尽きた完成値を予算切れにしない。規則の有無を調べたprobeは適用歩数へ数えず、次規則を表示するときは未実行と明記する。

固定した旧評価器を別経路で同じASTへ適用し、正常0/10/10/6、最後not-callableを比較する。旧評価器の64 node-enter予算やframe/enter/return等のevent数は規則の遷移数ではない。2歩で停止した小ステップと旧評価器の10が異なっても、意味不一致とはしない。この有限停止は発散の証明ではない。

## 原典・実装の対応

Software Foundations公式のSmallstep「A Toy Language」「Values」「Strong Progress and Normal Forms」、Stlc「Substitution」「Operational Semantics」を本文読取する。原典は自然数や型付きBoolを扱い、今回の整数・型なし部分言語・CallArg条件・資源予算はAtlasの明示仕様。Rocq証明、progress/preservation、全入力の等価性を獲得したとはしない。[原典と前提](SOURCES.md)へ位置と版・hashを結ぶ。

## 保存と受入

一歩ごとのbefore/after AST、規則列、redexの場所、適用歩数、終端分類、未実行の次規則、旧評価器の結果と完全観測ログを保存する。入力拒否・言語上のstuck・観測予算切れ・実process失敗を分ける。別担当の実装前手表と照合し、少なくとも右先行/2歩の潰し込み/分類の混同/途中項改変を保存値で拒否する。producerはexpectedを読まない。

実行はまだ未許可。予定はPython stdlibの単独子1batch、nice実値10以上、CPU soft2/hard3秒・wall3秒、有限TERM/KILL/wait、retry0。実装前レビュー、今回のroot枠、fresh資源・完全ps、今回限りのroot所有/既存idle資源判断が必要。旧decisionを自動継承せず、unknownは停止。具体guard/環境/hashは実行前に別途固定する。

画面は保存結果だけを読み、予想→1歩の再生→big-step観測との比較→原典/コード→答え→限界の順。rootの既存pageを再利用する確認コードを後で用意し、作者browser/server起動0。実DOM/画像/限定Skillの確認なしに局所受入trueへしない。

Skillでは「0は値か」「予算2の残項は何か」「なぜbig-stepの10と矛盾しないか」「どこを1歩で変えたか」「整数callで引数を評価したか」「型安全性や発散を証明したか」を資料へ戻して案内する。一般Agent評価や分野全体の完成とは区別する。
