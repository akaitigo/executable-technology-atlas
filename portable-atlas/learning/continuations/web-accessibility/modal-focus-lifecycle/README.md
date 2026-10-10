# モーダルのfocusを開閉で追う

[元のボタン教材](../../../subjects/web-accessibility/README.md)の[学習経路・実験2](../../../subjects/web-accessibility/LEARNING_PATH.md)を実制作する深掘り単元です。入口分野数へ追加せず、Subjectは **incomplete**。元教材・XR・元QA原票はread-onlyで、新単元のEvidenceだけを追加します。

## 前提 → 予想 → 操作

前提はHTML/DOM/event/focus。見た目、role/name、Browserキー動作、activeElement、AX、実読み上げを区別します。開くとどこへfocusし、Tab/Shift+Tab、Escape、閉じるbuttonでどこへ移るかを先に予想します。

```sh
node serve.mjs
```

表示された動的127.0.0.1 URLを開き、予想を選びます。確認後はCtrl+Cで所有serverを終了します。第三者素材・新依存・実AT/OS設定変更・公開はありません。

1. native-basicを選んで「新しい試行を準備」。準備だけが起点buttonへprogrammatic focusします。
2. Enterで開き、Tab→Shift+Tab→Escape。初期focus、内側2control、起点復帰を見る。
3. native-wrapでEnter→Tab→Tab→Shift+Tab→Escape。最後のcontrolを越える境界を別測定する。
4. native-closeでEnter→Tab→Enter。閉じるbuttonからの復帰を比較する。
5. role-faultでEnter→Tab→Tab→Shift+Tab→Escape。故障divのfocus漏れとEscape不作動を観察し、Tab→Tab→Enterで閉じる。cleanup移動2地点はAPG列と比較しない。
6. 実装と原典、原票を読み、答えを開く。元教材の読み取り参照はpreviewのreference/ aliasで提供し、fixture動作は元Sourceに依存しない。

## 今回の実装と独立期待列

[plan.json](plan.json)は4経路・24checkpoint（準備も含む）。Skill正常routeではnative-basicを別runで追試します。[oracle.mjs](oracle.mjs)はDOM実装をimportせず、APGに基づく望ましいfocus/open列を固定しています。実測を期待へ補正しません。

nativeは `dialog.showModal()` と第一buttonのautofocusを使用し、閉じるbuttonは `dialog.close()`。独自focus trap/Escape handler/復帰focus処理はありません。role-only divはroleと名前だけ、hiddenを外すだけで表示します。focus・trap・Escape・復帰を実装せず、aria-modalも付けない故障fixtureです。これは実務用の正しいcustom dialogではありません。[実装](lesson.mjs)を参照してください。

| 望ましい契約 | 正常として確認する経路 | 故障/境界の比較 |
|---|---|---|
| 初期focusが内側へ | native-basic / native-close | role-onlyで起点が残るか |
| Tab→次、ShiftTab→前 | native-basic | role-onlyで背景へ抜けるか |
| 最後から最初へ循環 | native-wrap | BODY/Browser focusなどの差異を保持 |
| Escapeで閉じる | native-basic / native-wrap | role-onlyでは閉じないか |
| 閉じるbutton後に起点へ | native-close | hiddenにしたdivで起点を失うか |

DOMのinert属性がfalseでもnative showModalの背景制約までfalseとは判定できません。activeElement、`:modal`、現在open、DOM/AXを併読します。BODYが出た場合は「第一controlへ移った」と書き換えず、期待との不一致として報告します。Browser UIの境界と外側DOM controlへの漏れも同じ事象と呼びません。

## 実務判断と限界

role宣言と操作契約は別。nativeを選んでも内容に応じたinitialfocus、起点消失時の復帰先、入れ子、Browser/OS/ATを確認します。今回の2control・1Browser経路をWCAG適合、全AT、全dialog設計へ広げません。CUAのBrowser key入力とtrusted DOM eventを観測しますが、物理keyboard/device・スクリーンリーダー音声は測定しません。AX treeは読み上げの代用ではありません。

[検証記録](VERIFICATION.md)に正常/故障/期待差異を保存します。Nodeは合成stateで独立期待列classifierを検査するだけで、Browser focusを動かしません。

## 未教材の問いと次実験

[scope.json](scope.json)に増分と残りを対応付けています。以下は未制作です。

- E1 長文/破壊操作/起点消失/入れ子：何を初期focusし、どの論理的起点へ復帰するか。独立fixtureで各1条件を比較。[APG Dialog Keyboard Interaction・Notes](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- E2 名前/説明、status、フォームerror、複合widget：DOM/AXがどの操作・通知へ繋がるか。短いstatusとformを実ATで別観測し、個別widgetキー契約へ展開。[Status Messages Intent](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)、[APG Patterns](https://www.w3.org/WAI/ARIA/apg/patterns/)
- E3 reflow/zoom/focus可視性・遮蔽/contrast/forced colors/touch：表示条件が変わってもcontrolを見失わないか。320 CSS pxと実zoomを分けて測る。[Reflow Intent](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)、[Focus Visible Intent](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
- E4 landmark/見出し/表/言語/読み順、media、多入力、実AT互換/継続監査：用途と利用者範囲を定めて目的到達を測る。構造・字幕・代替入力を別fixtureに分割。[WCAG 2.2 Guidelines 1.2/1.3/2.1/2.4/3.1/4.1](https://www.w3.org/TR/WCAG22/)

## 原典とEvidence

[APG Dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/) Keyboard Interactionは望ましい操作指針。[HTML dialog](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element)のfocusing/closing stepsはBrowser機構の原典。[WAI-ARIA 1.2 §3.2とdialog role](https://www.w3.org/TR/wai-aria-1.2/#dialog)で意味と操作の役割を読む。本文/code example/第三者画像はコピーしません。

```sh
node verify.mjs
node check.mjs
```

通常checkerはread-only。新原票だけ `node verify.mjs --record observations/NEW-ID` / `node check.mjs --record observations/NEW-CHECK` を指定し、既存directoryをEEXISTで拒否します。別原票は `--node observations/NEW-ID/raw.json --browser observations/NEW-BROWSER/raw.json` で照合できます。実Browser操作からactiveElement列、trusted key、時刻/環境、DOM/AX、実Screenshot、Source/input/artifact SHA-256を保存します。時刻や結果を既存原票へ後付けしません。[有限Skill](skills/atlas-modal-focus-lifecycle/SKILL.md)はmodule-localで、独立Forward Evalではありません。全体Goal完成を主張しません。
