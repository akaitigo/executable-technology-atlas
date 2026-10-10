# 見た目では分からないボタン操作

native buttonとclick-only divで同じカウント操作を行い、Tab到達、Enter/Space、focus、role/nameを個別に観察する一教材です。Subject全体やWCAG適合の完成を示すものではありません。

## 試す

このdirectoryで `node serve.mjs` を実行し、表示されたloopback URLをブラウザで開きます。依存追加は不要です。終了はCtrl+C。通常の検査は記録を変更しません。

```sh
node verify.mjs
node verify.mjs --browser observations/browser-attempt-01/browser.json
node audit.mjs
```

新しいNode記録を保存する場合だけ、未使用directory名を明示します。既存記録は上書きしません。

```sh
node verify.mjs --record node-attempt-02
```

`audit.mjs` は観測間の時刻・対象キー・Tab遷移・trusted入力を照合します。以前のキー記録を流用した負例など3件を拒否します。保存を求めた場合だけ `node audit.mjs --record 未使用名` を使います。

1. 予想を保存する。
2. Tabの出発点 → Tab → native button → Enter/Spaceを試す。次のTabはclick-only divを飛ばす。divはマウスでなら増える。
3. 右側をrole+tabindexだけへ変更。Tab到達とbutton roleはあるが、Enter/Spaceでは増えない。
4. 修正版へ変更。同じTab/Enter/Spaceで増え、フォーカス枠が残る。
5. 無効にするとnativeはTab順から外れ、修正版divは到達できるが動作を拒否する。
6. 別の名前欠落ボタンをAccessibility treeで調べる。文字は見えてもbutton nameが空。修正checkboxで名前が戻る。
7. 実装と一次資料を読み、修正を選んで回答する。

役割と名前の確認にはブラウザのAccessibility機能を使います。DOMのrole属性/textContentをcomputed accessible nameと同一視しません。実録は [VERIFICATION.md](VERIFICATION.md) を参照してください。

## ソースと限界

動作は独自のHTML/CSS/JS。第三者素材・ライブラリはありません。[W3C APG Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/button/)を動作指針として参照し、名前欠落の例は[AccName §4.3.2](https://www.w3.org/TR/accname-1.2/#computation-steps)のhidden判定を踏まえています。

Space保留のblur取消、repeat、disabled中の拒否はNodeの独立期待値表でも検査します。これは実ブラウザでのキー長押しや全AT組合せの証明ではありません。実スクリーンリーダー音声、WCAG監査、他Browser/OS、フォームや複合widget等は未制作・未実測です。[scope.json](scope.json) に分離しています。

module-local Skillは [skills/atlas-web-accessibility/SKILL.md](skills/atlas-web-accessibility/SKILL.md)。グローバルインストールはしません。
