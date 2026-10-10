# 検証記録

2026-10-05の有限unit検証。Subject/全体Goalはincomplete、入口分野数への加算0。実AT音声・WCAG適合は未測定です。

## 現在Sourceの実行原票

- [Node原票](observations/node-attempt-02/raw.json)：Node v25.2.1 / V8 14.1.146.11-node.14、darwin arm64。独立期待列24地点、合成classifier contract **70 assertion**。Browser focusの実行ではありません。
- [Browser原票](observations/browser-attempt-05/raw.json)：実IAB Chrome/154.0.0.0、ja、1280×720、DPR 2。4経路＋Skill独立試行の **5 run / 29 checkpoint / 29 screenshot**。各runはattempt 1 / retries 0。全キーはdocumented `Tab.pressKey(null,key)`で現在のfocusへ入力し、trusted keydown/keyup、focusin/out、cancel/close、実時刻、Source11件とplan digest、DOM/AXを保存。
- [照合原票](observations/check-attempt-03/raw.json)：**1,797 positive assertion / 9 negative fixture拒否 / 5,641 negative traversal check**。この件数は保存原票の照合で、追加の実Browser入力件数ではありません。
- module-local Skillの正常routeは新run `skill-native-basic` で実キー入力。未対応routeは実AT音声/WCAG全適合を測定済みと扱わずE2/E4へ案内。quick_validateはexit 0 / `Skill is valid!`。同一agent実行であり独立Forward Evalではありません。

## 期待と実測

[期待列](oracle.mjs)は実測前に固定し、結果に合わせて変更していません。以下の「一致」は指定キー列だけです。

| 経路 | 実activeElement列（準備から） | 期待との差 |
|---|---|---|
| native-basic | launch → native-first → native-close → native-first → launch | 0 |
| native-wrap | launch → native-first → native-close → BODY → native-close → launch | 1：最後からTab時、期待native-firstではなくBODY |
| native-close | launch → native-first → native-close → launch | 0 |
| role-fault | launch → launch → background → role-first → background → background → role-first → role-close → BODY | 5。cleanup移動2地点は比較対象外 |
| skill-native-basic | launch → native-first → native-close → native-first → launch | 0 |

native-wrap境界ではdialogはopenかつ`:modal=true`のまま、appの実Browser `document.hasFocus()`記録はfalse。その後Shift+Tabでnative-closeへ戻りました。Browser UIのどのcontrolに移ったかは測定しておらず断定しません。外側DOM controlへ抜けたrole-faultとは区別します。

role-faultは開いても起点focusが残り、Tab/逆Tabでbackgroundへ移動。Escapeで閉じず、閉じるbutton後はBODYで起点へ戻りません。AXにdialog role/nameが現れることは、このキー操作契約の実装を意味しません。

![Escape後も開いていて背景にfocusがある故障div](observations/browser-attempt-05/role-fault-5.jpg)

## 観測API境界と失敗保持

CUA read-only DOM facadeには`document.hasFocus()`/element.inert propertyがありません。documentHasFocusだけはapp実Browser原票から取得し、その他stateはDOM再読取。inertは反映属性の`hasAttribute('inert')`で読みました。DOM inert属性falseはnative modal背景制約なしの証明ではありません。AX treeは音声読み上げ測定の代替ではありません。

- [通常権限preview失敗](observations/preview-default-denied/raw.json)：127.0.0.1 listen EPERM、exit 1。原票保持後、同一sessionのhost reviewを経た同じcommandで一時表示。
- [Browser観測失敗01](observations/browser-attempt-01/raw.json)：hasFocus facade制約。保持。
- [Browser入力失敗02](observations/browser-attempt-02/raw.json)：nonfocusable html locator press deadline。準備原票を保持し、正式native inputへ変更。キーを途中で再focusする方式は不採用。
- [Browser原票03](observations/browser-attempt-03/raw.json)と[checker失敗01](observations/check-attempt-01/raw.json)：facade inert property未提供により観測fieldが欠落。失敗を保持して属性の読取りだけを修正、全5runを新規取得。
- [Browser原票04](observations/browser-attempt-04/raw.json)と[成功check02](observations/check-attempt-02/raw.json)：旧Sourceでは成功。check.mjsのdefault原票参照を使える現在版へ修正したためSource digestが変更され、Node02/Browser05を全実再実行。旧原票は変更せず歴史的記録として保持。
- 観測helperの文字列生成もREPLに拒否されました。Source/Oracle/Browser stateの変更には用いず、文字列生成なしの関数を直接定義して実行。

## 通常照合・所有resource終了

```sh
node verify.mjs
node check.mjs
```

通常は読取りだけ。新原票は明示`--record observations/NEW-ID`、別Browser原票は`--browser observations/NEW-BROWSER/raw.json`。既存directoryのrecord再使用はEEXISTで拒否します。現在defaultはNode02/Browser05です。

作成tab 17を閉じ、所有server session 65066/94226をSIGINTで終了（exit 130）。使用port 50729/51826は`lsof -nP -iTCP:50729 -iTCP:51826 -sTCP:LISTEN`がexit 1 / 空出力でLISTENなし。外部公開、依存追加、OS/実AT設定変更、Git操作は行っていません。

最終のSource/原票/文書hash・mtime、通常checkerのread-only性、既存directory拒否、元ボタン教材22件＋XR41件の不変確認は `observations/read-only-audit/raw.json` へ保存します（監査自身は循環hashを避けてinventory対象外）。E1–E4は未制作のままで、[残る問いと原典](scope.json)に接続しています。
