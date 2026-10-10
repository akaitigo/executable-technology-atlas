# トークンとbuttonの所有範囲を学ぶ

同じthemeと小さいbutton APIで「Aだけのoverrideを親へ置いた漏れ」「Aへ局所配置した修正」「不正色の計算時無効」「入力検証でthemeへ戻す」を比較する有限1教材です。実配布されたdesign systemでも全分野の完成でもありません。

## 前提から実務判断まで

HTML button、CSS selector/継承、JavaScript eventが前提です。[教材](index.html#learning-path)は予想→操作→比較→所有図/実装/一次資料→答えの順です。

テーマのsemantic tokenをcomponentが消費し、instance overrideが上書きする仕組みを[CSS](styles.css)と[DOM制御](lesson.mjs)で読みます。native button APIはlabel/type/primary variant/disabledと6桁hexのA背景overrideのみ。入力検証は[api.mjs](api.mjs)にあり、Web全色構文を拒否する仕様とは主張しません。

正常：light/dark、未定義overrideのtheme fallback、Aの局所上書き。意図異常：親へ置いた値がBにも継承。不正色not-a-colorはcustom property自体へ定義できてもbackground-colorへの置換が計算時に不正となり透明になり、varのfallbackへ戻るとは限りません。修正版はAPI境界で非hexを採用せずthemeを使います。境界：削除、native disabled属性、TabがAを飛ばすこと、Enter/Spaceのactivation。

実務で判断できるのは、上書きの所有scope・component APIの型境界・テーマ値とinstance値の役割・native操作を検査する必要です。scope修正は任意の外部CSSからの隔離を保証しません。buttonの見た目を整えただけでアクセシビリティ適合、token配布、採用運用まで保証できません。

## 起動・検査

このdirectoryでNode標準機能だけを使います（新規依存なし）。

```sh
node serve.mjs
```

表示された一時loopback URLをBrowserで開き、theme、A色、disabled、Tab/Enter/Spaceを操作。サーバーはCtrl+Cで停止。ホスト審査が拒否した場合に設定変更で迂回しません。

```sh
node verify.mjs
node check.mjs
node verify.mjs --record node-attempt-new
node check.mjs --record check-attempt-new
```

通常2検査はread-only。明示recordだけ未使用directoryへ新規保存し、既存directoryはEEXIST拒否。verifyはpure APIを独立状態表へ照合し、checkは保存済み実Browser原票と実computed style/DOM/属性/keyboard eventを[独立token表](oracle.mjs)へ照合します。check自体はBrowserを起動しません。[原票と制約](VERIFICATION.md) / [専用Skill](skills/atlas-design-system-component-engineering/SKILL.md)。Browser再取得は原票・画像を新directoryへ明示保存し、source bindingが変われば新実行が必要です。

## 次に何を学ぶか：主要未教材coverage

網羅的inventoryではありません。次の8領域は未教材で、以下4案はすべて未実装/未検証。[画面の学習案](index.html#next-experiments)にも接続します。

| 未教材IDと概念 | 問い | 次の実験・公式locator |
|---|---|---|
| token-format-pipeline：primitive/semantic alias、型、変換 | alias cycleや型不一致をbuild時に検出できるか | E1：tokenファイルの型検証・CSS変換・cycle注入。[DTCG aliases](https://www.designtokens.org/tr/2025.10/format/#aliases-references)、[types](https://www.designtokens.org/tr/2025.10/format/#types) |
| theme-modes-governance：mode、命名、変更責任 | 複数brand/modeの互換性は何で守るか | E1：brand/mode欠落の拒否と変更レビュー。同じDTCG原典を起点にmode方針は独自に設計 |
| component-composition：slot、state、compound component | button以外の構成でAPIをどう分けるか | E2：icon/label/slotの状態API。[HTML slot](https://html.spec.whatwg.org/multipage/scripting.html#the-slot-element) |
| style-isolation：cascade layer、Shadow DOM、外部CSS | 利用側CSSとどの境界で共存するか | E2：Shadow DOMとlayerの干渉比較。[CSS layers](https://www.w3.org/TR/css-cascade-5/#layering) |
| accessibility-internationalization：accessible name、RTL、forced colors | 視覚以外と多言語の操作をどう検証するか | E3：icon-only/RTL/forced colors。[AccName](https://www.w3.org/TR/accname-1.2/#computation-steps)、[forced colors](https://www.w3.org/TR/css-color-adjust-1/#forced-colors-mode) |
| responsive-visual-regression：viewport、layout、font、screenshot差分 | 画面幅と環境差をどう検査するか | E3：狭幅/複数環境の画像と操作照合。[WCAG focus visible](https://www.w3.org/TR/WCAG22/#focus-visible)（画像差分手法自体の規定ではない） |
| package-version-migration：配布、exports、互換API、deprecation | 利用側の移行を実packageでどう保証するか | E4：別consumerへの実package配布と移行。[Node entry points](https://nodejs.org/api/packages.html#package-entry-points)、[npm pack](https://docs.npmjs.com/cli/v11/commands/npm-pack) |
| documentation-adoption-operations：利用例、採用、品質gate、運用 | docと実packageの乖離をどう防ぐか | E4：doc例をconsumerで実行し互換性を検査。Node/npm原典を起点に採用/運用条件を設計 |

## 一次資料と観測を区別する

[CSS Custom Properties §3](https://www.w3.org/TR/css-variables-1/#using-variables) / [§3.1 invalid variables](https://www.w3.org/TR/css-variables-1/#invalid-variables)が継承・置換・不正値処理の根拠。[HTML button](https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element)がnative属性の根拠。これらの仕様全体をこの一例で検証したとは言いません。DTCGのtokenファイル形式は読書/次案のみで、今回のCSS変数を形式適合データとは呼びません。
