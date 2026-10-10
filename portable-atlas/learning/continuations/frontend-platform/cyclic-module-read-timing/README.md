# 循環moduleは、いつbindingを読むか

[原典のlive binding教材](../../../subjects/frontend-platform/README.md) → [今回の実Node比較](index.html) → [static name resolution](../../programming-languages-compilers-runtimes/static-name-resolution/README.md)。元README E1のcycle/TDZだけを進める有限追加です。

A↔Bのimport graphは同じ。B評価中にAの未初期化`value`を即時readすると実ReferenceError。Bは関数を定義するだけにしてentryから初期化後に呼ぶと1を読めます。関数に包んでもB評価中に呼べば失敗します。循環の存在だけでは成否を決められません。

```sh
node checker.mjs
node runner.mjs
node route.mjs
```

既存Node v25.2.1、built-inだけ。producerはケースごとに新processを起動し、Node native ES modulesを実行する。sourceを独自linkerで模擬しない。通常checker/runnerはread-onlyで全file hash/mtime不変。明示 `node runner.mjs --record` だけfresh UTC directoryにchild stdout/stderr/exit、pid、環境、source snapshot、digest、rawを作りUI pointerを更新する。旧runは保持する。

UIは保存実Node原票のreader。比較ボタンではNodeを再起動しない。editable欄は「予想の数値」でありsource・実行入力ではない。空欄/1桁0..9を受け付け、abc/10/−1等はUIの予想入力拒否（Node例外とは別）。予想または数値だけの変更で旧比較・答え本文・traceを空にし、detailsを閉じ、新値を残す。case変更は両予想欄をresetする。

## 固定graphとconsole観測

[固定表](expected-table.json)のgraph、event列、例外class、final値を最初のengine実行前にliteralで置いた。[contracts](contracts.json)は5fixtureの入口。`driver.mjs`がdynamic importを開始し、完了/例外をcatchする。top-level awaitは使用しない。ReferenceErrorを捕捉したchildはstderrに実name/messageを出しexit1。batch producerのexit0は全case成功という意味ではない。

| ケース | graph | 観測結果 |
|---|---|---|
| immediate | entry→A↔B | B:before-read後ReferenceError。A/entry本文のlogなし、finalなし |
| delayed | entry→A↔B | B:ready→A:init1→entry→B:read1、exit0/final1 |
| early-call | entry→A↔B | Bで定義したreadをB評価中に呼びReferenceError |
| acyclic | entry→B→A | A:init1→B:read1、循環なし即時read成功 |
| live-update | entry→A↔B | read1→A:update2→read2。数値snapshotは1を保持 |

event列は明示`console.log`箇所の実観測。link、binding作成、内部stack/status/DFS index等はengineから採取していない。「A:init」は宣言直後の利用者logでありengine内部InitializeBinding traceではない。stderrもstackは出さずname/messageのみ採取し、host絶対pathは記録しない。

[ECMAScript Cyclic Module Records](https://tc39.es/ecma262/multipage/ecmascript-language-scripts-and-modules.html#sec-cyclic-module-records)は依存graphのlink/evaluateを定義する。[Module Environment GetBindingValue](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records-getbindingvalue-n-s)はimportの間接参照先を読み、未初期化bindingはReferenceErrorとなる。[Declarative GetBindingValue](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-declarative-environment-records-getbindingvalue-n-s)も参照する。これらの仕様説明と今回のconsole観測を区別する。

[producer](experiment.mjs) / [driver](driver.mjs) / [独立oracle](checker.mjs) / [一次資料](sources.json) / [残coverage](coverage.json) / [routing](route.mjs) / [Skill](skills/atlas-cyclic-module-read-timing/SKILL.md) / [実IAB QA](qa/README.md)。独立oracleはproducerをimportせず同じlinkerを実装しない。literal event/final/class/exitとsourceの固定import辺を照合する。

未実証: TLA、bundler、browser realm/worker、URL cache、CORS/MIME/CSP、全ECMAScript仕様。原典のBrowser実行を今回Nodeで代替して証明しない。Subject/Atlas全体未完了、Core/fullGateは中央の範囲。unit-only previewでは親/関連単元リンクは配信外（filesystem存在だけ確認する）。
