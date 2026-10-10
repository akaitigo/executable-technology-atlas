# 同じ小gridの更新順とtimerを測る

DOM layout-read/writeの交互実装とbatched実装を、同一fixtureで実行する有限1教材です。速さの一般化ではなく、値一致と測定条件を分けて学びます。LCP/INP全面証明、全Web performanceの完成、性能保証ではありません。

## 学ぶ順番と実務判断

前提はDOM style更新、geometry read、event loop。[教材](index.html#learning-path)の予想→操作→比較→手順図/実装/一次資料→答えを通します。主な仕組みはstyleの無効化とlayoutを必要とするread、read/write batching、performance.now、task占有とtimer予約です。

正常：両方式のchecksum/最終geometry一致。境界：0反復はread/write/checksumが0、初期80px幅。-1反復は実行拒否してDOMを維持。意図異常：120msの同期spinでtimer/microtaskが待つ反例。長timer予約は待機時間そのものが同期占有ではないと比較します。

[実DOM runner](experiment.mjs)は16セル、8反復、warmup2 round、本測定5 roundを固定し、interleaved/batchedの順を交互にします。resetと最終geometry採取は計時外。各sampleに実elapsed、read/write回数、checksum、computed widthと相対box geometryを残します。[独立oracle](oracle.mjs)はrunner/plan/CSSをimportせず固定期待値を持ちます。

判断できること：不要なwrite/read混在を探し、同じ出力を保って順序を変え、warmup/条件/雑音を分けること。判断できないこと：batchedは常に速い、全readでengine layout発生、timerをINPとみなすこと。この計時にはJS/geometry計算などが含まれ、純layout時間ではありません。小標本、JIT/GC、background、他process、時間精度が影響。0msや外れ値も保持し、観測上の最小正deltaは厳密な時計精度や統計誤差ではありません。

## 起動・検査・原票

このdirectoryでNode標準機能のみ使用。新規依存なし。

```sh
node serve.mjs
```

表示された一時loopback URLをBrowserで開き、予想、2方式、0/-1反復、timer probe、答えを操作。probeは約120ms同期処理を意図的に実行します。serverはCtrl+Cで終了。ホスト審査拒否を永続設定で迂回しません。

```sh
node verify.mjs
node check.mjs
node verify.mjs --record node-attempt-new
node check.mjs --record check-attempt-new
```

通常検査はread-only、明示recordのみ未使用directoryへ新規保存。既存directoryはEEXIST拒否。Nodeは純粋なworkload計画を検査し、Browser DOMやelapsed証拠ではありません。checkは保存済み実Browser原票を固定oracleへ照合しBrowserを起動しません。[検証記録](VERIFICATION.md) / [専用Skill](skills/atlas-web-performance/SKILL.md)。Browser再取得は実操作・snapshot・画像を未使用directoryへ明示保存し、Source変更をdigest更新だけで済ませません。

## 未教材coverageと次の4実験

主要8領域の入口を整理したもので、網羅台帳ではありません。次のE1–E4はすべて未実装/未実証。[画面の道筋](index.html#next-experiments)にも対応します。

| 未教材ID・概念 | 問い | 次の実験・公式locator |
|---|---|---|
| vitals-metrics：LCP/INP/CLSと測定窓 | どのmetricが利用者のどの体験を表すか | E1：実navigation/interaction/shiftを観測。[LCP API](https://www.w3.org/TR/largest-contentful-paint/)、[Event Timing](https://www.w3.org/TR/event-timing/)、[Web Vitals](https://web.dev/articles/vitals) |
| field-rum：実利用分布・session・集計 | lab結果とfield分布をどう区別するか | E1：lab/fieldを別集計。Web Vitalsを起点にprivacyと分布条件を設計（実ユーザー収集は未実施） |
| network-loading：resource waterfall・cache・優先度 | 転送と待ち時間の支配要因は何か | E2：自前assetでcache/転送を変え比較。[Resource Timing](https://www.w3.org/TR/resource-timing/) |
| assets-budgets：画像・font・JSのbudget | 同じ表示品質で何を削減できるか | E2：画像/JS/fontのサイズと表示品質を比較。[HTML responsive images](https://html.spec.whatwg.org/multipage/images.html#responsive-images) |
| rendering-animation：layout/paint/composite・containment | geometry変更とtransformでpipelineはどう違うか | E3：各更新の実engine trace採取。[CSS containment](https://www.w3.org/TR/css-contain-1/) |
| main-thread-workers：task分割・worker・通信コスト | 計算を移すと何が応答性の制約になるか | E3：同期/分割/workerと通信量を比較。[HTML workers](https://html.spec.whatwg.org/multipage/workers.html#workers) |
| memory-lifecycle：resource ownership・heap・retention | 繰返しmount/unmountで何が残るか | E4：resource破棄とheap保持を比較。[Chrome memory tools](https://developer.chrome.com/docs/devtools/memory-problems) |
| regression-delivery：統計・CI環境・性能budget・運用 | 雑音と回帰をどう区別し配信後も追うか | E4：固定環境の多標本と配信後観測。[Lighthouse](https://developer.chrome.com/docs/lighthouse/overview)（統計手法自体の規定ではない） |

## 原典と観測の区別

[CSSOM View geometry](https://www.w3.org/TR/cssom-view-1/#dom-element-getboundingclientrect)、[Chrome開発者のlayout解説](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing)、[High Resolution Time](https://www.w3.org/TR/hr-time-3/#dom-performance-now)、[HTML timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)を起点にします。仕様/解説は処理モデルの根拠、保存した原票は今回の小fixtureの観測です。今回未取得のengine tracing、paint、実input latency、Core Web Vitals、複数device/browser、CPU/network profileを実証したとは言いません。
