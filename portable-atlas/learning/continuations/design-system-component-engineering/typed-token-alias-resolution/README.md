# 型付きtoken alias: blue変更は利用先へ連動する？

[元Subject coverageのtoken-format-pipeline / E1](../../../subjects/design-system-component-engineering/README.md#次に何を学ぶか主要未教材coverage)のうち、primitive/semantic alias・型検査・CSS変換を固定color subsetで学ぶ追加単元。前提はJSON、参照、CSS custom property、Browser computed style。

読む順番: 元Subjectのtheme/instance所有→[事前契約](EXPECTATIONS.md)→[UI](index.html)の2予想→正常/未解決CSS故障/拒否/実Error→[固定参照先・sRGB・CSS表](oracle.json)→[独立検証](oracle.py)→[DTCG原典locator](SOURCES.md)→答え/実務判断。[関連selection/draft](../../frontend-application-architecture/selection-draft-cancel/README.md)は入力の所有と旧比較リセットの観点で読む。

## 今回埋めた有限範囲

5固定token: primitive.blue/green、semantic.action/focus/positive。action→blue、focus→action、positive→green。blueの値をredに変更するとA/B背景とfocus outlineがredへ連動し、positive badgeはgreenのまま。actionの参照をgreenへ変更するとA/B/focusもgreen。元のJSON参照は保持し、CSS生成時に実値を取り出す。

| 対照 | Python生成 | 実Browser computed |
|---|---|---|
| normal blue | action/focus=rgb(0 0 255) | A/B/outline青、positive緑 |
| primitive値red | blue/action/focus=rgb(255 0 0) | A/B/outline赤、positive緑 |
| action aliasをgreenへ | action/focus=rgb(0 255 0) | A/B/outlineも緑 |
| 故障の未解決CSS | aliasへ未定義var参照を誤生成 | A/B/positive透明、outline=currentColor |
| cycle/missing/type mismatch | CSS生成前にINPUT_REFUSED | 旧CSSを消し未実行の灰色へ |

明示$type、curly-braceの値全体alias、sRGBの有限component3個、不透明alpha=1（省略時1）だけ。独自8bit丸めfloor(component×255+0.5)で0.5→128も別case。numberは型不一致を認識する検査用でCSS変換未対応。詳細な構造・優先順位・17caseは契約/fixtureを参照する。

## 実装・実行・原票

```sh
python3 -B runner.py --case blue
python3 -B runner.py --case primitive-red
python3 -B runner.py --case cycle          # INPUT_REFUSED exit2
python3 -B runner.py --case execution-failure # EXECUTION_FAILURE exit1
python3 -B checker.py
python3 -B server.py
python3 -B route.py tokens
python3 -B route.py full-dtcg             # unsupported exit2
python3 -B runner.py --record             # 新UTC/UUID receiptだけ保存
python3 -B checker.py --record-binding
```

serverはdynamic127.0.0.1 port。UIは同じPython [producer](producer.py)へ入力を送り、返されたCSSを専有#token-scopeへ適用する。UIの実getComputedStyle表示と、IABの別DOM readの値を[oracle](oracle.py)の固定表に照合する。見た目やPythonの色表をBrowser rawとして代用しない。終了は所有terminalのCtrl-Cと所有tabだけ。

[producer](producer.py)は構造・color・alias型・cycle/missingを検査後、全5tokenを解決してからCSSを作る。通常の型解決結果は故障caseでも正しいが、故障CSS writerだけが参照名を未定義の--unresolvedへ変える。CSS生成成功と実computed一致を別々に検査する。

[oracle](oracle.py)はresolverをimportしない。実行前の固定最終参照先・正規化sRGB・CSS全文・computed値が正本。実reference/resolved traceも固定mapへ照合する。独立は別実装/手計算であり、別の人によるbrand承認ではない。

通常runner/checker/routeは書込なし。CLIはNORMAL/意図故障exit0、拒否exit2、実行失敗exit1。明示recordは17実child attemptのUTC/実exit/stdout/stderr、入力、sourceSHAを新rawへ保存、旧raw保持。想定外失敗はcurrentへ昇格しない。HTTPはin-process producer、HTTP200とCLI exitを混同しない。source変更は新実行が必要。digestは改変検出で仕様適合証明ではない。

## 予想・答えdetails・実務判断

全予想controlごとに、成功比較→答えdetailsを開く→その予想だけ変更を実IABで確認する。新値と他欄を保持し、旧答え本文は空・detailsは閉じて隠す。旧CSS/raw/computed表示も消す。条件resetは両予想とJSON上書きを消す。拒否でも予想を保持して理由と比較できる。実ErrorはCSSなし・正常答えなし。説明図は手生成の正常依存図で実captureではない。

答え: semantic aliasの利用先は参照先のprimitive変更へ連動する。まずtype/参照を検査し、変換後にCSS変数名と実computedを検査する。cycle/missingを適当な色で隠さず、故障の未解決CSSを正常のfallbackと混同しない。

実務判断: tokenの所有・参照・typeとcomponentのCSS消費を分けてレビューする。生成物が存在してもBrowserが意図した色を計算したとは限らない。1brand・5tokenの成功を命名規約、移行承認、package互換性へ外挿しない。

## 残ったcoverageと次の3実験（未実施）

1. JSON Pointer/$ref、group type継承、複合型を新契約で検査。元token-format-pipeline/E1の残り。
2. 複数brand/modeと変更責任の方針を比較。元theme-modes-governance/E1。人の承認は生成しない。
3. 別consumerへのpackage配布とmigrationを実行。元package-version-migration/E4。

DTCG 2025.10 Format/Colorの全spec、他色空間、半透明、hex/none、group拡張、metadata、brand governance、全形式、package配布、視覚回帰/a11y適合/全Browserは未実証。元READMEの他7未教材領域も未達。今回の17caseをSubject全体完成へ昇格しない。元/関連教材は凍結維持。install/設定/課金/公開/Core/fullGate/commit/pushは行わない。

[fixture](fixture.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-typed-color-alias/SKILL.md)
