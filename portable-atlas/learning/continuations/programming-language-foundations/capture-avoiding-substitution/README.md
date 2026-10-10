# 捕獲回避置換: 外側y=10が引数3へ化ける？

[元Subjectの次実験1](../../../subjects/programming-language-foundations/README.md#次の4実験未実施)から進む、独自open-term ASTの有限単元。元教材のclosure環境を前提に、自由/束縛name、alpha rename、置換を学ぶ。Python stdlibだけ、text parserやhost eval/execを使わない。

読む順番: 元Subject→[事前契約](EXPECTATIONS.md)→[UI](index.html)の2予想→正常/naive/拒否/実Error→[手書きfree集合とAST](oracle.json)→[環境oracle](oracle.py)→[Stlc原典locator](SOURCES.md)→答え/実務判断。

中心は `[x:=y](λy.x)`。安全版λv0.y、naive版λy.y。外側y=10で引数3を適用すると10対3。置換前λy.xのfree={x}、置換term yのfree={y}、安全結果free={y}、naive結果free={}。naiveは自由yをbinder yへ捕獲する故障で、名前に同じ字があるだけでは同じ束縛にならない。

| 対照 | 安全 / naiveの整数 | 判断点 |
|---|---|---|
| 中心capture | 10 / 3 | free yを保つ |
| 同名target binder λx.x | 3 / 3 | 置換停止 |
| 衝突なし | 10 / 10 | rename不要 |
| free v0衝突 | 15 / 8 | fresh v1、free v0も保つ |
| bound v0衝突 | 10 / 3 | bound nameもfresh候補から除外 |
| 内側同名binder | 14 / 7 | renameは内側yを越えない |
| target不在 / closed置換 | 3 / 3、9 / 9 | 不要rename・open限定の故障を区別 |
| open lambda / fresh2回 | 12 / 5、10 / 4 | replacementのfree、生成freshの重複回避 |

## 実装と再現

```sh
python3 -B runner.py --case capture
python3 -B runner.py --case invalid-binder  # INPUT_REFUSED exit2
python3 -B runner.py --case execution-failure # EXECUTION_FAILURE exit1
python3 -B checker.py
python3 -B server.py
python3 -B route.py substitution
python3 -B route.py type-safety       # unsupported exit2
python3 -B runner.py --record         # 明示、新receiptだけ追加
python3 -B checker.py --record-binding
```

serverはdynamic127.0.0.1 port。UIは同じ[producer](producer.py)の実AST置換・環境評価を呼ぶ。JSのAST文字列表示は計算結果の表示で、別評価器ではない。終了は自身のCtrl-Cと所有tabだけ。[関連selection/draft教材](../../frontend-application-architecture/selection-draft-cancel/README.md)と同じく、入力の所有と旧比較の保持を分ける。

通常runner/checker/routeは書込なし。CLIはNORMAL exit0、構造拒否exit2、実行失敗exit1。明示[runner record](runner.py)は18個の実child attemptのUTC・実exit・stdout/stderr、入力、sourceSHAを新UUID rawへ保存する。旧rawを上書きせず、想定外失敗はcurrentに昇格しない。HTTPは同じproducerをin-process実行し、attemptに実開始/終了時刻と遅延を表示する。HTTP200とCLI exitを混同しない。

ASTはInt/Var/Lam/App/Add、name規則・literal範囲・64node/depth16・env/引数型を有限契約で拒否。validationは型安全性の静的証明ではない。実RuntimeError注入は両経路結果なし、正常答えを隠す。一般入力のruntimeエラー/予算停止は理由付き失敗として保持する。

各予想の単独変更は新値・他欄を保持し旧raw/比較/答えを消す。条件resetは2予想・AST上書きも消す。拒否は予想を保持して理由と比較できる。成功の後に拒否/失敗が来ても旧整数/答えを残さない。「遅い実行」は所有requestのみ1800ms遅らせ、旧responseのversionが違えば破棄数だけ増やし最新結果を変えない。任意network race全体の保証ではない。

## 独立oracleと原典の前提

[oracle](oracle.py)はproducerの置換/rename/free関数をimportしない。元termをbound indexとfree-nameへcompileし、replacementを外側環境で評価、その値をfree targetへ束縛して元termを環境評価する。10正常ケースのsafe値をこの経路と手計算へ照合し、safe/naive生成ASTも別環境評価器で検査。4種類のfree集合、生成AST、fresh対は実行前の手書き表と照合する。名前置換の別コピーをoracleにしない。

Software Foundations Stlc「Substitution」は同名binderでの停止を説明する。Technical noteはopen replacementによるcaptureを示し、closed termのstep relationではその複雑さを避ける。今回のInt/Add/open-term/alpha renameは独自拡張で、原典を一般open置換へそのまま適用しない。一般言語互換・Rocq証明・型安全性証明は未実証。

答え: binder名をfreshへ変えて、置換termの自由な参照を同じ外側環境へ戻す。binder=targetなら置換停止、renameも内側同名binderで停止。すべての文字列x/yを置換する方法ではこの意味を保てない。

実務判断: open inputを扱うmacro/interpreterのレビューではfree/bound集合とrename停止点を検査する。closed入力の成功や1つの整数一致を一般置換の正しさへ外挿しない。AST hashは改変検出で、意味同値の証明ではない。

## 次の3実験（未実施）と有限coverage

1. alpha同値の判定とbound-index表現を新契約で比較。fresh文字列の一致と意味同値を分ける。
2. 別small-step評価器と規則導出を比較。[元Subject実験2](../../../subjects/programming-language-foundations/README.md)
3. Int/arrowの型付けを実装し、progress/preservationを別証明課題へ。[元Subject実験3](../../../subjects/programming-language-foundations/README.md)

18case/5AST kind/固定env・引数だけ。一般置換補題、全alpha同値、一般言語互換、型安全性、termination、mutable store、effect、性能は未実証。元Subject/他教材を凍結し、Core/fullGate/設定/install/公開/commit/push/課金/権限設定は変更しない。

[fixture](fixture.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-capture-substitution/SKILL.md)
