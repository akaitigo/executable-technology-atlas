# native ES modulesのlive binding

2つのimporterが同じcounterを読む一教材です。named/namespaceのlive参照、初回の数値snapshot、同URLの再import、importerからの代入拒否を実Browserで操作します。HTTP読込失敗と構文失敗は別Documentのiframeへ隔離しました。Subject全体の完成ではありません。

## 学習の道筋と実務判断

前提はlet/const、関数、object property、Promise/try-catch。次に「export元のbinding→importerの間接参照→URL/Document単位の評価→読込/parse」を、この教材の予想→操作→正常/異常比較で理解します。確認できた範囲と限界を区別してから一次資料へ戻り、次の実験へ進みます。

ここから判断できることは、現在値が必要ならlive参照、特定時点を保持したいならコピーを選ぶこと、更新をexport元の関数へ集約すること、初期化がimporterごとに走る前提を置かないこと、404と構文不良を別層で診断することです。DOM更新はこの教材の `render()` が明示的に実行し、live bindingだけで自動再描画されません。iframeは同一originの別Documentで、security sandboxの実証ではありません。

## 主要未教材領域 → 次の4実験

全て未実装の学習計画です。各行は領域の最初の実験で、分野全体の完成条件ではありません。[scope.json](scope.json) の9未教材領域と対応しています。

| 次の実験 | 未教材領域・具体的な問い | 実験と公式locator |
|---|---|---|
| E1 評価順とidentity | module-advanced / language-runtime。cycle/TDZ/TLAで初期化前の読み取りはいつ失敗する？別Document/worker/URLは同じstate？ | 2moduleのcycle・await有無で評価trace/ReferenceError、次にURL/realm違いを比較。[ECMAScript Cyclic Module Records](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html#sec-cyclic-module-records)、[HTML module map](https://html.spec.whatwg.org/multipage/webappapis.html#module-map)。GC/Wasm/言語全体は別途未教材。 |
| E2 loaderと配信境界 | network-storage / security-isolation / delivery-operations。HTTP 200でも動かない場合、MIME/CORS/CSP/cacheのどこを調べる？ | 正/誤MIME・404・policy拒否でloaderとNetworkを比較し、cache/offlineの版を確認。[HTML Fetch a single module script](https://html.spec.whatwg.org/multipage/webappapis.html#fetch-a-single-module-script)、[CSP script-src](https://www.w3.org/TR/CSP3/#directive-script-src)。新origin等は別の承認済みfixtureが必要。 |
| E3 stateとUI更新 | dom-rendering / frameworks / testing-engineering。値の更新とDOM再描画は同じ？破棄後に通知は残る？ | nativeの明示renderとframework stateを並べ、値/DOM/通知/cleanupを回帰検査。[React State: A Component's Memory](https://react.dev/learn/state-a-components-memory)。layout/paint/accessibility全体は別教材。 |
| E4 build後の意味と版 | build-tooling / delivery-operations / testing-engineering。tree-shaking/code splitting後もlive値/初期化/失敗分類は同じ？ | 同fixtureのnative/bundleを比較し、評価回数・chunk request・source map・版違いを記録。[Rollup Introduction / Tree-shaking](https://rollupjs.org/introduction/#tree-shaking)。実性能/全Browser運用は次段階。 |

これらの追試を今回行ったとは扱いません。学習導線は[index.html](index.html#learning-path)、実測は[VERIFICATION.md](VERIFICATION.md)、現在の実装は以下の起動手順で確認します。

## 起動と検査

このdirectoryで実行します。依存追加は不要です。

```sh
node verify.mjs
node audit.mjs
node serve.mjs
```

serverは127.0.0.1へport0でbindし、own動的URLを表示します。ブラウザでtitleとA/Bボタンを確認してから操作。終了はCtrl+C。他担当のlistener/processは停止しません。

`verify.mjs` はNodeのfile loaderを実行します。Node側のモジュールstateは毎processで独立で、ブラウザのcounterに影響しません。`audit.mjs` は保存Browser原票を独立期待値表、fresh domain event、source hashで照合します。いずれも通常はread-onlyで、新しい記録を明示した場合だけ保存します。

```sh
node verify.mjs --record new-node-run-01
node audit.mjs --record new-audit-run-01
```

例の名前も既に使われている場合は未使用の名前へ変えます。既存directoryは拒否し、成功/失敗原票を上書きしません。新しいBrowser実観測はブラウザで別に行う必要があり、Nodeの再実行や保存記録検査で置き換えません。

## 操作

1. Aが更新したらB/snapshotはどうなるか予想する。
2. A +1、B +1。両liveは0→1→2、snapshotは0のまま。
3. delta0、−1、同URL再import、NaN拒否を試す。counter評価はこのDocumentで1回。
4. imported count / namespace.countへ99を代入する。TypeErrorで拒否され、countは保たれる。
5. 読込/構文失敗のiframeをそれぞれ実行。404/TypeErrorと200/SyntaxErrorを分ける。HTTPは別probeの結果。
6. 原典と実装を読み、現在値を得る方法を回答する。

scopeが「1回評価」を新Documentやquery/fragment違いまで保証しているわけではありません。importのread-onlyもobject内部のdeep freezeではありません。この教材ではprimitiveなcountを使います。

## 一次資料と実装

[ECMAScript §9.1.1.5.5 CreateImportBinding](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records-createimportbinding-n-m-n2) の間接bindingと[§10.4.6.9 Module Namespace [[Set]]](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html#sec-module-namespace-exotic-objects-set-p-v-receiver)、[HTML module map](https://html.spec.whatwg.org/multipage/webappapis.html#module-map)を参照しています。コード/素材は独自実装です。

`counter.mjs`がexport元、`importer-a.mjs`と`importer-b.mjs`が2参照元、`journal.mjs`が実評価/変更のdomain event記録です。`failed-case.html`は正常counterをimportせず、別iframeでdynamic importをcatchします。`bad-syntax.mjs`は意図的にparse不能なので、正常Sourceのlint成功へ偽装せず負例として維持します。`missing-module.mjs`は存在せず、404がfixtureです。

[検証記録](VERIFICATION.md) / [未教材領域](scope.json) / [module-local Skill](skills/atlas-frontend-platform/SKILL.md)。NodeとBrowserの違い、cycle・framework・build tool等の未確認を明記しています。global Skillや公開は行いません。
