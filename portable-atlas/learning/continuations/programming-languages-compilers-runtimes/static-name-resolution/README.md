# 静的名前解決と宣言ID

[元Subjectの学習パス](../../../subjects/programming-languages-compilers-runtimes/LEARNING_PATH.md) §6「実験2」の有限継続教材。元の整数式lexer/parserを変えず、独立した明示ASTを使う。まず規則を読む→注目useの宣言IDを予想→条件を変える→実行→ASTと束縛・値・拒否位置を比較→原典/実装/rawを読む→答えと実務判断を開く。

blockは独立scope、letはその位置で宣言、useは内側から見える先行同名宣言を探す。宣言IDはAST全体で一意。resolverが全ASTを走査してuse→宣言IDを固定し、成功したときだけevaluatorが逐次letを初期化、IDで値を読む。scopeを離れてもIDの値保存は残るが、名前の可視性はresolverに固定されている。最大32 node/depth4、整数literal 0..100、同scope同名let不可、3種のnodeでexact keys。UI/APIは固定8入力だけ。

| ケース | strict期待／故障結果 |
|---|---|
| shadow | before→outer10、inner→inner20、after→outer10 |
| before-inner-let | 内側let前use→outer10、let後20、外側へ戻る10 |
| sibling-scope | 第1block20、第2blockはouter10、after10 |
| scope-escape | u-outside/yを静的拒否。u-inside部分束縛あり、全評価未開始 |
| undeclared | u-z/zを静的拒否、全評価未開始 |
| before-local-let | 外側もないu-early/xを静的拒否、全評価未開始 |
| bad-pre-register | 未来のd-innerへ誤束縛。未初期化IDを実evaluatorが拒否（値は返さない） |
| bad-flat-scope | u-after→d-innerへ漏れ、[10,20,20]。正しくは[10,20,10] |

strict6の内訳は評価完了3・期待する静的拒否3。故障比較2は別枠（評価拒否1・誤った評価完了1）。期待拒否を実験の異常終了や正常プログラム数へ混ぜない。

## 再現と証拠

このdirectoryで `python3 -B runner.py --case before-inner-let`。明示保存は `python3 -B runner.py --record` のみでfresh UTC directoryを作る。採用原票は `observations/20261005T114623924298Z/raw.json`、実command exit0。UTC/runtime/input/resolution trace/evaluation trace/4 source SHAを保持する。`python3 -B check.py` と `python3 -B skills/atlas-static-name-resolution/route.py name-resolution` は保存原票をread-only検査する。

checkerはproducerをimportしない。独立したparent環境lookupで逐次name→(宣言ID,値)を計算し、手書きoracleと宣言ID・値・拒否位置を照合。故障版は正しいlookupとの差も要求する。resolver bind event、evaluator initialize-before-use、静的拒否後の無評価、値の順序を確認し、5種の証拠改変を拒否する。

`python3 -B server.py` は127.0.0.1:0で所有portを予約。sandbox bind拒否は別実行失敗として保持し、同じserverをhost許可で実IAB検査する。予想/条件変更で結果・trace/raw・答えをresetし、古いresponseもgeneration tokenで破棄。ブラウザQAは実操作の要約、raw本文の架空exportは作らない。captureはツール表示のみの場合、その制約をQAに明示する。

## 原典と契約の範囲

著者Robert Nystromの[Resolving and Bindingの公開ソース](https://github.com/munificent/craftinginterpreters/blob/master/book/resolving-and-binding.md)、Static ScopeおよびResolving Variable Bindingsを2026-10-05確認。主サイト取得失敗から著者GitHubへfallback。先行宣言/最内scopeと静的解決を評価へ渡す設計を参照し、教材は独自の有限AST契約と宣言ID実装で作成した。moving masterであり版固定の仕様準拠証明ではない。原典の文章/コードを転載していない。

JavaScript letのTDZ、closure、型検査、parser、任意ソースeval、言語全体の適合は未実装。Subject/Atlas全体の完了、Core監査・全Gate、commit/push/publicationは実施していない。

## 次の未実施教材案

1. initializerに式を加える。自分自身を読むletと外側letを読む式を入力にし、宣言済み/初期化済みの規則を比較する。原典同章Resolving Variable Bindingsの宣言・定義の区別を確認する。現単元はliteralのみ。
2. closureのuseを宣言IDへ固定する。宣言後に同scopeへ名前を追加する入力で、可変環境lookupと固定bindingを比較する。原典同章Static Scopeのclosure反例を確認する。現単元はclosureなし。
3. source位置とshadow警告を加える。入れ子同名宣言・未宣言useを入力にして、宣言IDと位置付き診断を比較する。原典同章Resolution Errorsを確認する。現単元はnode IDのみ。
