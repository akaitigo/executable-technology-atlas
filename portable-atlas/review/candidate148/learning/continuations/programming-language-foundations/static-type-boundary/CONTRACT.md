# Atlas：静的な型判断と実行時の値を分ける契約

目標07「プログラミング言語基礎」の、名前・型・効果を分ける実務判断へ進む。元README:83/93は実行時guardと静的型検査を分け、Int/arrow checkerを次の実験3としている。171受入済みの束縛・置換・小ステップ・AST命令変換を前提とし、再制作・再加算しない。

専有先 language-static-type-boundary/ は作成直前に未存在を確認した。旧repo/教材/目標/台帳はread-only、共有owner不明のまま統合しない。これは実装前の契約であり、実測成功の記録ではない。

## 問い・前提

関数をまだ呼んでいなくても、その本体の型矛盾を実行前に見つけられるか。実行時にFnという値になったことと、その式に型を付けられたことは同じか。AST、再帰、辞書、束縛、閉項、値とstuckを前提とする。

## 言語と型規則

項はInt/Var/Fn/Call/Addだけ。Fnにparam_typeを明示し、型はIntまたはArrow(T1,T2)。閉項に限り、Let/store/例外/外部I/O/text parserは追加しない。入力は64 node/depth16/literal±1000、型の深さは4以内、boolを整数として認めない。予算は0..16、固定5条件では8を用いる。

Γは名前→型の辞書で、実行時の名前→値の環境とは別である。T_IntはInt、T_VarはΓ参照、T_FnはΓへparameter型を加えて本体を検査しArrow(parameter,body)を合成する。T_Callは関数側を先に検査しArrowでなければ引数を検査せず拒否、Arrowなら引数型がdomainと構造一致したときだけcodomainを返す。T_Addは左から検査し各側がIntであるときだけInt、左が不適合なら右へ進まない。子の拒否はAST位置を保って親へ伝える。shadow時は内側の型を使い外側Γを破壊しない。

型導出を実行traceと呼ばない。規則木にはAST位置、Γ、規則、合成型または拒否理由、調べたpremiseと未検査位置を保存する。明示注釈から型を合成するが、注釈なしの引数型推論・単一化・多相型推論は扱わない。

## 5条件と実装前の手期待

[固定AST](inputs/cases.json)と[全型規則木・比較AST列](expected.json)をproducerより先に保存する。

| 条件 | 静的判断 | 注釈消去した診断比較 |
|---|---|---|
| fn x:Int => x+1 | Int→Int | Fn value、0歩 |
| (fn f:(Int→Int) => f(2))(fn x:Int => x+1) | Int | Beta→Beta→AddInts、値3、3歩 |
| 0(1+2) | $.fnのIntをArrowとして使えず拒否、arg未検査 | stuck/not-callable、0歩、arg未還元 |
| (fn x:Int => x)+1 | $.leftのArrowをIntとして使えず拒否、right未検査 | stuck/addition-type、0歩 |
| fn x:Int => x(1) | $.body.fnがIntなので本体で拒否 | 未呼出Fn value、0歩 |

通常経路は静的受理した2条件だけ固定評価器を呼び、拒否3条件の評価呼出数は0。診断比較は、静的拒否の理由を学ぶための別の操作であり、全5条件の注釈を消して同評価器を各1回呼ぶ。通常2回・診断5回を別countとして保存し、通常経路が型検査を迂回したとはしない。対象processは1回のまま、7 evaluator呼出しとprocess数を混ぜない。

注釈消去はFnのparam_typeだけを除き、他のkind/名前/値/左右/子の位置を保持する。既受入small-step.pyの完全一致コピーを比較に使い、旧source/旧実行ログは変更しない。この比較投影の一般的な意味保存を証明したとはしない。

## 原典と有限受入

Software Foundations公式StlcのValues、Contexts、T_Var/T_Abs/T_Appを本文読取した。原典の基底型Bool・条件式に対し、本教材はInt/Addを明示選択する。Python checkerはRocq証明の実行ではない。

独立担当がproducer未読で5条件のΓ/規則木/AST位置/型または拒否・消去AST列を先固定する。producerはexpectedを読まない。保存検査は型とΓ・拒否位置・評価0/別診断回数・全AST列・source/完全stdoutを照合し、対応する改変が意味ラベルでも拒否されることを確認する。入力形式拒否、型拒否、診断stuck、資源停止、実process失敗を分ける。

実行は独立preexec、今回root枠/identity判断/new freshが揃ってからPython stdlibの1子1batch。予定nice実値10以上、CPU soft2/hard3秒、wall3秒、有限TERM0.5秒/KILL後wait1秒、自動retry0。旧decisionを流用せずunknownは停止。新SDK/設定/他process停止はしない。

readerは保存結果だけを読み、予想→型判断の木と通常/診断の別列→原典/コード→答え→限界へ進む。rootの既存pageで実DOM/2幅画像を確認し、作者browser/server起動0。限定Skill6問と独立受入・status読戻しまで結ぶ。全入力のprogress/preservation、型安全性、型消去の一般定理、未実行枝、一般Agent評価は対象外。作者加算0、171からの追加判断はroot担当。
