# Browser event loop: microtaskの追加はいつ走る？

同期log、Promise reaction、microtask内の追加microtask、timer内microtaskを、専用iframeの実callback traceで比較する一教材です。全Subjectの完成ではありません。Nodeのevent loop実行をBrowserの証拠へ代用しません。

## 学習の道筋

前提は関数・配列・Promise.then/catch・setTimeout・throw。同期実行→Promise job→Browser microtask checkpoint→timer taskという仕組みを、予想→操作→比較→原典/実装→回答で学びます。

今回の3caseはbasic（追加なし、delay 0の境界）、nested（parent→child→grandchildとpeer）、caught-error（reactionのthrow→catch）です。各実行で新Documentを作り、正常・境界・意図した異常を比較します。例外はcatchで記録し、後続timerも実行されるか確認します。無限microtaskやBrowser停止を故意に起こしません。

実務では「Promiseへ移すだけではtimer/描画へ必ずyieldしない」「catchは同期try/catchのようにその場で割り込むわけではない」「delay 0は即時/精度保証ではない」と判断できます。ただし、全task sourceに単一FIFOの順序を保証したり、paintのタイミングをこのlogだけで結論したりはしません。同一origin iframeの新Documentはthread/process/securityの隔離を保証しません。

## 起動と操作

このdirectoryで、依存追加なしに実行します。

```sh
node check.mjs --self-test
node check.mjs
node serve.mjs
```

`--self-test`は合成fixtureで独立oracleの負例を検査し、Runtimeの実証ではありません。通常 `check.mjs` は保存Browser原票と現在のsourceを照合するread-only検査です。serverは127.0.0.1:port0の動的URLを表示。自分の起動URLとtitleを確認してブラウザで開き、最後にCtrl+Cで自分のserverだけ停止します。

1. 追加microtaskが同じcheckpointで走るか予想し、保存する。
2. basic→nested→caught-errorを実行。iframeのlabel順と経過時刻を比較。
3. 誤モデルの列と最初に違う行を調べる。nestedを新Documentでもう一度実行。
4. [case.mjs](case.mjs) と [oracle.mjs](oracle.mjs)、下の原典を読む。
5. 正確な0ms/単一FIFO/追加分も処理という回答を試し、理由を比較。

記録更新が必要な場合だけ、未使用名へ明示します。

```sh
node check.mjs --record new-check-01
```

既存directoryはEEXISTで拒否し、成功/失敗原票を上書きしません。Browser原票の新規取得は別の実Browser操作が必要です。checker再実行やhash変更だけで新しい実行証拠にはしません。

## 独立oracleと原典

runnerは期待値をimportしません。oracle側で3caseの固定label順をHTML/ECMAScriptの規則から導出し、UI結果や現在のtraceから期待値を生成しません。fixtureは同じ同期呼出し内で同delayの2timerを順に登録します。timer-first内のPromise reactionがtimer-second前に来るか確認します。日時とperformance値は観測値で、一定時間内の実行を成功条件にしません。

- [HTML event loop processing model](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model)、[microtask checkpoint](https://html.spec.whatwg.org/multipage/webappapis.html#perform-a-microtask-checkpoint)。追加されたqueueの処理を調べる。
- [HTML timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)。delayと実行時刻を同一視しない。
- [ECMAScript PerformPromiseThen](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-performpromisethen)、[NewPromiseReactionJob](https://tc39.es/ecma262/multipage/control-abstraction-objects.html#sec-newpromisereactionjob)。then/catchとthrowによるrejectionを調べる。

一次資料は2026-10-05に確認。独自コード/素材で、第三者サイトの表示・コードはコピーしていません。原典は生きた仕様へのlocatorで、全本文を固定/網羅レビューしたものではありません。

## 未教材coverage → 次の4実験

[scope.json](scope.json) は非網羅の主要領域の未教材リスト。以下は全て未実装の計画で、成功Evidenceではありません。[index](index.html#learning-path)にも同じ学習導線があります。

| 計画 | 未教材領域・概念と問い | 次の実験・公式locator |
|---|---|---|
| E1 DOM構築とscript | parsing-dom。tokenizer/tree builderとasync/defer/moduleはどう交わる？ | 小HTMLのDOM markerとscript時刻/parse errorを比較。[HTML parsing](https://html.spec.whatwg.org/multipage/parsing.html#parsing)。全parser実装は別途。 |
| E2 schedulerと表示 | rendering-input / scheduling-advanced / tooling-compatibility。microtask後は必ずpaint？input、visibility、engine/versionで何が違う？ | 有限microtask/timer/rAFとinput/paintの観測、DevTools trace/版差を比較。[HTML rendering](https://html.spec.whatwg.org/multipage/webappapis.html#update-the-rendering)、[timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)。starvation/全互換性は未実証。 |
| E3 agentとprocess | workers-memory / engine-architecture / security-isolation。iframeとworkerは同じthread/process？message/transfer/shared stateの違いは？ | worker有限計算とmessage/transferを比較し、processは別観測で確かめる。[HTML workers](https://html.spec.whatwg.org/multipage/workers.html#workers)、[Chromium architecture](https://www.chromium.org/developers/design-documents/multi-process-architecture/)。sandbox、shared memory、GC/JIT/Wasmは別途。 |
| E4 requestと保存 | networking-storage。fetch/cache/SWのresponseと実行/更新の境界は？ | 承認済み別fixtureでlocal response/offline/版更新を比較。[Service Worker lifetime](https://w3c.github.io/ServiceWorker/#service-worker-lifetime)。本教材ではSWを登録せずstorage/quotaも未実証。 |

全Browserやworker/runtime、engine internals、描画/Network全trace、wall-clock精度、無限queue/負荷、権限・セキュリティ全般は未確認です。[検証記録](VERIFICATION.md)と[教材専用Skill](skills/atlas-browser-engine-web-runtime/SKILL.md)で、実測と対象外を分けます。global install、Docker、依存・OS/GitHub設定、公開は行いません。
