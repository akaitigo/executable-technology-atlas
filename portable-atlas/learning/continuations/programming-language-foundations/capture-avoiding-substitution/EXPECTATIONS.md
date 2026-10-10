# 実装前に固定する有限契約

独自ASTはInt/Var/Lam/App/Add、nameはASCII `[a-z][a-z0-9_]{0,15}`、Intはboolを除く整数-1000..1000。各term/replacementは最大64node、root深さ0から最大16。fieldはkindごとに厳密一致。environmentは同name規則→同整数範囲、argumentsは1..3整数。JSON syntax、形/型、name、深さ/node数を拒否する。構造拒否はINPUT_REFUSEDで評価を開始しない。

置換は自由なtargetだけ。binder=targetならそのLam以下へ入らない。targetがbodyのfreeに無ければalpha rename不要。binderがreplacementのfreeに含まれると、全term/replacementのfree/bound nameとtargetを避け、v0,v1...最初の未使用nameへrenameする。生成済みfreshも予約する。renameは内側の同名binderで停止する。

中心例はλy.xへx:=y。安全版λv0.y、naive版λy.y。外側y=10、引数3なら10対3。naive版もbinder=targetで停止するが、衝突時renameを省く故障。safeの定義を原典の誤り修正と呼ばない。

[手書きoracle](oracle.json)は実行前に各AST、original/replacement/safe/naiveのfree-name集合、整数結果、fresh対を固定。free v0がある例とbound v0がある例はv1を使う。内側同名binder、2回fresh、target不在、closed replacementを別対照にする。18caseだけ。

独立oracleは名前置換/renameを実装しない。元termをbound indexとfree-nameにコンパイルし、replacementを外側環境で評価、その値をfree targetへ束縛して元termを環境評価する。safeの整数結果をこの評価と手計算へ照合。生成ASTも同じ別評価器で検査する。free集合は手書き集合が正本。一般置換補題・alpha同値の証明ではない。

実RuntimeError注入はEXECUTION_FAILUREで両経路結果なし、正常答えへ進まない。通常言語runtimeの予期しないunbound/type/budgetエラーも理由付き失敗として残す。budgetは400評価stepでありtermination証明ではない。

UIは条件resetで2予想、AST上書き、旧raw/比較/答えを消す。各予想単独変更は新値と他欄を保持し旧raw/比較/答えを消す。拒否も予想と実理由を比較。実行開始/入力変更のversionで旧応答を破棄し、最新結果を旧応答で上書きしない。遅い実行は自分のHTTP requestだけ1800ms遅延する。

通常runner/checker/routeは書込なし。明示recordは新UTC/UUID原票、実attempt/exit/source hashを保存し旧原票を保持。想定外実行失敗はcurrentへ昇格しない。captureは実IAB byteのみ、再構成しない。
